#!/usr/bin/env python3
"""
資料庫初始化腳本
讀取 database/schema.sql 並執行，以建立 SQLite 資料庫與所有表格。
"""

import sqlite3
import sys
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = PROJECT_ROOT / "database" / "schema.sql"


def main() -> None:
    """建立或重置 SQLite 資料庫"""
    db_path = PROJECT_ROOT / "database" / "ai_csm.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_FILE.exists():
        print(f"❌ 找不到 schema 檔案：{SCHEMA_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"✅ 資料庫已初始化：{db_path}")
    except Exception as e:
        print(f"❌ 初始化失敗：{e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()