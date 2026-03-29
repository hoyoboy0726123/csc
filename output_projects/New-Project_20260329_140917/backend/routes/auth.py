from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from config import Settings
from utils.security import create_access_token, verify_token
from middleware.auth import get_current_user
from models.user import User
from sqlalchemy.orm import Session
from models import Base, User
from utils.logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])
settings = Settings()

AZURE_AD_AUTH_URL = f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}/oauth2/v2.0/authorize"
AZURE_AD_TOKEN_URL = f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}/oauth2/v2.0/token"
AZURE_AD_REDIRECT_URI = f"{settings.BACKEND_URL}/auth/callback"

@router.get("/login")
def login_redirect(request: Request):
    state = str(uuid.uuid4())
    params = {
        "client_id": settings.AZURE_AD_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": AZURE_AD_REDIRECT_URI,
        "scope": "openid profile email User.Read",
        "state": state,
        "response_mode": "query",
    }
    auth_url = f"{AZURE_AD_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Redirecting to Azure AD login with state {state}")
    return RedirectResponse(url=auth_url)

@router.get("/callback")
def callback(code: str, state: str, request: Request, response: Response, db: Session = Depends(get_db)):
    if not code:
        logger.error("Missing authorization code")
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_payload = {
        "client_id": settings.AZURE_AD_CLIENT_ID,
        "scope": "openid profile email User.Read",
        "code": code,
        "redirect_uri": AZURE_AD_REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": settings.AZURE_AD_CLIENT_SECRET,
    }

    import httpx
    r = httpx.post(AZURE_AD_TOKEN_URL, data=token_payload)
    if r.status_code != 200:
        logger.error("Failed to fetch Azure AD token")
        raise HTTPException(status_code=400, detail="Invalid token response")

    token_json = r.json()
    id_token = token_json.get("id_token")
    access_token = token_json.get("access_token")

    try:
        id_claims = jwt.decode(id_token, options={"verify_signature": False})
    except Exception as e:
        logger.error(f"Invalid id_token: {e}")
        raise HTTPException(status_code=400, detail="Invalid id_token")

    oid = id_claims.get("oid")
    email = id_claims.get("email")
    name = id_claims.get("name") or email

    if not oid or not email:
        logger.error("Missing oid or email in id_token")
        raise HTTPException(status_code=400, detail="Missing user info")

    user = db.query(User).filter(User.azure_ad_oid == oid).first()
    if not user:
        user = User(
            email=email,
            name=name,
            role="agent",
            azure_ad_oid=oid,
            disabled=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user {email}")
    else:
        if user.disabled:
            logger.warning(f"Disabled user {email} attempted login")
            raise HTTPException(status_code=403, detail="Account disabled")
        user.name = name
        db.commit()

    jwt_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    response.set_cookie(
        key="Authorization",
        value=f"Bearer {jwt_token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    logger.info(f"User {email} logged in")
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard")

@router.post("/refresh")
def refresh(current_user: User = Depends(get_current_user)):
    new_token = create_access_token(data={"sub": str(current_user.id), "role": current_user.role})
    logger.debug(f"Token refreshed for user {current_user.email}")
    return {"access_token": new_token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("Authorization")
    logger.info("User logged out")
    return {"detail": "Logged out"}

def get_db():
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()