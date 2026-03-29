from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import sqlite3
from database.connection import get_connection


@dataclass
class Ticket:
    id: Optional[int] = None
    title: str = ""
    status: str = "待處理"          # 待處理 / 處理中 / 已解決
    assignee_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # ---------- 實例方法 ----------
    def save(self) -> None:
        """將自身資料寫入或更新至 SQLite；若為新資料會回填 self.id"""
        conn = get_connection()
        if self.id is None:
            # INSERT
            sql = """
                INSERT INTO tickets (title, status, assignee_id, created_at)
                VALUES (?, ?, ?, ?)
            """
            cur = conn.execute(
                sql,
                (
                    self.title,
                    self.status,
                    self.assignee_id,
                    self.created_at.isoformat(timespec="seconds"),
                ),
            )
            self.id = cur.lastrowid
        else:
            # UPDATE
            sql = """
                UPDATE tickets
                SET title = ?,
                    status = ?,
                    assignee_id = ?
                WHERE id = ?
            """
            conn.execute(sql, (self.title, self.status, self.assignee_id, self.id))
        conn.commit()

    # ---------- 靜態方法 ----------
    @staticmethod
    def list_by_status(status: str) -> List[Ticket]:
        """依狀態查詢所有案件"""
        conn = get_connection()
        cur = conn.execute(
            "SELECT id, title, status, assignee_id, created_at FROM tickets WHERE status = ?",
            (status,),
        )
        rows = cur.fetchall()
        tickets = []
        for row in rows:
            tickets.append(
                Ticket(
                    id=row[0],
                    title=row[1],
                    status=row[2],
                    assignee_id=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                )
            )
        return tickets