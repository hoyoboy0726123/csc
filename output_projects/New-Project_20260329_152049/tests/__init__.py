import os
import tempfile
import shutil
from pathlib import Path

# 測試專用全域設定
TEST_DB_NAME = "test_ai_csm.db"

def get_test_db_path() -> Path:
    """回傳測試用的暫存 SQLite 檔案路徑"""
    tmpdir = Path(tempfile.gettempdir()) / "ai_csm_tests"
    tmpdir.mkdir(exist_ok=True)
    return tmpdir / TEST_DB_NAME

def clean_test_db() -> None:
    """清理測試資料庫檔案"""
    db_path = get_test_db_path()
    if db_path.exists():
        db_path.unlink()

def setup_test_env() -> None:
    """初始化測試環境：設定環境變數與乾淨目錄"""
    os.environ["AI_CSM_DB_PATH"] = str(get_test_db_path())
    os.environ["AI_CSM_LOG_LEVEL"] = "CRITICAL"  # 測試時降低日誌雜訊
    clean_test_db()

def teardown_test_env() -> None:
    """清理測試環境"""
    clean_test_db()
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        for item in uploads_dir.glob("test_*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

# 自動載入測試環境
setup_test_env()