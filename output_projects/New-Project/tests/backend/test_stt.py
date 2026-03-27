import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.stt import STTService
from backend.utils.exceptions import STTError, FileFormatError
import io
import os


@pytest.fixture
def stt_service():
    return STTService(whisper_url="http://whisper:8000")


@pytest.fixture
def fake_audio_file():
    """產生一個假的音檔 bytes"""
    return io.BytesIO(b"RIFF....WAVEfmt....data....")


class TestSTTService:
    """STTService 單元測試"""

    # ---------- 同步測試 ----------
    def test_validate_file_format_success(self, stt_service):
        for ext in ["mp3", "wav", "m4a", "ogg"]:
            assert stt_service._validate_file_format(f"test.{ext}") is None

    def test_validate_file_format_fail(self, stt_service):
        with pytest.raises(FileFormatError):
            stt_service._validate_file_format("test.txt")

    def test_validate_file_size_success(self, stt_service):
        assert stt_service._validate_file_size(49 * 1024 * 1024) is None  # 49 MB

    def test_validate_file_size_fail(self, stt_service):
        with pytest.raises(STTError):
            stt_service._validate_file_size(51 * 1024 * 1024)  # 51 MB

    @patch("os.path.getsize", return_value=1024 * 1024)
    def test_validate_file_path_success(self, mock_getsize, stt_service):
        assert stt_service._validate_file_path("/tmp/test.wav") is None

    @patch("os.path.getsize", return_value=1024 * 1024)
    def test_validate_file_path_fail_not_exist(self, mock_getsize, stt_service):
        mock_getsize.side_effect = FileNotFoundError
        with pytest.raises(STTError):
            stt_service._validate_file_path("/tmp/not_exist.wav")

    # ---------- 非同步測試 ----------
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_transcribe_success(self, mock_post, stt_service, fake_audio_file):
        # 模擬 Whisper 回傳
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"text": "這是一個測試"})
        mock_post.return_value.__aenter__.return_value = mock_resp

        text = await stt_service.transcribe(fake_audio_file, filename="test.wav")
        assert text == "這是一個測試"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_transcribe_whisper_error(self, mock_post, stt_service, fake_audio_file):
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.text = AsyncMock(return_value="Internal Server Error")
        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(STTError):
            await stt_service.transcribe(fake_audio_file, filename="test.wav")

    @pytest.mark.asyncio
    async def test_transcribe_invalid_format(self, stt_service, fake_audio_file):
        with pytest.raises(FileFormatError):
            await stt_service.transcribe(fake_audio_file, filename="test.txt")

    @pytest.mark.asyncio
    async def test_transcribe_large_file(self, stt_service, fake_audio_file):
        # 模擬大檔案
        fake_audio_file.size = 52 * 1024 * 1024
        with pytest.raises(STTError):
            await stt_service.transcribe(fake_audio_file, filename="test.wav")

    # ---------- 整合測試 ----------
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_transcribe_real_filename(self, mock_post, stt_service):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"text": "整合測試成功"})
        mock_post.return_value.__aenter__.return_value = mock_resp

        with patch("builtins.open", return_value=io.BytesIO(b"RIFF....")) as mock_file:
            text = await stt_service.transcribe_file("/tmp/demo.wav")
            assert text == "整合測試成功"
            mock_file.assert_called_once_with("/tmp/demo.wav", "rb")

    @pytest.mark.asyncio
    async def test_transcribe_file_not_exist(self, stt_service):
        with pytest.raises(STTError):
            await stt_service.transcribe_file("/tmp/not_exist.wav")