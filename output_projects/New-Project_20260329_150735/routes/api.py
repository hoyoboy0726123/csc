from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

# Define the database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"

# Create the database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create the session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the base model
Base = declarative_base()

# Define the user model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# Define the work order model
class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    status = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

# Define the token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define the user model for authentication
class UserAuth(BaseModel):
    username: str
    password: str

# Define the work order model for creation
class WorkOrderCreate(BaseModel):
    title: str
    description: str
    status: str

# Define the work order model for update
class WorkOrderUpdate(BaseModel):
    title: str
    description: str
    status: str

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define the dependency for authentication
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

# Define the dependency for the work order service
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define the work order service
class WorkOrderService:
    def __init__(self, db: SessionLocal):
        self.db = db

    def get_work_orders(self):
        return self.db.query(WorkOrder).all()

    def create_work_order(self, work_order: WorkOrderCreate):
        db_work_order = WorkOrder(title=work_order.title, description=work_order.description, status=work_order.status)
        self.db.add(db_work_order)
        self.db.commit()
        self.db.refresh(db_work_order)
        return db_work_order

    def update_work_order(self, work_order_id: int, work_order: WorkOrderUpdate):
        db_work_order = self.db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if db_work_order is None:
            raise HTTPException(status_code=404, detail="Work order not found")
        db_work_order.title = work_order.title
        db_work_order.description = work_order.description
        db_work_order.status = work_order.status
        self.db.commit()
        self.db.refresh(db_work_order)
        return db_work_order

# Define the API router
app = FastAPI()

# Define the token endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(user_auth: UserAuth):
    user = UserAuth(username=user_auth.username, password=user_auth.password)
    return {"access_token": "token", "token_type": "bearer"}

# Define the work order endpoint
@app.get("/work_orders", response_model=List[WorkOrder])
async def read_work_orders(db: SessionLocal = Depends(get_db)):
    return WorkOrderService(db).get_work_orders()

# Define the work order creation endpoint
@app.post("/work_orders", response_model=WorkOrder)
async def create_work_order(work_order: WorkOrderCreate, db: SessionLocal = Depends(get_db)):
    return WorkOrderService(db).create_work_order(work_order)

# Define the work order update endpoint
@app.put("/work_orders/{work_order_id}", response_model=WorkOrder)
async def update_work_order(work_order_id: int, work_order: WorkOrderUpdate, db: SessionLocal = Depends(get_db)):
    return WorkOrderService(db).update_work_order(work_order_id, work_order)