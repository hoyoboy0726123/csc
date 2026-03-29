import os
import logging
from typing import Dict

import openai

# 設定 OpenAI API 金鑰
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 初始化 OpenAI API
openai.api_key = OPENAI_API_KEY

# 設定 logger
logger = logging.getLogger(__name__)

def get_llm_response(prompt: str) -> str:
    """
    從 LLM 取得回應。

    Args:
    - prompt (str): 輸入提示。

    Returns:
    - str: LLM 回應。
    """
    try:
        # 使用 OpenAI GPT-4 模型
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        # 取得回應文字
        response_text = response.choices[0].message.content
        return response_text
    except Exception as e:
        # 日誌記錄錯誤
        logger.error(f"LLM 回應錯誤：{e}")
        return ""

def extract_info_from_text(text: str) -> Dict:
    """
    從文字中提取資訊。

    Args:
    - text (str): 輸入文字。

    Returns:
    - Dict: 提取的資訊。
    """
    # 定義提取資訊的提示
    prompt = f"請從以下文字中提取客戶名稱、產品編號、摘要與建議結案日期：{text}"
    # 從 LLM 取得回應
    response = get_llm_response(prompt)
    # 解析回應文字
    info = {}
    # 簡單的解析邏輯，實際上可能需要更複雜的 NLP 處理
    lines = response.splitlines()
    for line in lines:
        if "客戶名稱：" in line:
            info["client_name"] = line.replace("客戶名稱：", "").strip()
        elif "產品編號：" in line:
            info["product_number"] = line.replace("產品編號：", "").strip()
        elif "摘要：" in line:
            info["summary"] = line.replace("摘要：", "").strip()
        elif "建議結案日期：" in line:
            info["suggested_close_date"] = line.replace("建議結案日期：", "").strip()
    return info

def generate_reply_draft(case_id: int, case_info: Dict) -> str:
    """
    生成回覆草稿。

    Args:
    - case_id (int): 案件 ID。
    - case_info (Dict): 案件資訊。

    Returns:
    - str: 回覆草稿。
    """
    # 定義生成回覆草稿的提示
    prompt = f"請根據以下案件資訊生成回覆草稿：案件 ID {case_id}，客戶名稱 {case_info['client_name']}，產品編號 {case_info['product_number']}，摘要 {case_info['summary']}"
    # 從 LLM 取得回應
    response = get_llm_response(prompt)
    return response