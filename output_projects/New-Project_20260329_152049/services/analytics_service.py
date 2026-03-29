import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from database.connection import get_db_connection
from models.ticket import Ticket
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    提供與 Ticket 相關的統計與趨勢分析功能。
    所有方法皆為靜態方法，無需實例化。
    """

    @staticmethod
    def get_ticket_trend(days: int = 30) -> pd.DataFrame:
        """
        回傳最近 N 天內，每日新增與結案趨勢的 DataFrame。
        欄位：date, created_count, closed_count
        """
        if days <= 0:
            raise ValueError("days 必須為正整數")

        conn = get_db_connection()
        sql = """
        SELECT
            date(created_at) AS date,
            SUM(CASE WHEN status = '已解決' THEN 1 ELSE 0 END) AS closed_count,
            COUNT(*) AS created_count
        FROM tickets
        WHERE created_at >= date('now', '-' || ? || ' days')
        GROUP BY date(created_at)
        ORDER BY date
        """
        df = pd.read_sql_query(sql, conn, params=(days,))
        conn.close()

        # 補齊缺日，確保連續日期
        start = datetime.utcnow().date() - timedelta(days=days - 1)
        end = datetime.utcnow().date()
        idx = pd.date_range(start, end, freq="D").date
        df = df.set_index("date").reindex(idx, fill_value=0).rename_axis("date").reset_index()
        return df

    @staticmethod
    def get_agent_load() -> pd.DataFrame:
        """
        回傳每位客服專員的負載統計。
        欄位：assignee_id, assignee_name, pending, in_progress, resolved, total
        """
        conn = get_db_connection()
        sql = """
        SELECT
            u.id          AS assignee_id,
            u.name        AS assignee_name,
            SUM(CASE WHEN t.status = '待處理' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN t.status = '處理中' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN t.status = '已解決' THEN 1 ELSE 0 END) AS resolved,
            COUNT(*)      AS total
        FROM users u
        LEFT JOIN tickets t ON u.id = t.assignee_id
        GROUP BY u.id, u.name
        ORDER BY total DESC
        """
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df

    @staticmethod
    def get_avg_resolution_time(days: int = 30) -> float:
        """
        計算最近 N 天內，已結案案件的平均處理時間（小時）。
        若無資料，回傳 0.0
        """
        conn = get_db_connection()
        sql = """
        SELECT
            AVG((julianday(closed_at) - julianday(created_at)) * 24) AS avg_hours
        FROM tickets
        WHERE status = '已解決'
          AND closed_at IS NOT NULL
          AND created_at >= date('now', '-' || ? || ' days')
        """
        cur = conn.execute(sql, (days,))
        row = cur.fetchone()
        conn.close()
        return float(row["avg_hours"]) if row and row["avg_hours"] is not None else 0.0

    @staticmethod
    def get_unassigned_count() -> int:
        """
        回傳目前未指派（assignee_id IS NULL）的待處理案件數量。
        """
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT COUNT(*) AS cnt FROM tickets WHERE assignee_id IS NULL AND status = '待處理'"
        )
        count = cur.fetchone()["cnt"]
        conn.close()
        return int(count)