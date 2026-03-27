import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import get_db
from backend.models.user import User
from backend.models.prd import PRDHistory
from backend.models.code_version import CodeVersion
from backend.services.crypto import encrypt_key, decrypt_key
from backend.utils.config import settings
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def override_get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_headers(override_get_db):
    user = User(email="test@example.com")
    override_get_db.add(user)
    override_get_db.commit()
    token = "test_jwt_token"
    return {"Authorization": f"Bearer {token}"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_audio_unauthorized():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"fake audio data")
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            response = client.post("/api/v1/upload-audio", files={"file": f})
        assert response.status_code == 401
    finally:
        os.remove(tmp_path)

@patch("backend.routers.upload.process_audio_task")
def test_upload_audio_authorized(mock_process, auth_headers):
    mock_process.delay = MagicMock(return_value=MagicMock(id="fake_task_id"))
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"fake audio data")
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            response = client.post("/api/v1/upload-audio", files={"file": f}, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == "fake_task_id"
        assert data["status"] == "processing"
    finally:
        os.remove(tmp_path)

def test_get_prd_not_found(auth_headers):
    response = client.get("/api/v1/prd/nonexistent", headers=auth_headers)
    assert response.status_code == 404

def test_patch_prd_unauthorized():
    response = client.patch("/api/v1/prd/some_id", json={"instruction": "change price"})
    assert response.status_code == 401

@patch("backend.routers.prd.update_prd_with_instruction")
def test_patch_prd_authorized(mock_update, auth_headers):
    mock_update.return_value = {"status": "completed", "prd_md": "# Updated PRD"}
    response = client.patch("/api/v1/prd/some_id", json={"instruction": "change price"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["prd_md"] == "# Updated PRD"

def test_generate_code_unauthorized():
    response = client.post("/api/v1/code", json={"prd_id": 1, "stack": "python"})
    assert response.status_code == 401

@patch("backend.routers.code.generate_code_zip")
def test_generate_code_authorized(mock_generate, auth_headers):
    mock_generate.return_value = {"zip_path": "/tmp/fake.zip", "version": 1}
    response = client.post("/api/v1/code", json={"prd_id": 1, "stack": "python"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["zip_path"] == "/tmp/fake.zip"
    assert data["version"] == 1

def test_fix_code_unauthorized():
    response = client.post("/api/v1/fix", json={"code_id": 1, "error": "ImportError"})
    assert response.status_code == 401

@patch("backend.routers.fix.fix_code_error")
def test_fix_code_authorized(mock_fix, auth_headers):
    mock_fix.return_value = {"fixed_code": "import os", "version": 2}
    response = client.post("/api/v1/fix", json={"code_id": 1, "error": "ImportError"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["fixed_code"] == "import os"
    assert data["version"] == 2

def test_crypto_roundtrip():
    key = "sk-123456"
    encrypted = encrypt_key(key)
    decrypted = decrypt_key(encrypted)
    assert decrypted == key