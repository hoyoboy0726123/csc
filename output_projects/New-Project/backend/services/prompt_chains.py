import json
import re
from typing import Dict, List, Optional

from backend.services.model_router import ModelRouter
from backend.utils.config import settings
from backend.utils.exceptions import PromptChainError


class PromptChains:
    """
    封裝所有 LLM prompt chain 邏輯：
    1. PRD 生成鏈
    2. 程式碼生成鏈
    3. 錯誤修復鏈
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    # --------------------------------------------------
    # PRD 鏈
    # --------------------------------------------------
    async def generate_prd(self, transcript: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        根據語音轉譯文字產生標準 PRD Markdown。
        """
        system = (
            "你是一位資深產品經理，專精於將口語需求轉化為結構化 PRD。請嚴格遵守以下格式：\n"
            "- 使用繁體中文（台灣用語）。\n"
            "- 輸出僅包含 Markdown，不要多餘解釋。\n"
            "- 必填欄位：功能清單、User Flow、ER 圖（以 mermaid 語法）、API 規格（OpenAPI 3.0 格式）。\n"
            "- 若資訊不足，請以「TODO:」標註待補項目，不要自行假設商業邏輯。\n"
        )
        user_prompt = f"原始需求：{transcript}"
        if history:
            user_prompt += "\n\n歷史對話：\n"
            for turn in history[-5:]:
                user_prompt += f"{turn['role']}: {turn['content']}\n"

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}]
        prd_md = await self.router.call(messages, task="prd")
        if not prd_md:
            raise PromptChainError("PRD 生成失敗，模型回傳空值")
        return prd_md

    async def refine_prd(self, prd: str, instruction: str) -> str:
        """
        根據自然語言指令微調 PRD。
        """
        system = (
            "你負責微調 PRD，僅修改與指令相關內容，保留其餘章節不動。輸出完整 Markdown。"
        )
        user = f"原始 PRD：\n{prd}\n\n修改指令：{instruction}"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        refined = await self.router.call(messages, task="prd")
        if not refined:
            raise PromptChainError("PRD 微調失敗")
        return refined

    # --------------------------------------------------
    # 程式碼生成鏈
    # --------------------------------------------------
    async def pick_stack(self, prd: str) -> str:
        """
        根據 PRD 關鍵字自動推薦技術棧：python / react / nodejs
        """
        system = (
            "你是一位全端架構師，依據需求選擇最合適技術棧。僅回傳小寫單一值：python、react、nodejs。"
        )
        user = f"PRD 內容：\n{prd[:2000]}"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        stack = await self.router.call(messages, task="code")
        stack = stack.strip().lower()
        if stack not in {"python", "react", "nodejs"}:
            stack = "python"  # 預設值
        return stack

    async def generate_code(self, prd: str, stack: str) -> Dict[str, str]:
        """
        生成完整專案檔案結構與程式碼。
        回傳 dict: {file_path: file_content}
        """
        system = (
            "你是一位全端工程師，專精於生成可直接運行的專案。請遵守：\n"
            "- 僅輸出 JSON，格式：{\"file_path\": \"file_content\", ...}\n"
            "- 檔案路徑使用 Unix 斜線，如 src/main.py。\n"
            "- 包含 README.md、requirements.txt 或 package.json，確保本地可一鍵啟動。\n"
            "- 預設使用 SQLite 與本地檔案，零外部金鑰即可跑。\n"
            "- 程式碼需符合社群最佳實踐，含基本錯誤處理。\n"
        )
        user = f"技術棧：{stack}\n\nPRD：\n{prd}"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        raw = await self.router.call(messages, task="code")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # 簡易 regex 提取 JSON
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise PromptChainError("無法解析生成程式碼 JSON")
            data = json.loads(match.group(0))
        if not isinstance(data, dict):
            raise PromptChainError("生成程式碼格式錯誤")
        return data

    # --------------------------------------------------
    # 錯誤修復鏈
    # --------------------------------------------------
    async def fix_error(self, stack: str, code_files: Dict[str, str], error_log: str) -> Dict[str, str]:
        """
        根據錯誤日誌自動修復程式碼。
        回傳 dict: {file_path: new_content}
        """
        system = (
            "你是一位除錯專家，僅修改與錯誤相關的檔案，其餘保持不動。輸出 JSON 格式："
            "{\"file_path\": \"new_content\", ...}"
        )
        user = (
            f"技術棧：{stack}\n\n"
            f"錯誤日誌：\n{error_log}\n\n"
            f"目前程式碼：\n{json.dumps(code_files, ensure_ascii=False, indent=2)}"
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        raw = await self.router.call(messages, task="fix")
        try:
            fixed = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise PromptChainError("無法解析修復結果")
            fixed = json.loads(match.group(0))
        if not isinstance(fixed, dict):
            raise PromptChainError("修復結果格式錯誤")
        return fixed

    async def incremental_feature(self, stack: str, code_files: Dict[str, str], prd_patch: str) -> Dict[str, str]:
        """
        根據增量 PRD 需求進行開發，不破壞既有功能。
        """
        system = (
            "你負責增量開發，僅新增或微調必要檔案，確保向後相容。輸出 JSON 格式："
            "{\"file_path\": \"new_content\", ...}"
        )
        user = (
            f"技術棧：{stack}\n\n"
            f"增量需求：{prd_patch}\n\n"
            f"目前程式碼：\n{json.dumps(code_files, ensure_ascii=False, indent=2)}"
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        raw = await self.router.call(messages, task="code")
        try:
            inc = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise PromptChainError("無法解析增量結果")
            inc = json.loads(match.group(0))
        if not isinstance(inc, dict):
            raise PromptChainError("增量結果格式錯誤")
        return inc