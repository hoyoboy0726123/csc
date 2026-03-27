from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
import os
import aiofiles
from typing import Dict, Any

from database.connection import get_db
from models.user import User
from services.stt import transcribe_audio
from services.llm_orchestrator import LLMOrchestrator
from utils.config import UPLOAD_DIR, MAX_AUDIO_SIZE_MB
from utils.exceptions import AudioTooLargeError, TranscriptionError
from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["upload"])

def get_file_size_mb(file: UploadFile) -> float:
    return len(file.file.read()) / (1024 * 1024)

@router.post("/upload-audio")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are accepted.")

    file_size_mb = get_file_size_mb(file)
    if file_size_mb > MAX_AUDIO_SIZE_MB:
        raise AudioTooLargeError(f"Audio file too large: {file_size_mb:.2f} MB > {MAX_AUDIO_SIZE_MB} MB")

    task_id = str(uuid.uuid4())
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await file.read())

    background_tasks.add_task(process_audio_transcription, task_id, file_path, current_user.id, db)

    return JSONResponse(status_code=201, content={"task_id": task_id, "status": "processing"})

async def process_audio_transcription(
    task_id: str,
    file_path: str,
    user_id: int,
    db: Session
):
    try:
        transcription = await transcribe_audio(file_path)
        orchestrator = LLMOrchestrator(db=db, user_id=user_id)
        prd_md = await orchestrator.generate_prd_from_transcription(transcription)
        orchestrator.save_prd_to_db(task_id, prd_md)
    except TranscriptionError as e:
        orchestrator.update_task_status(task_id, "failed", str(e))
    except Exception as e:
        orchestrator.update_task_status(task_id, "failed", "Internal processing error")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload-text")
async def upload_text(
    background_tasks: BackgroundTasks,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    text_input = data.get("text", "").strip()
    if not text_input:
        raise HTTPException(status_code=400, detail="Text input cannot be empty")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_text_to_prd, task_id, text_input, current_user.id, db)

    return JSONResponse(status_code=201, content={"task_id": task_id, "status": "processing"})

async def process_text_to_prd(
    task_id: str,
    text_input: str,
    user_id: int,
    db: Session
):
    try:
        orchestrator = LLMOrchestrator(db=db, user_id=user_id)
        prd_md = await orchestrator.generate_prd_from_text(text_input)
        orchestrator.save_prd_to_db(task_id, prd_md)
    except Exception as e:
        orchestrator.update_task_status(task_id, "failed", str(e))