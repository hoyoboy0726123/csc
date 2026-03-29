import os
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.main import create_app
from backend.config import Settings
from backend.models import Base
from backend.utils.logger import logger

# --------------------------------------------------------------------------- #
# 測試專用設定：使用 SQLite in-memory，避免汙染開發/正式資料庫
# --------------------------------------------------------------------------- #
SQLITE_URL = "sqlite:///:memory:"


def get_test_settings() -> Settings:
    """回傳測試專用的 Settings，覆寫 DB_URL 與其他敏感設定。"""
    return Settings(
        _env_file=None,  # 不讀 .env
        DB_URL=SQLITE_URL,
        AZURE_OPENAI_ENDPOINT="https://fake.openai.azure.com",
        AZURE_OPENAI_KEY="fake-key",
        AZURE_OPENAI_DEPLOYMENT="gpt-4-test",
        BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=fake;AccountKey=fake;EndpointSuffix=core.windows.net",
        BLOB_CONTAINER="test-container",
        ERP_API_BASE_URL="https://fake-erp.local",
        ERP_API_KEY="fake-erp-key",
        EMAIL_SMTP_SERVER="fake-smtp.local",
        EMAIL_SMTP_PORT=587,
        EMAIL_USERNAME="test@fake.local",
        EMAIL_PASSWORD="fake-pwd",
        JWT_SECRET_KEY="test-secret-key-please-change-in-production",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRATION_MINUTES=30,
        REDIS_URL="redis://localhost:6379/1",  # 測試用 DB 1
    )


# --------------------------------------------------------------------------- #
# 同步 Engine / Session
# --------------------------------------------------------------------------- #
test_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestSessionLocal = sessionmaker(bind=test_engine, expire_on_commit=False)


# --------------------------------------------------------------------------- #
# Fixture：建立/清除資料庫
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """在測試 session 開始前建立所有表格，結束後 drop 掉。"""
    logger.info("Creating test database tables…")
    Base.metadata.create_all(bind=test_engine)
    yield
    logger.info("Dropping test database tables…")
    Base.metadata.drop_all(bind=test_engine)


# --------------------------------------------------------------------------- #
# Fixture：FastAPI TestClient
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """回傳已掛載測試設定的 FastAPI TestClient。"""
    app = create_app()
    app.dependency_overrides[Settings] = get_test_settings
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# Fixture：獨立 DB Session（供測試函式手動操作）
# --------------------------------------------------------------------------- #
@pytest.fixture
def db() -> Generator[Session, None, None]:
    """提供獨立 Session，測試函式可手動 commit/rollback。"""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# Fixture：黃金資料集（Golden Dataset）
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def golden_dataset() -> list[dict]:
    """載入 LLM 評估用的黃金資料集。"""
    import json
    from pathlib import Path

    fixture_path = Path(__file__).parent / "fixtures" / "golden_dataset.json"
    if not fixture_path.exists():
        logger.warning("Golden dataset not found, returning empty list.")
        return []
    with fixture_path.open(encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# 全域 pytest 設定
# --------------------------------------------------------------------------- #
def pytest_configure(config):
    """設定 pytest 全域環境變數與標記。"""
    # 可在此處註冊自訂標記，例如：
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    # 強制使用 UTC 時區，避免 CI 與本地不一致
    os.environ["TZ"] = "UTC"