from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class User(BaseModel):
    """
    使用者資料模型，對應資料庫 users 表。
    所有欄位均為必要，除非標註 Optional。
    """
    id: str = Field(..., description="全域唯一識別碼，使用 Azure AD 的 oid")
    name: str = Field(..., description="顯示名稱，來自 Azure AD 的 displayName")
    email: EmailStr = Field(..., description="公司信箱，來自 Azure AD 的 mail")
    role: str = Field(..., description="角色代碼，目前僅支援 'agent' 或 'manager'")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "王小明",
                "email": "ming.wang@example.com",
                "role": "agent"
            }
        }