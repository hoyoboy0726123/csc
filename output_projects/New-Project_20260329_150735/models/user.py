from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    email: str
    password: str
    role: str  # 'customer_service', 'team_leader', 'it_operator'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True
```

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User

engine = create_engine('postgresql://user:password@localhost/dbname')
Session = sessionmaker(bind=engine)

def get_user_by_id(user_id: int):
    session = Session()
    user = session.query(User).get(user_id)
    session.close()
    return user

def create_user(username: str, email: str, password: str, role: str):
    session = Session()
    user = User(username=username, email=email, password=password, role=role)
    session.add(user)
    session.commit()
    session.close()
    return user