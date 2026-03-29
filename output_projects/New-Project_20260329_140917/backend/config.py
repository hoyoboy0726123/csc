from pydantic import BaseSettings, validator
from typing import Optional
import os


class Settings(BaseSettings):
    # 基本
    APP_NAME: str = "AI-CSM"
    DEBUG: bool = False
    VERSION: str = "v1.0.0"

    # 資料庫
    DB_URL: str

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4-1106"
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"

    # Blob
    BLOB_CONNECTION_STRING: str
    BLOB_CONTAINER_NAME: str = "cases"

    # ERP API
    ERP_API_BASE_URL: str
    ERP_API_KEY: str

    # Email
    EMAIL_SMTP_SERVER: str
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Redis（Rate Limit）
    REDIS_URL: str = "redis://localhost:6379/0"

    # Azure AD SSO
    AZURE_AD_TENANT_ID: str
    AZURE_AD_CLIENT_ID: str
    AZURE_AD_CLIENT_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("DB_URL", pre=True)
    def build_db_url(cls, v: Optional[str], values) -> str:
        if v:
            return v
        user = os.getenv("POSTGRES_USER", "aicms")
        pwd = os.getenv("POSTGRES_PASSWORD", "")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "aicms")
        return f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{db}"


settings = Settings()