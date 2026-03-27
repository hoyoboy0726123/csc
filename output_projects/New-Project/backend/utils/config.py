import os
from functools import lru_cache
from pydantic import BaseSettings, Field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    # FastAPI
    app_name: str = "Voice-to-Code Pipeline"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")

    # Database
    database_url: str = Field(
        default=f"sqlite:///{BASE_DIR}/v2c.db", env="DATABASE_URL"
    )

    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # JWT
    jwt_secret: str = Field(env="JWT_SECRET")

    # File Upload
    max_file_size_mb: int = 50
    allowed_audio_extensions: set = {".mp3", ".wav", ".m4a", ".flac"}
    upload_dir: Path = BASE_DIR / "static" / "uploads"
    zip_cache_dir: Path = BASE_DIR / "static" / "zip_cache"

    # Whisper STT
    whisper_api_url: str = Field(
        default="http://whisper:8001/transcribe", env="WHISPER_API_URL"
    )
    whisper_timeout: int = 120  # seconds

    # LLM Providers
    gemini_model: str = Field(default="gemini-1.5-pro", env="GEMINI_MODEL")
    groq_model: str = Field(default="llama3-70b-8192", env="GROQ_MODEL")
    default_provider: str = Field(default="gemini", env="DEFAULT_PROVIDER")

    # Model Router
    router_timeout: int = 30  # seconds
    router_retry_attempts: int = 3
    router_backoff_factor: float = 0.5

    # Prompt Chains
    prd_chain_max_tokens: int = 2048
    code_chain_max_tokens: int = 4096
    fix_chain_max_tokens: int = 2048

    # Quota
    daily_prd_quota: int = Field(default=10, env="DAILY_PRD_QUOTA")
    daily_code_quota: int = Field(default=5, env="DAILY_CODE_QUOTA")
    quota_reset_hour: int = Field(default=0, env="QUOTA_RESET_HOUR")

    # Crypto
    aes_key_size: int = 32  # 256 bits
    aes_iv_size: int = 16  # 128 bits

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Ensure directories exist
settings = get_settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.zip_cache_dir.mkdir(parents=True, exist_ok=True)