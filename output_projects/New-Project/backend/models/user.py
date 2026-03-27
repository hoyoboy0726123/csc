from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    gemini_key_enc = Column(Text, nullable=True)
    groq_key_enc = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prd_histories = relationship("PRDHistory", back_populates="owner")
    code_versions = relationship("CodeVersion", back_populates="creator")


class PRDHistory(Base):
    __tablename__ = "prd_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    prd_md = Column(Text, nullable=False)
    frozen = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="prd_histories")
    code_versions = relationship("CodeVersion", back_populates="prd")


class CodeVersion(Base):
    __tablename__ = "code_version"

    id = Column(Integer, primary_key=True, index=True)
    prd_id = Column(Integer, ForeignKey("prd_history.id"), nullable=False)
    stack = Column(String, nullable=False)  # python | react | nodejs
    zip_path = Column(String, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prd = relationship("PRDHistory", back_populates="code_versions")
    creator = relationship("User", back_populates="code_versions")