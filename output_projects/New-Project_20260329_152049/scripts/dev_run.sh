#!/usr/bin/env bash
set -euo pipefail

# 開發啟動腳本：一鍵完成環境檢查、資料庫初始化、相依安裝與 Streamlit 啟動
# 僅供本地開發使用，生產部署請改用 Docker 或 PyInstaller 打包

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "=== AI-CSM Dev Runner ==="

# 1. 檢查 Python 版本
if ! python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null; then
  echo "❌ 需要 Python ≥3.10，請先升級"
  exit 1
fi

# 2. 建立/啟動 venv
if [ ! -d "venv" ]; then
  echo "🔨 建立 venv..."
  python3 -m venv venv
fi
source venv/bin/activate

# 3. 安裝相依（若 requirements.txt 有變動會自動更新）
echo "📦 安裝相依..."
pip install -q -r requirements.txt

# 4. 初始化資料庫（若尚未建立）
DB_PATH=$(python -c "from config.settings import get_db_path; print(get_db_path())")
if [ ! -f "$DB_PATH" ]; then
  echo "🗃️  初始化 SQLite DB..."
  python scripts/setup_db.py
fi

# 5. 啟動 Streamlit
echo "🚀 啟動 Streamlit..."
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=false
streamlit run main.py --server.port=$STREAMLIT_SERVER_PORT --server.address=127.0.0.1