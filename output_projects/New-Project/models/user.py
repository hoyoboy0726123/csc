from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        orm_mode = True