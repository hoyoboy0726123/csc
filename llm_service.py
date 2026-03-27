import os
import time
from google import genai
from groq import Groq
import database

def get_active_client():
    """根據資料庫中的全域設定取得 Client。"""
    provider = database.get_config("ACTIVE_PROVIDER")
    api_key = database.get_config("ACTIVE_KEY")
    
    if not provider or not api_key:
        return None, None
    
    try:
        if provider == "Gemini":
            return genai.Client(api_key=api_key), "Gemini"
        elif provider == "Groq":
            return Groq(api_key=api_key), "Groq"
    except Exception as e:
        print(f"Client 初始化失敗: {e}")
    return None, None

def get_dynamic_models(provider, api_key):
    """
    動態獲取模型清單 (2026 最新 SDK 實作)。
    """
    if not provider or not api_key: return []
    models_list = []
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            # 2.0 SDK 的 list() 返回一個可迭代的 Pager 物件
            for m in client.models.list():
                # 只保留支援生成內容的模型
                if hasattr(m, "supported_generation_methods") and "generateContent" in m.supported_generation_methods:
                    name = m.name.replace("models/", "")
                    models_list.append(name)
        elif provider == "Groq":
            client = Groq(api_key=api_key)
            models_list = sorted([m.id for m in client.models.list().data if getattr(m, 'active', True)])
        
        return sorted(models_list) if models_list else []
    except Exception as e:
        print(f"動態獲取模型失敗: {e}")
        # 如果是配額限制，提示使用者
        if "429" in str(e):
            return ["Gemini 配額已滿，請稍後再試"]
        return []

def test_connection(provider, api_key, model):
    """測試 API 連線。"""
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            # 使用最極簡的生成請求
            client.models.generate_content(model=model, contents="Hi")
        elif provider == "Groq":
            client = Groq(api_key=api_key)
            client.chat.completions.create(messages=[{"role": "user", "content": "Hi"}], model=model)
        return True, "連線成功！"
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            return True, "金鑰有效，但目前配額已滿 (429)。您可以儲存設定並在幾分鐘後使用。"
        return False, f"連線失敗: {err_msg}"

def call_model(system_prompt, user_content):
    """全域統一調用入口，增加長文本支援。"""
    client, provider = get_active_client()
    model = database.get_config("ACTIVE_MODEL")
    
    if not client or not model:
        return "系統尚未正確配置主模型與 API Key。"

    try:
        if provider == "Gemini":
            # 增加 Gemini 的 max_output_tokens
            response = client.models.generate_content(
                model=model, 
                contents=[system_prompt, user_content],
                config={"max_output_tokens": 8192, "temperature": 0.2}
            )
            return response.text
        elif provider == "Groq":
            # 增加 Groq 的 max_tokens (視模型支援度，通常 llama3 可達 8k)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
                model=model,
                max_tokens=8000,
                temperature=0.2
            )
            return chat_completion.choices[0].message.content
    except Exception as e:
        if "429" in str(e):
            return "錯誤：API 配額已耗盡 (429)。請等待 1-2 分鐘後再試。"
        return f"API 呼叫失敗 ({provider}/{model}): {str(e)}"

# 功能對接
def generate_prd(raw_text):
    system = "你是一個專業的 PM。請將需求整理成結構化的 Markdown PRD。"
    return call_model(system, f"使用者原始需求：\n{raw_text}")

def update_prd_with_feedback(old_prd, feedback):
    system = "你是一個專業的 PM。請根據建議更新現有的 PRD。"
    user = f"原 PRD：\n{old_prd}\n\n修改建議：\n{feedback}"
    return call_model(system, user)

def fix_code_error(code, error_log):
    system = "你是一個資深工程師。請修復程式碼報錯。"
    user = f"Code:\n{code}\n\nError Log:\n{error_log}"
    return call_model(system, user)
