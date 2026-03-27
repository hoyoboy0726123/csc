from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional
from database.connection import get_db
from models.user import User
from services.crypto import decrypt, encrypt
from utils.config import settings
from utils.exceptions import InvalidCredentialsError, UserNotFoundError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24 * 7  # 7 days


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    has_gemini_key: bool
    has_groq_key: bool


class UpdateKeysRequest(BaseModel):
    gemini_key: Optional[str] = None
    groq_key: Optional[str] = None


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=JWT_EXPIRATION_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise InvalidCredentialsError
    except jwt.PyJWTError:
        raise InvalidCredentialsError

    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise UserNotFoundError
    return user


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    db = next(get_db())
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(email=req.email)
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.email})
    return LoginResponse(access_token=access_token, expires_in=JWT_EXPIRATION_MINUTES * 60)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        has_gemini_key=bool(current_user.gemini_key_enc),
        has_groq_key=bool(current_user.groq_key_enc),
    )


@router.put("/keys")
def update_keys(req: UpdateKeysRequest, current_user: User = Depends(get_current_user)):
    db = next(get_db())
    user = db.query(User).filter(User.id == current_user.id).first()

    if req.gemini_key is not None:
        if req.gemini_key.strip() == "":
            user.gemini_key_enc = None
        else:
            user.gemini_key_enc = encrypt(req.gemini_key)

    if req.groq_key is not None:
        if req.groq_key.strip() == "":
            user.groq_key_enc = None
        else:
            user.groq_key_enc = encrypt(req.groq_key)

    db.commit()
    return {"status": "updated"}


@router.get("/keys")
def get_keys(current_user: User = Depends(get_current_user)):
    keys = {}
    if current_user.gemini_key_enc:
        keys["gemini_key"] = decrypt(current_user.gemini_key_enc)
    if current_user.groq_key_enc:
        keys["groq_key"] = decrypt(current_user.groq_key_enc)
    return keys