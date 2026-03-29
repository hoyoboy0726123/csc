import json
from typing import Dict, List, Optional
from openai import AzureOpenAI
from backend.config import Settings
from backend.utils.logger import logger

class LLMService:
    """
    封裝 Azure OpenAI 呼叫與 prompt 管理。
    提供 extract_fields() 與 generate_reply() 兩大公開方法。
    """

    def __init__(self, settings: Settings):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        logger.info("LLMService initialized")

    def extract_fields(self, text: str) -> Dict[str, Optional[str]]:
        """
        從原始文字提取客戶名稱、產品編號、摘要、建議結案日期。
        回傳 Dict，缺失欄位以 None 表示。
        """
        system_prompt = (
            "你是一位客服助手，請從以下文字提取四個欄位："
            "1. customer_name：客戶名稱（公司或個人）"
            "2. product_id：產品編號（若無則回 null）"
            "3. summary：案件摘要，50 字內"
            "4. suggested_close_date：建議結案日期，格式 YYYY-MM-DD，若無則回 null"
            "僅回傳 JSON，勿附說明。"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                max_tokens=300,
            )
            content = response.choices[0].message.content or ""
            data = json.loads(content)
            logger.info("LLM extract_fields succeeded")
            return {
                "customer_name": data.get("customer_name"),
                "product_id": data.get("product_id"),
                "summary": data.get("summary"),
                "suggested_close_date": data.get("suggested_close_date"),
            }
        except Exception as e:
            logger.error(f"LLM extract_fields error: {e}")
            return {
                "customer_name": None,
                "product_id": None,
                "summary": None,
                "suggested_close_date": None,
            }

    def generate_reply(
        self,
        case_summary: str,
        tone: str = "professional",
        history: Optional[List[str]] = None,
    ) -> str:
        """
        依據案件摘要與歷史回覆，生成回覆草稿。
        tone: professional | friendly | apology
        """
        tone_map = {
            "professional": "專業",
            "friendly": "友善",
            "apology": "道歉",
        }
        tone_str = tone_map.get(tone, "專業")
        history_str = "\n".join(history[-3:]) if history else "無"
        system_prompt = (
            f"你是一位客服人員，請用「{tone_str}」語氣，依據以下案件摘要與歷史回覆，"
            "生成一段 80~120 字的回覆草稿，直接以中文回覆，勿附標題或簽名。"
        )
        user_content = f"案件摘要：{case_summary}\n歷史回覆：{history_str}"
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            reply = response.choices[0].message.content or ""
            logger.info("LLM generate_reply succeeded")
            return reply.strip()
        except Exception as e:
            logger.error(f"LLM generate_reply error: {e}")
            return "抱歉，系統暫時無法生成回覆，請稍後再試。"