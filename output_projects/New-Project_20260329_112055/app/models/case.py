from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class Case(BaseModel):
    """
    案件資料模型，對應資料庫 cases 資料表。
    """
    id: Optional[int] = Field(None, description="主鍵，自動遞增")
    customer_name: str = Field(..., description="客戶名稱，必填")
    product_id: Optional[str] = Field(None, description="產品編號，選填")
    summary: str = Field(..., max_length=200, description="摘要，必填，≤200 字")
    due_date: datetime = Field(..., description="建議結案日期，必填")
    status: str = Field("待處理", description="狀態，預設「待處理」")
    assignee_id: Optional[int] = Field(None, description="負責人 user.id，選填")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="建立時間")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新時間")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        allowed = {"待處理", "處理中", "已解決"}
        if v not in allowed:
            raise ValueError(f"status 必須為 {allowed} 其中之一")
        return v

    @validator("due_date", pre=True)
    def parse_due_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d")
        return v

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(timespec="seconds")
        }