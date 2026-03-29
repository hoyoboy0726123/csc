import os
from utils.llm_utils import get_llm_response
from models.case import get_case
from models.assignee import get_assignee

class AIService:
    def extract_info_from_text(self, text: str):
        """
        從文本中提取案件資訊。

        Args:
        - text (str): 案件文本。

        Returns:
        - dict: 提取的案件資訊。
        """
        prompt = f"從以下文本中提取案件資訊：{text}。請提供客戶名稱、產品編號、摘要和建議結案日期。"
        response = get_llm_response(prompt)
        # 解析回應並返回提取的資訊
        info = {}
        # 簡化起見，假設回應格式固定
        lines = response.splitlines()
        for line in lines:
            if "客戶名稱：" in line:
                info["client_name"] = line.split("：")[-1].strip()
            elif "產品編號：" in line:
                info["product_number"] = line.split("：")[-1].strip()
            elif "摘要：" in line:
                info["summary"] = line.split("：")[-1].strip()
            elif "建議結案日期：" in line:
                info["suggested_close_date"] = line.split("：")[-1].strip()
        return info

    def generate_reply_draft(self, case_id: int):
        """
        生成案件回覆草稿。

        Args:
        - case_id (int): 案件 ID。

        Returns:
        - str: 回覆草稿。
        """
        case = get_case(case_id)
        assignee = get_assignee(case.assignee)
        prompt = f"根據以下案件資訊生成回覆草稿：案件 ID {case_id}，客戶名稱 {case.client_name}，產品編號 {case.product_number}，摘要 {case.summary}。負責人是 {assignee.name}。"
        response = get_llm_response(prompt)
        return response