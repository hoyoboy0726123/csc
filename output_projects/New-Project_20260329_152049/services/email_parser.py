import email
import email.policy
from email.message import EmailMessage
from typing import Dict
import logging

# 全域日誌設定由 config/settings.py 載入，此處僅取用
logger = logging.getLogger(__name__)


def parse_eml(eml_text: str) -> Dict[str, str]:
    """
    將 RFC-822 格式的 Email 文字解析為結構化欄位。
    回傳 Dict 至少包含：
    {
      "subject": "",
      "from": "",
      "to": "",
      "date": "",
      "body": ""
    }
    若解析失敗，回傳空 Dict 並寫入日誌。
    """
    try:
        # email 6+ 建議使用 policy.default 以支援 UTF-8
        msg = email.message_from_string(eml_text, policy=email.policy.default)
    except Exception as e:
        logger.exception("無法解析 eml_text: %s", e)
        return {}

    result: Dict[str, str] = {}

    # 基本欄位
    result["subject"] = str(msg.get("Subject", ""))
    result["from"] = str(msg.get("From", ""))
    result["to"] = str(msg.get("To", ""))
    result["date"] = str(msg.get("Date", ""))

    # 取得純文字內容
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition", ""))
            # 只取純文字且非附件
            if ctype == "text/plain" and "attachment" not in cdispo:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_parts.append(payload.decode("utf-8", errors="replace"))
                except Exception as e:
                    logger.warning("解析 multipart 內容錯誤: %s", e)
    else:
        # 非 multipart
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body_parts.append(payload.decode("utf-8", errors="replace"))
        except Exception as e:
            logger.warning("解析單段內容錯誤: %s", e)

    result["body"] = "\n".join(body_parts).strip()

    return result