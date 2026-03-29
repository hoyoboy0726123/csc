import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional

import openai
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
openai.api_key = settings.openai_api_key
openai.api_base = settings.openai_api_base or "https://api.openai.com/v1"


class Case(BaseModel):
    id: Optional[str] = None
    customer_name: str
    product_id: Optional[str] = None
    summary: str
    due_date: str
    status: str = "To Do"
    assignee_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def _call_llm(messages: list, temperature: float = 0.0, max_tokens: int = 1500) -> str:
    """統一呼叫 OpenAI-compatible 端點"""
    response = openai.ChatCompletion.create(
        model=settings.llm_model or "gpt-4",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=30,
    )
    return response.choices[0].message.content.strip()


def extract_fields(text: str) -> Dict[str, str]:
    """
    從自由文字抽取出
    - customer_name
    - product_id
    - summary
    - due_date
    回傳 dict；若信心值 < 80%，於 dict 中附加 "needs_review"=True
    """
    prompt = f"""
你是一位客服助手，請從以下客戶需求文字中，提取指定欄位並以 JSON 輸出。
僅輸出 JSON，不要有任何解釋或 markdown 標記。

需求文字：
{text}

請提取：
{{
  "customer_name": "客戶名稱（必填）",
  "product_id": "產品編號（若無則空字串）",
  "summary": "摘要（限 200 字內，必填）",
  "due_date": "建議結案日期，格式 yyyy-mm-dd（必填）"
}}

信心值計算：
- 若任一必填欄位空白或格式不符，則附加 "needs_review": true
- 若 product_id 有值但格式明顯錯誤（如不含英文字母或長度<5），也標記 needs_review
"""
    content = _call_llm([{"role": "user", "content": prompt}], temperature=0)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # 防呆：LLM 有時會包 markdown code block
        content = re.sub(r"```json|```", "", content).strip()
        data = json.loads(content)

    # 基本檢核
    needs_review = False
    if not data.get("customer_name"):
        needs_review = True
    if not data.get("summary"):
        needs_review = True
    if not data.get("due_date"):
        needs_review = True
    else:
        # 簡易日期格式檢核
        try:
            datetime.strptime(data["due_date"], "%Y-%m-%d")
        except ValueError:
            needs_review = True
    pid = data.get("product_id", "")
    if pid and (len(pid) < 5 or not re.search(r"[A-Za-z]", pid)):
        needs_review = True

    data["needs_review"] = needs_review
    return data


def generate_reply(case: Case, tone: str = "friendly") -> str:
    """
    依據案件與語氣生成回覆草稿
    tone: friendly / formal / concise
    """
    tone_map = {
        "friendly": "友善、親切",
        "formal": "正式、有禮",
        "concise": "簡潔、直接",
    }
    prompt = f"""
你是客服人員，請用繁體中文撰寫一封回覆信給客戶，語氣：{tone_map.get(tone, "友善")}。

案件摘要：
客戶名稱：{case.customer_name}
產品編號：{case.product_id or "無"}
問題摘要：{case.summary}
建議結案日期：{case.due_date}

回覆信需包含：
1. 感謝客戶反映
2. 簡述我們將如何處理
3. 預計處理/回覆時程
4. 聯絡窗口（簽名留白）

僅輸出信件內文，不含主旨與結尾署名。
"""
    return _call_llm([{"role": "user", "content": prompt}], max_tokens=1000)