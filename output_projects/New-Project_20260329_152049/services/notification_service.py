import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import requests
from config.settings import Settings

settings = Settings()
logger = logging.getLogger(__name__)

class NotificationService:
    """
    統一通知發送服務
    支援 SMTP Email 與 Teams Webhook 兩種通道
    """

    @staticmethod
    def send(to: str, message: str, channel: str = "email", subject: Optional[str] = None) -> None:
        """
        對外發送通知
        :param to: 收件者 Email 或 Teams Webhook URL
        :param message: 訊息內容
        :param channel: 通道選擇，預設 'email'，可選 'teams'
        :param subject: Email 主旨（channel='email' 時有效）
        """
        if channel.lower() == "email":
            NotificationService._send_email(to, message, subject or "AI-CSM 系統通知")
        elif channel.lower() == "teams":
            NotificationService._send_teams(to, message)
        else:
            raise ValueError(f"Unsupported channel: {channel}")

    @staticmethod
    def _send_email(to: str, body: str, subject: str) -> None:
        """透過 SMTP 寄送 Email"""
        smtp_host = os.getenv("SMTP_SERVER", "smtp.office365.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASSWORD", "")

        if not smtp_user or not smtp_pass:
            logger.warning("SMTP 帳密未設定，跳過 Email 發送")
            return

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info("Email 通知已發送至 %s", to)
        except Exception as exc:
            logger.error("Email 發送失敗: %s", exc)
            raise

    @staticmethod
    def _send_teams(webhook_url: str, body: str) -> None:
        """透過 Teams Webhook 發送訊息"""
        payload = {"text": body}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Teams 通知已發送")
        except Exception as exc:
            logger.error("Teams 發送失敗: %s", exc)
            raise