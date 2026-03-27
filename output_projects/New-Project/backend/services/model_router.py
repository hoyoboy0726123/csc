import os
import json
import httpx
import asyncio
from typing import Dict, Any, Optional
from backend.utils.config import settings
from backend.utils.exceptions import ModelRouterError
import google.generativeai as genai
from groq import Groq

class ModelRouter:
    """
    根據任務類型與用戶選擇，動態路由到 Gemini 或 Groq。
    支援 PRD、Code、Fix 三種鏈，並自動重試與降級。
    """

    def __init__(self):
        self.gemini_key: Optional[str] = None
        self.groq_key: Optional[str] = None
        self._init_clients()

    def set_keys(self, gemini_key: Optional[str], groq_key: Optional[str]):
        self.gemini_key = gemini_key
        self.groq_key = groq_key
        self._init_clients()

    def _init_clients(self):
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-pro")
        else:
            self.gemini_model = None

        if self.groq_key:
            self.groq_client = Groq(api_key=self.groq_key)
        else:
            self.groq_client = None

    async def route(
        self,
        task: str,
        prompt: str,
        model_preference: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> str:
        """
        task: "prd" | "code" | "fix"
        model_preference: "gemini" | "groq" | None(自動)
        """
        if model_preference:
            model = model_preference
        else:
            model = await self._auto_select_model(task)

        for attempt in range(2):
            try:
                if model == "gemini" and self.gemini_model:
                    return await self._call_gemini(prompt, max_tokens, temperature)
                elif model == "groq" and self.groq_client:
                    return await self._call_groq(prompt, max_tokens, temperature)
                else:
                    raise ModelRouterError("模型未初始化或金鑰無效")
            except Exception as e:
                if attempt == 0:
                    model = "groq" if model == "gemini" else "gemini"
                    await asyncio.sleep(1)
                else:
                    raise ModelRouterError(f"模型路由重試失敗: {e}")

        raise ModelRouterError("模型路由最終失敗")

    async def _auto_select_model(self, task: str) -> str:
        # 簡單策略：PRD 用 Gemini，Code/Fix 用 Groq
        if task == "prd":
            return "gemini" if self.gemini_model else "groq"
        else:
            return "groq" if self.groq_client else "gemini"

    async def _call_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
        )
        return response.text

    async def _call_groq(self, prompt: str, max_tokens: int, temperature: float) -> str:
        completion = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return completion.choices[0].message.content


model_router = ModelRouter()