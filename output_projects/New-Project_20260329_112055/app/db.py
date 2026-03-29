import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from app.config import get_settings

_settings = get_settings()

def _get_connection_factory() -> sqlite3.Connection:
    conn = sqlite3.connect(
        _settings.sqlite_path,
        check_same_thread=False,
        isolation_level=None,
        timeout=30.0
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

_local = threading.local()

@contextmanager
def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "connection"):
        _local.connection = _get_connection_factory()
    conn: sqlite3.Connection = _local.connection
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise

def init_db(schema_sql: str) -> None:
    Path(_settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(schema_sql)