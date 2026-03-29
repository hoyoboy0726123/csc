#!/usr/bin/env bash
set -euo pipefail

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
VENV_DIR="${PROJECT_ROOT}/venv"

# 清理舊檔
rm -rf "${DIST_DIR}" "${BUILD_DIR}"

# 建立並啟用虛擬環境
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

# 安裝依賴
pip install --upgrade pip setuptools wheel
pip install -r "${PROJECT_ROOT}/requirements.txt"
pip install pyinstaller

# 打包單一執行檔
PyInstaller \
  --onefile \
  --distpath "${DIST_DIR}" \
  --workpath "${BUILD_DIR}" \
  --specpath "${PROJECT_ROOT}" \
  --add-data "${PROJECT_ROOT}/config:config" \
  --add-data "${PROJECT_ROOT}/database:database" \
  --add-data "${PROJECT_ROOT}/ui:ui" \
  --add-data "${PROJECT_ROOT}/uploads:uploads" \
  --add-data "${PROJECT_ROOT}/logs:logs" \
  --hidden-import streamlit \
  --hidden-import jinja2 \
  --hidden-import yaml \
  --hidden-import sqlite3 \
  --hidden-import openai \
  --hidden-import PyMuPDF \
  --hidden-import python_dotenv \
  --hidden-import streamlit_authenticator \
  --hidden-import win32com \
  "${PROJECT_ROOT}/main.py"

# 複製必要靜態檔案
cp -r "${PROJECT_ROOT}/config" "${DIST_DIR}/"
cp -r "${PROJECT_ROOT}/database" "${DIST_DIR}/"
cp -r "${PROJECT_ROOT}/ui" "${DIST_DIR}/"
cp -r "${PROJECT_ROOT}/uploads" "${DIST_DIR}/"
cp -r "${PROJECT_ROOT}/logs" "${DIST_DIR}/"
cp "${PROJECT_ROOT}/.env.example" "${DIST_DIR}/.env.example"

echo "✅ 執行檔已生成於 ${DIST_DIR}/main"
echo "📦 複製 ${DIST_DIR} 至目標機器即可離線運行"