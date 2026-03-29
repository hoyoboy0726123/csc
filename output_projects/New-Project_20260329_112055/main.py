import os
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑，確保能正確 import app
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 讀取 .env
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# 初始化資料庫
from app.db import init_db
from app.config import get_settings

settings = get_settings()
init_db(settings.sqlite_path)

# 啟動 Streamlit 應用
from app.app import run
run()