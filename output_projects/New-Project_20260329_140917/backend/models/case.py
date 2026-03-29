from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models import Base
import enum


class CaseStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    product_id = Column(String(64), nullable=True, index=True)
    summary = Column(Text, nullable=False)
    suggested_close_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.pending, nullable=False, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    assignee = relationship("User", back_populates="assigned_cases")
    attachments = relationship("Attachment", back_populates="case", cascade="all, delete-orphan")