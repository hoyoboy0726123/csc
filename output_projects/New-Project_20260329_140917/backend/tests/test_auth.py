import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import create_app
from backend.config import Settings
from backend.models import Base, User
from backend.utils.security import create_access_token

# 使用 SQLite 記憶體資料庫做為測試隔離
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app = create_app()
    app.dependency_overrides[lambda: db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def seed_user(db):
    user = User(
        email="test@example.com",
        name="Test User",
        role="agent",
        azure_ad_oid="00000000-0000-0000-0000-000000000000",
        disabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(seed_user):
    token = create_access_token(data={"sub": seed_user.email})
    return {"Authorization": f"Bearer {token}"}


def test_login_redirect(client: TestClient):
    """測試 SSO 登入導向端點"""
    resp = client.get("/auth/login")
    assert resp.status_code == 307  # 暫時重定向至 Azure AD


def test_callback_without_code(client: TestClient):
    """缺少 code 參數應回 400"""
    resp = client.get("/auth/callback")
    assert resp.status_code == 400
    assert "code" in resp.json()["detail"].lower()


def test_refresh_token(client: TestClient, auth_headers):
    """測試 JWT 更新端點"""
    resp = client.post("/auth/refresh", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_protected_route_without_token(client: TestClient):
    """未帶 Token 應回 401"""
    resp = client.get("/cases")
    assert resp.status_code == 401


def test_protected_route_with_invalid_token(client: TestClient):
    """帶無效 Token 應回 401"""
    resp = client.get("/cases", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401