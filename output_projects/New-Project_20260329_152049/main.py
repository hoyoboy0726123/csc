import os
import sys
from pathlib import Path

import streamlit as st

# 將專案根目錄加入 sys.path，確保能 import 內部模組
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from ui.app import render


def main() -> None:
    """
    AI-CSM 入口點：啟動 Streamlit 應用。
    所有 UI 邏輯委由 ui/app.py 的 render() 負責。
    """
    # 可在此處做最上層的環境檢查或全域例外捕捉
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "false")

    # 交給 UI 模組進行頁面繪製
    render()


if __name__ == "__main__":
    main()