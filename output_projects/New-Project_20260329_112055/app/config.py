import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """集中管理所有環境變數與全域設定，供全專案引用。"""

    # LLM 端點
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(None, env="OPENAI_API_BASE")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(0.2, env="OPENAI_TEMPERATURE")

    # Azure AD OAuth
    azure_client_id: str = Field(..., env="AZURE_CLIENT_ID")
    azure_client_secret: str = Field(..., env="AZURE_CLIENT_SECRET")
    azure_tenant_id: str = Field(..., env="AZURE_TENANT_ID")
    azure_authority: str = Field(None, env="AZURE_AUTHORITY")
    azure_redirect_path: str = Field("/getAToken", env="AZURE_REDIRECT_PATH")

    # Microsoft Graph
    graph_scopes: list[str] = Field(
        default=["https://graph.microsoft.com/Mail.ReadWrite"],
        env="GRAPH_SCOPES",
    )

    # SQLite
    sqlite_path: Path = Field(Path("data/app.db"), env="SQLITE_PATH")

    # 系統
    app_secret_key: str = Field(..., env="APP_SECRET_KEY")
    app_env: str = Field("prod", env="APP_ENV")  # dev / prod
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自動補足 Azure authority
        if not self.azure_authority:
            self.azure_authority = f"https://login.microsoftonline.com/{self.azure_tenant_id}"
        # 確保目錄存在
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """提供單例 Settings，方便全專案引入。"""
    return Settings()