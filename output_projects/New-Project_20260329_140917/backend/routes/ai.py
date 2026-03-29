from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
from middleware.auth import get_current_user
from services.llm_service import LLMService
from utils.logger import logger

router = APIRouter(prefix="/ai", tags=["ai"])


class SmartFillRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=50_000)


class SmartFillResponse(BaseModel):
    customer_name: str
    product_id: str
    summary: str
    suggested_close_date: str


class GenerateReplyRequest(BaseModel):
    case_id: int
    tone: str = Field("professional", regex="^(professional|friendly|apology)$")


class GenerateReplyResponse(BaseModel):
    reply_html: str
    reply_text: str


@router.post("/smart-fill", response_model=SmartFillResponse)
async def smart_fill(
    payload: SmartFillRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    智慧填單：根據原始內容提取關鍵欄位
    """
    try:
        llm = LLMService()
        fields = await llm.extract_fields(payload.content)
        return SmartFillResponse(**fields)
    except Exception as e:
        logger.error(f"smart_fill error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 提取失敗，請稍後再試",
        )


@router.post("/generate-reply", response_model=GenerateReplyResponse)
async def generate_reply(
    payload: GenerateReplyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    生成回覆草稿：依案件歷史與知識庫產生專業回覆
    """
    try:
        llm = LLMService()
        reply = await llm.generate_reply(
            case_id=payload.case_id,
            tone=payload.tone,
            user_id=current_user["oid"],
        )
        return GenerateReplyResponse(**reply)
    except Exception as e:
        logger.error(f"generate_reply error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 回覆生成失敗，請稍後再試",
        )