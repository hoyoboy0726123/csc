from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from models import Case, User
from services.notification_service import NotificationService
from middleware.auth import get_current_user
from utils.logger import logger
from database import get_db

router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignRequest(BaseModel):
    case_id: int
    assignee_id: int = Field(..., description="Target user id to assign the case to")


class BulkAssignRequest(BaseModel):
    case_ids: List[int] = Field(..., min_items=1, max_items=100)
    assignee_id: int = Field(..., description="Target user id to assign all cases to")


class AssignResponse(BaseModel):
    success: bool
    message: str


@router.post("/assign", response_model=AssignResponse)
def assign(
    payload: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    notification: NotificationService = Depends(),
):
    """
    Assign a single case to a user and send notification email.
    """
    case = db.query(Case).filter(Case.id == payload.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    assignee = db.query(User).filter(User.id == payload.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee user not found")

    # Authorization: only managers or the current assignee can re-assign
    if current_user.role not in {"manager", "admin"} and case.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to assign this case")

    previous_assignee_id = case.assignee_id
    case.assignee_id = assignee.id
    db.commit()
    db.refresh(case)

    # Notify the new assignee
    try:
        notification.notify_assignment(case=case, assignee=assignee, actor=current_user)
    except Exception as exc:
        logger.warning("Failed to send assignment email", exc_info=exc)

    logger.info(
        "Case assigned",
        extra={
            "case_id": case.id,
            "previous_assignee_id": previous_assignee_id,
            "new_assignee_id": assignee.id,
            "actor_id": current_user.id,
        },
    )

    return AssignResponse(success=True, message="Case assigned successfully")


@router.post("/bulk-assign", response_model=AssignResponse)
def bulk_assign(
    payload: BulkAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    notification: NotificationService = Depends(),
):
    """
    Bulk assign up to 100 cases to a single user.
    """
    if current_user.role not in {"manager", "admin"}:
        raise HTTPException(status_code=403, detail="Only managers can bulk assign")

    cases = db.query(Case).filter(Case.id.in_(payload.case_ids)).all()
    if len(cases) != len(payload.case_ids):
        raise HTTPException(status_code=404, detail="Some cases not found")

    assignee = db.query(User).filter(User.id == payload.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee user not found")

    for case in cases:
        case.assignee_id = assignee.id
    db.commit()

    # Send a single summary email instead of spamming
    try:
        notification.notify_bulk_assignment(cases=cases, assignee=assignee, actor=current_user)
    except Exception as exc:
        logger.warning("Failed to send bulk assignment email", exc_info=exc)

    logger.info(
        "Bulk assignment completed",
        extra={
            "case_ids": payload.case_ids,
            "assignee_id": assignee.id,
            "actor_id": current_user.id,
        },
    )

    return AssignResponse(success=True, message=f"{len(cases)} cases assigned to {assignee.name}")