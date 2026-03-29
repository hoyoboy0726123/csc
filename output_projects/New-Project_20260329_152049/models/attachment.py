import os
import sqlite3
from datetime import datetime
from typing import Optional
from database.connection import get_conn

class Attachment:
    """
    附件資料類別，對應資料庫 attachment 表。
    公開欄位：id, ticket_id, file_path
    靜態方法：create_from_upload()
    """

    def __init__(self, id: int, ticket_id: int, file_path: str):
        self.id = id
        self.ticket_id = ticket_id
        self.file_path = file_path

    @staticmethod
    def create_from_upload(ticket_id: int, uploaded_file) -> "Attachment":
        """
        將上傳的檔案存放到本地 uploads/ 目錄並寫入資料庫。
        uploaded_file: Streamlit UploadedFile-like object，需有 .name 與 .getbuffer()
        """
        os.makedirs("uploads", exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        safe_name = f"{timestamp}_{uploaded_file.name}"
        dest_path = os.path.join("uploads", safe_name)

        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO attachment (ticket_id, file_path) VALUES (?, ?)",
                (ticket_id, dest_path),
            )
            conn.commit()
            attachment_id = cur.lastrowid

        return Attachment(id=attachment_id, ticket_id=ticket_id, file_path=dest_path)