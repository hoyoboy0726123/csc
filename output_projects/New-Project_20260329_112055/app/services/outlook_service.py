import json
import logging
from typing import Optional

import requests
from msal import ConfidentialClientApplication

from app.auth import get_access_token
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OutlookService:
    """
    封裝 Microsoft Graph API 操作，負責將草稿郵件存入 Outlook 草稿匣。
    """

    def __init__(self) -> None:
        self.client_id: str = settings.AZURE_CLIENT_ID
        self.client_secret: str = settings.AZURE_CLIENT_SECRET
        self.tenant_id: str = settings.AZURE_TENANT_ID
        self.scopes: list[str] = ["https://graph.microsoft.com/MailboxSettings.ReadWrite"]

        self.app: ConfidentialClientApplication = ConfidentialClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )

    def _get_headers(self) -> dict[str, str]:
        token = get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def save_draft(self, to: str, subject: str, body: str) -> str:
        """
        將郵件存入使用者草稿匣，回傳 Graph API 回應中的 draftId。
        """
        url = "https://graph.microsoft.com/v1.0/me/messages"
        payload = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
            "isDraft": True,
        }

        resp = requests.post(url, headers=self._get_headers(), data=json.dumps(payload), timeout=10)
        if resp.status_code not in (200, 201):
            logger.error("Graph API 錯誤: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()

        draft_id: str = resp.json().get("id")
        if not draft_id:
            raise RuntimeError("Graph API 未回傳 draftId")

        logger.info("草稿已建立: %s", draft_id)
        return draft_id


_outlook_service: Optional[OutlookService] = None


def get_outlook_service() -> OutlookService:
    global _outlook_service
    if _outlook_service is None:
        _outlook_service = OutlookService()
    return _outlook_service