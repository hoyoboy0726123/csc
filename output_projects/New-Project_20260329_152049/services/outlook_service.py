import logging
import win32com.client
import pythoncom
from typing import Optional

logger = logging.getLogger(__name__)


class OutlookService:
    """
    僅支援 Windows 平台，依賴 win32com。
    提供 create_draft 方法將草稿存入 Outlook 草稿匣。
    """

    def __init__(self):
        # 延遲 COM 初始化，方便單元測試 mock
        self._app: Optional[win32com.client.Dispatch] = None

    def _ensure_app(self):
        if self._app is None:
            pythoncom.CoInitialize()
            self._app = win32com.client.Dispatch("Outlook.Application")
            logger.debug("Outlook.Application COM 已初始化")

    def create_draft(self, to: str, subject: str, body: str) -> str:
        """
        建立 Outlook 草稿郵件並回傳 EntryID，供後續開啟或追蹤。
        參數：
            to: 收件者，可為單一信箱或分號分隔
            subject: 主旨
            body: 純文字或 HTML 內容
        回傳：
            草稿的 EntryID
        """
        self._ensure_app()
        mail = self._app.CreateItem(0)  # 0 = olMailItem
        mail.To = to
        mail.Subject = subject
        # 若 body 含 HTML 標籤，自動切換 HTML 格式
        if "<html>" in body.lower():
            mail.HTMLBody = body
        else:
            mail.Body = body
        mail.Save()  # 存入草稿匣
        entry_id = mail.EntryID
        logger.info("Outlook 草稿已建立，EntryID=%s", entry_id)
        return entry_id