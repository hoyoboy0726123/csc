from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.middleware.auth import get_current_user
from backend.models import Case, User
from backend.schemas.case import (
    CaseCreate,
    CaseOut,
    CaseStatus,
    CaseUpdate,
)
from backend.services.kanban_service import KanbanService
from backend.utils.logger import logger
from backend.utils.validators import normalize_product_id

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=List[CaseOut])
async def list_cases(
    status_filter: Optional[CaseStatus] = Query(None, alias="status"),
    assignee_id: Optional[UUID] = Query(None),
    mine: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_current_user.db),
    current_user: User = Depends(get_current_user),
) -> List[CaseOut]:
    """
    列出案件，支援篩選與分頁。
    mine=True 時僅查詢指派給自己的案件。
    """
    stmt = select(Case)
    if mine:
        stmt = stmt.where(Case.assignee_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Case.status == status_filter)
    if assignee_id:
        stmt = stmt.where(Case.assignee_id == assignee_id)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar()
    stmt = stmt.order_by(Case.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    logger.info(
        "list_cases",
        extra={
            "user": current_user.email,
            "status": status_filter,
            "assignee": str(assignee_id) if assignee_id else None,
            "mine": mine,
            "total": total,
        },
    )
    return [CaseOut.from_orm(r) for r in rows]


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_current_user.db),
    current_user: User = Depends(get_current_user),
) -> CaseOut:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found"
        )
    logger.info("get_case", extra={"user": current_user.email, "case": str(case_id)})
    return CaseOut.from_orm(case)


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_current_user.db),
    current_user: User = Depends(get_current_user),
) -> CaseOut:
    payload.product_id = normalize_product_id(payload.product_id)
    new_case = Case(**payload.dict(), assignee_id=current_user.id)
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    logger.info("create_case", extra={"user": current_user.email, "case": str(new_case.id)})
    return CaseOut.from_orm(new_case)


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: UUID,
    payload: CaseUpdate,
    db: AsyncSession = Depends(get_current_user.db),
    current_user: User = Depends(get_current_user),
) -> CaseOut:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found"
        )
    if payload.product_id is not None:
        payload.product_id = normalize_product_id(payload.product_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(case, k, v)
    await db.commit()
    await db.refresh(case)
    logger.info("update_case", extra={"user": current_user.email, "case": str(case_id)})
    return CaseOut.from_orm(case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_current_user.db),
    current_user: User = Depends(get_current_user),
) -> None:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found"
        )
    await db.delete(case)
    await db.commit()
    logger.info("delete_case", extra={"user": current_user.email, "case": str(case_id)})
    return


@router.patch("/{case_id}/status", response_model=CaseOut)
async def move_case_status(
    case_id: UUID,
    status: CaseStatus,
    db: AsyncSession = Depends(get_current_user.db),
    current_user: User = Depends(get_current_user),
    kanban: KanbanService = Depends(KanbanService),
) -> CaseOut:
    """
    供看板拖曳後呼叫，統一由 KanbanService 處理商業邏輯與通知。
    """
    case = await kanban.move_card(
        db=db, case_id=case_id, new_status=status, actor=current_user
    )
    return CaseOut.from_orm(case)