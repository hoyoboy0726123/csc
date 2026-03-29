import json
import logging
from typing import Dict

import openai
from openai import OpenAI

from config.settings import get_openai_key, get_llm_model
from models.ticket import Ticket

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 抽象服務：提取欄位、生成回覆草稿"""

    def __init__(self):
        self.client = OpenAI(api_key=get_openai_key())
        self.model = get_llm_model()

    # ---------- 公開介面 ----------
    def extract_fields(self, text: str) -> Dict[str, str]:
        """從原始文字提取結構化欄位"""
        if not text.strip():
            return {}

        prompt = f"""
你是一名客服助手，請從以下客訴內容提取四個欄位，並以 JSON 輸出：
{{
  "customer_name": "客戶名稱（若無則填''）",
  "product_id": "產品編號（若無則填''）",
  "summary": "50 字內摘要",
  "suggested_due_date": "建議結案日，格式 yyyy-mm-dd（若無則填''）"
}}

客訴內容：
{text}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=300,
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            logger.info("LLM 提取欄位成功: %s", data)
            return data
        except json.JSONDecodeError:
            logger.exception("LLM 回應非有效 JSON")
            return {}
        except Exception:
            logger.exception("LLM 提取欄位錯誤")
            return {}

    def generate_reply(self, ticket: Ticket) -> str:
        """依據 Ticket 生成回覆草稿"""
        if not ticket:
            return ""

        prompt = f"""
你是客服專員，請根據以下案件資訊，撰寫一段禮貌、專業的「初次回覆草稿」：
- 案件標題：{ticket.title}
- 客戶名稱：（若有請代入，若無則用「親愛的客戶」）
- 語氣：同理、感謝、提供下一步

請直接輸出信件內文（不含主旨），控制在 150 字內。
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )
            draft = response.choices[0].message.content.strip()
            logger.info("LLM 生成回覆草稿完成，長度 %s 字", len(draft))
            return draft
        except Exception:
            logger.exception("LLM 生成回覆錯誤")
            return ""