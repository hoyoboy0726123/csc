import os
import io
import uuid
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import aiofiles
import aiofiles.os
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import whisper
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("whisper-service")

# Global model cache
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading Whisper model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("large-v3", device=device)
    logger.info("Whisper model loaded on %s", device)
    yield
    logger.info("Shutting down Whisper service")


app = FastAPI(
    title="Whisper STT Service",
    description="Lightweight microservice for OpenAI Whisper inference",
    version="1.0.0",
    lifespan=lifespan,
)


class TranscriptionResponse(BaseModel):
    task_id: str
    text: str
    language: Optional[str] = Field(None, description="Detected language code")


class ErrorResponse(BaseModel):
    detail: str


@app.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def transcribe(
    file: UploadFile = File(..., description="Audio file ≤50 MB"),
    task_id: Optional[str] = Form(None, description="Optional UUID to track task"),
):
    """
    Synchronous transcription endpoint.
    Accepts an audio file (MP3/WAV/OGG/FLAC) and returns the transcribed text.
    """
    if not task_id:
        task_id = str(uuid.uuid4())

    # Validate content type
    if file.content_type not in {
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/ogg",
        "audio/flac",
        "audio/mp3",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio format",
        )

    # Read file into memory
    try:
        contents = await file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file",
        ) from exc
    finally:
        await file.close()

    # Size check (50 MB)
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 50 MB limit",
        )

    # Run inference in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(io.BytesIO(contents), language=None, word_timestamps=False)
        )
    except Exception as exc:
        logger.exception("Whisper inference failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription failed",
        ) from exc

    return TranscriptionResponse(
        task_id=task_id,
        text=result["text"].strip(),
        language=result.get("language"),
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model": "large-v3"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WHISPER_PORT", 8001))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)