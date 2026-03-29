from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import asyncio
from datetime import datetime

from middleware.auth import get_current_user
from models import User
from services import PdfService
from utils.azure_blob import upload_file
from utils.logger import logger
from config import Settings

router = APIRouter(prefix="/api/upload", tags=["upload"])

settings = Settings()


class UploadResponse(BaseModel):
    success: bool
    message: str
    case_id: Optional[str] = None
    fields: Optional[dict] = None


@router.post("/pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    pdf_service: PdfService = Depends(PdfService),
):
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案")

    if file.size > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=400, detail="檔案大小超過 10 MB 限制")

    try:
        unique_name = f"{uuid.uuid4().hex}.pdf"
        local_path = f"/tmp/{unique_name}"
        with open(local_path, "wb") as f:
            f.write(await file.read())

        blob_url = await upload_file(
            container="pdf",
            blob_name=unique_name,
            file_path=local_path,
            overwrite=True,
        )

        fields = await pdf_service.parse(local_path)

        os.remove(local_path)

        case_id = str(uuid.uuid4())
        logger.info(
            "PDF uploaded and parsed",
            extra={
                "user": current_user.email,
                "blob_url": blob_url,
                "case_id": case_id,
            },
        )

        return UploadResponse(
            success=True,
            message="解析成功",
            case_id=case_id,
            fields=fields,
        )

    except Exception as e:
        logger.error("PDF upload failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="上傳或解析失敗")