import sqlite3
from datetime import datetime, timedelta
from typing import List
import csv
import io
from app.db import get_conn
from app.models.case import Case


class KPIObject:
    """
    簡單的 DTO，用於封裝報表所需的關鍵指標。
    """
    def __init__(
        self,
        pending_count: int,
        avg_processing_hours: float,
        overdue_count: int,
        total_closed: int,
    ):
        self.pending_count = pending_count
        self.avg_processing_hours = avg_processing_hours
        self.overdue_count = overdue_count
        self.total_closed = total_closed


def get_kpi(days: int = 7) -> KPIObject:
    """
    依據最近 days 天內的資料，計算並回傳關鍵指標。
    指標定義：
      - pending_count: 目前處於「待處理」狀態的案件數
      - avg_processing_hours: 已結案案件的平均處理時長（小時）
      - overdue_count: 已逾時（>24h）且尚未結案之案件數
      - total_closed: 在區間內已結案之案件數
    """
    since = datetime.utcnow() - timedelta(days=days)
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) 待處理數量
    cur.execute(
        "SELECT COUNT(*) AS c FROM cases WHERE status = '待處理'"
    )
    pending_count = cur.fetchone()["c"]

    # 2) 區間內已結案之平均處理時長
    cur.execute(
        """
        SELECT AVG((julianday(closed_at) - julianday(created_at)) * 24) AS avg_hours
        FROM cases
        WHERE status = '已解決'
          AND closed_at >= ?
        """,
        (since,),
    )
    row = cur.fetchone()
    avg_processing_hours = float(row["avg_hours"] or 0)

    # 3) 逾時案件數（>24h 且未結案）
    cur.execute(
        """
        SELECT COUNT(*) AS c
        FROM cases
        WHERE status != '已解決'
          AND (julianday('now') - julianday(created_at)) * 24 > 24
        """
    )
    overdue_count = cur.fetchone()["c"]

    # 4) 區間內結案總數
    cur.execute(
        """
        SELECT COUNT(*) AS c
        FROM cases
        WHERE status = '已解決'
          AND closed_at >= ?
        """,
        (since,),
    )
    total_closed = cur.fetchone()["c"]

    conn.close()
    return KPIObject(
        pending_count=pending_count,
        avg_processing_hours=round(avg_processing_hours, 2),
        overdue_count=overdue_count,
        total_closed=total_closed,
    )


def export_csv(cases: List[Case]) -> bytes:
    """
    將給定的 Case 列表匯出為 CSV 格式，回傳 bytes 方便 Streamlit 下載。
    欄位順序：id, customer_name, product_id, summary, due_date, status, assignee_id, created_at, updated_at
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Customer Name",
            "Product ID",
            "Summary",
            "Due Date",
            "Status",
            "Assignee ID",
            "Created At",
            "Updated At",
        ]
    )
    for c in cases:
        writer.writerow(
            [
                c.id,
                c.customer_name,
                c.product_id or "",
                c.summary,
                c.due_date.isoformat() if c.due_date else "",
                c.status,
                c.assignee_id or "",
                c.created_at.isoformat() if c.created_at else "",
                c.updated_at.isoformat() if c.updated_at else "",
            ]
        )
    return output.getvalue().encode("utf-8-sig")