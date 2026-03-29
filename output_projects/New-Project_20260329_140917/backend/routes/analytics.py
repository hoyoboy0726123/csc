from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional, List

from backend.models import Case, User
from backend.services.kanban_service import KanbanService
from backend.middleware.auth import get_current_user
from backend.utils.logger import logger
from backend.main import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/metrics")
def get_metrics(
    start: Optional[date] = Query(None, description="YYYY-MM-DD, default 30 days ago"),
    end: Optional[date] = Query(None, description="YYYY-MM-DD, default today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    儀表板指標：
    - 待處理量
    - 平均處理天數
    - 逾期率
    - 個人負荷（若角色為主管則回傳全隊）
    """
    if not start:
        start = date.today() - timedelta(days=30)
    if not end:
        end = date.today()
    logger.info(f"[metrics] user={current_user.email} range={start}~{end}")

    svc = KanbanService(db)
    return svc.get_metrics(start, end, current_user)


@router.get("/chart")
def get_chart_data(
    chart: str = Query(..., regex="^(bar|line|pie)$"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    回傳圖表資料：
    - bar: 個人負荷（案件數）
    - line: 每日趨勢（30 天滑動）
    - pie: 案件狀態分佈
    """
    if not start:
        start = date.today() - timedelta(days=30)
    if not end:
        end = date.today()
    logger.info(f"[chart] type={chart} user={current_user.email}")

    svc = KanbanService(db)
    return svc.get_chart_data(chart, start, end, current_user)