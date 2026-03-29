from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from backend.models import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    blob_url = Column(String(2048), nullable=False)
    content_type = Column(String(128), nullable=False)
    size = Column(Integer, nullable=False)
    ocr_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("Case", back_populates="attachments")

    def get_signed_url(self, expiry_minutes: int = 60) -> str:
        """
        Generate a short-lived SAS URL for direct client download.
        In production, delegate to Azure Blob SDK with stored access policy.
        """
        from backend.config import get_settings
        settings = get_settings()
        # Example stub: real implementation uses azure-storage-blob
        sas_token = f"sp=r&st=2024-01-01&se=2024-01-01T{expiry_minutes}M&spr=https&sv=2020-08-04&sr=b&sig=dummy"
        return f"{self.blob_url}?{sas_token}"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "case_id": str(self.case_id),
            "filename": self.filename,
            "blob_url": self.blob_url,
            "content_type": self.content_type,
            "size": self.size,
            "ocr_text": self.ocr_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }