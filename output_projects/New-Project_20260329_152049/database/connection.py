import sqlite3
import logging
from contextlib import contextmanager
from config.settings import Settings

logger = logging.getLogger(__name__)

@contextmanager
def get_conn() -> sqlite3.Connection:
    """
    取得 SQLite 連線，啟用 WAL 模式與外鍵支援。
    使用 contextmanager 自動關閉連線。
    """
    conn = sqlite3.connect(Settings.get_db_path(), isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
    except Exception as e:
        logger.exception("資料庫連線錯誤: %s", e)
        raise
    finally:
        conn.close()