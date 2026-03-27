from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import asyncio
from datetime import datetime

from backend.models.prd import PRDHistory
from backend.models.user import User
from backend.services.llm_orchestrator import LLMOrchestrator
from backend.services.stt import STTService
from backend.database.connection import get_db
from backend.utils.exceptions import AudioTooLargeError, STTError, LLMError
from backend.utils.config import MAX_AUDIO_SIZE_MB
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["prd"])


class AudioUploadResponse(BaseModel):
    task_id: str
    status: str


class PRDResponse(BaseModel):
    task_id: str
    status: str
    prd_md: Optional[str] = None
    editable: bool = True


class PRDUpdateRequest(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=2000)


class PRDListResponse(BaseModel):
    id: int
    title: str
    frozen: bool
    created_at: datetime


@router.post("/upload-audio", response_model=AudioUploadResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    if file.size > MAX_AUDIO_SIZE_MB * 1024 * 1024:
        raise AudioTooLargeError(f"Audio file too large. Max {MAX_AUDIO_SIZE_MB}MB allowed.")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_audio, task_id, file, current_user.id, db)
    return AudioUploadResponse(task_id=task_id, status="processing")


async def process_audio(task_id: str, file: UploadFile, user_id: int, db):
    try:
        stt_service = STTService()
        text = await stt_service.transcribe(file)
    except Exception as e:
        raise STTError("Failed to transcribe audio") from e

    try:
        orchestrator = LLMOrchestrator()
        prd_md = await orchestrator.generate_prd(text)
    except Exception as e:
        raise LLMError("Failed to generate PRD") from e

    prd_record = PRDHistory(
        user_id=user_id,
        title=extract_title_from_prd(prd_md),
        prd_md=prd_md,
        frozen=False,
    )
    db.add(prd_record)
    db.commit()


def extract_title_from_prd(prd_md: str) -> str:
    first_line = prd_md.splitlines()[0]
    if first_line.startswith("# "):
        return first_line[2:].strip()
    return "Untitled PRD"


@router.get("/prd/{task_id}", response_model=PRDResponse)
async def get_prd(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    prd_record = (
        db.query(PRDHistory)
        .filter(PRDHistory.user_id == current_user.id)
        .order_by(PRDHistory.created_at.desc())
        .first()
    )
    if not prd_record:
        raise HTTPException(status_code=404, detail="PRD not found")

    return PRDResponse(
        task_id=task_id,
        status="completed",
        prd_md=prd_record.prd_md,
        editable=not prd_record.frozen,
    )


@router.patch("/prd/{task_id}", response_model=PRDResponse)
async def update_prd(
    task_id: str,
    payload: PRDUpdateRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    prd_record = (
        db.query(PRDHistory)
        .filter(PRDHistory.user_id == current_user.id)
        .order_by(PRDHistory.created_at.desc())
        .first()
    )
    if not prd_record:
        raise HTTPException(status_code=404, detail="PRD not found")
    if prd_record.frozen:
        raise HTTPException(status_code=400, detail="PRD is frozen and cannot be edited")

    try:
        orchestrator = LLMOrchestrator()
        updated_prd = await orchestrator.refine_prd(prd_record.prd_md, payload.instruction)
    except Exception as e:
        raise LLMError("Failed to refine PRD") from e

    prd_record.prd_md = updated_prd
    prd_record.title = extract_title_from_prd(updated_prd)
    db.commit()

    return PRDResponse(
        task_id=task_id,
        status="completed",
        prd_md=updated_prd,
        editable=True,
    )


@router.post("/prd/{task_id}/freeze", status_code=status.HTTP_204_NO_CONTENT)
async def freeze_prd(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    prd_record = (
        db.query(PRDHistory)
        .filter(PRDHistory.user_id == current_user.id)
        .order_by(PRDHistory.created_at.desc())
        .first()
    )
    if not prd_record:
        raise HTTPException(status_code=404, detail="PRD not found")
    prd_record.frozen = True
    db.commit()


@router.get("/prd", response_model=List[PRDListResponse])
async def list_prds(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    records = (
        db.query(PRDHistory)
        .filter(PRDHistory.user_id == current_user.id)
        .order_by(PRDHistory.created_at.desc())
        .all()
    )
    return [
        PRDListResponse(
            id=r.id,
            title=r.title,
            frozen=r.frozen,
            created_at=r.created_at,
        )
        for r in records
    ]