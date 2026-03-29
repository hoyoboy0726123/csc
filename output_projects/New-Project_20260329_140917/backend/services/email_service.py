import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from config import settings
from utils.logger import logger


class EmailService:
    """發送 Outlook 信件與寫入草稿匣"""

    def __init__(self):
        self.smtp_server = settings.EMAIL_SMTP_SERVER
        self.smtp_port = settings.EMAIL_SMTP_PORT
        self.sender = settings.EMAIL_SENDER
        self.password = settings.EMAIL_PASSWORD

    def send(
        self,
        to: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> None:
        """立即發送信件"""
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype="html")

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender, self.password)
                server.send_message(msg)
            logger.info(f"Email sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise

    def save_draft(
        self,
        to: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> None:
        """將草稿寫入 Outlook 草稿匣（透過 Microsoft Graph API）"""
        # 實作時可透過 Graph API POST /me/messages 並設 isDraft=true
        # 此處先以 logger 模擬
        logger.info(f"Draft saved: to={to}, subject={subject}")
        # TODO: 整合 Microsoft Graph SDK
        pass