from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.models import Case
from backend.services.export_service import ExportService
from backend.middleware.auth import get_current_user
from backend.models.user import User
from backend.utils.logger import logger

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/excel")
def export_excel(
    case_ids: list[int] | None = None,
    current_user: User = Depends(get_current_user),
    service: ExportService = Depends(ExportService),
):
    """
    依 case_ids 匯出 Excel；若未提供則匯出可見範圍內全部案件。
    回傳 Blob SAS URL，有效期限 1 小時。
    """
    try:
        url = service.export(case_ids=case_ids, current_user=current_user)
        logger.info(f"user={current_user.email} exported {len(case_ids or [])} cases")
        return {"download_url": url}
    except Exception as e:
        logger.error(f"export excel failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法產生匯出檔案",
        )