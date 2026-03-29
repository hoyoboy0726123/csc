import sqlite3
from typing import List, Optional
from database.connection import get_conn

class User:
    """使用者資料類別"""
    def __init__(self, id: int, name: str, email: str, role: str):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

    @staticmethod
    def list_all() -> List["User"]:
        """取得所有使用者"""
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, email, role FROM users ORDER BY id")
            rows = cur.fetchall()
        return [User(id=r[0], name=r[1], email=r[2], role=r[3]) for r in rows]