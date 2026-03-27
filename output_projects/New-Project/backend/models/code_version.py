from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base


class CodeVersion(Base):
    __tablename__ = "code_version"

    id = Column(Integer, primary_key=True, index=True)
    prd_id = Column(Integer, ForeignKey("prd_history.id"), nullable=False)
    stack = Column(String, nullable=False)  # python | react | nodejs
    zip_path = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prd = relationship("PRDHistory", back_populates="code_versions")