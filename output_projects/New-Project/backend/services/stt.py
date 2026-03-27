import os
import uuid
import asyncio
import aiofiles
from typing import Optional
from pathlib import Path
import httpx
from fastapi import HTTPException, UploadFile
from utils.config import get_settings
from utils.exceptions import STTError, FileTooLargeError, UnsupportedMediaTypeError

settings = get_settings()

WHISPER_SERVICE_URL = os.getenv("WHISPER_SERVICE_URL", "http://whisper:8001")
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3"}


class STTService:
    """
    語音轉文字服務
    負責與獨立 Whisper 容器通訊，將音檔轉為文字
    """

    def __init__(self, whisper_url: str = WHISPER_SERVICE_URL):
        self.whisper_url = whisper_url.rstrip("/")

    async def transcribe(self, file: UploadFile, language: Optional[str] = None) -> str:
        """
        非同步上傳音檔至 Whisper 容器並回傳轉錄文字
        """
        # 檔案大小檢查
        if file.size > MAX_AUDIO_SIZE:
            raise FileTooLargeError("音檔超過 50 MB 限制")

        # MIME 類型檢查
        if file.content_type not in ALLOWED_AUDIO_TYPES:
            raise UnsupportedMediaTypeError("僅支援 MP3 與 WAV 格式")

        # 暫存檔案
        tmp_dir = Path("/tmp/v2c_stt")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{uuid.uuid4().hex}_{file.filename}"

        try:
            # 寫入暫存
            async with aiofiles.open(tmp_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    await f.write(chunk)

            # 轉發至 Whisper 容器
            async with httpx.AsyncClient(timeout=120) as client:
                with open(tmp_path, "rb") as f:
                    files = {"file": (file.filename, f, file.content_type)}
                    data = {"language": language} if language else {}
                    resp = await client.post(
                        f"{self.whisper_url}/transcribe",
                        files=files,
                        data=data,
                    )

            if resp.status_code != 200:
                raise STTError(f"Whisper 服務回傳錯誤：{resp.text}")

            result = resp.json()
            text = result.get("text", "").strip()
            if not text:
                raise STTError("無法從音檔識別出任何文字")
            return text

        except httpx.RequestError as exc:
            raise STTError(f"無法連線至 Whisper 服務：{exc}")
        finally:
            # 清理暫存
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    async def health(self) -> bool:
        """
        檢查 Whisper 容器健康狀態
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.whisper_url}/health")
                return resp.status_code == 200
        except Exception:
            return False


# 全域實例
stt_service = STTService()