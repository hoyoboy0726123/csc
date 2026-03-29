import os
import time
import json
import re
from groq import Groq
import database
import streamlit as st

# --- 全域請求追蹤器 (滑動窗口) ---
class RequestTracker:
    def __init__(self, rpm_limit=15, window_size=60):
        self.rpm_limit = rpm_limit - 1 
        self.window_size = window_size
        self.request_times = []

    def check_and_wait(self):
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < self.window_size]
        
        if len(self.request_times) >= self.rpm_limit:
            wait_time = self.window_size - (now - self.request_times[0]) + 1
            if wait_time > 0:
                try:
                    st.warning(f"⏳ 觸發 RPM 安全保護：系統將休息 {int(wait_time)} 秒以恢復配額...")
                except:
                    pass
                time.sleep(wait_time)
                return self.check_and_wait()
        
        self.request_times.append(time.time())

tracker = RequestTracker(rpm_limit=15)

def get_groq_client():
    api_key = database.get_config("ACTIVE_KEY")
    if not api_key: return None
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"Groq Client 初始化失敗: {e}")
        return None

def get_dynamic_models():
    api_key = database.get_config("ACTIVE_KEY")
    if not api_key: return []
    try:
        tracker.check_and_wait()
        client = Groq(api_key=api_key)
        return sorted([m.id for m in client.models.list().data if getattr(m, 'active', True)])
    except Exception as e:
        print(f"動態獲取模型失敗: {e}")
        return ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

def test_connection(api_key, model):
    try:
        tracker.check_and_wait()
        client = Groq(api_key=api_key)
        client.chat.completions.create(messages=[{"role": "user", "content": "Hi"}], model=model, max_tokens=5)
        return True, "連線成功！"
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            return True, "金鑰有效，但目前配額已滿 (429)。"
        return False, f"連線失敗: {err_msg}"

def parse_wait_time(error_msg):
    match = re.search(r'try again in (?:(\d+)m)?([\d.]+)s', error_msg)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = float(match.group(2))
        return int(minutes * 60 + seconds) + 2
    return 60

def call_model(system_prompt, user_content):
    api_key = database.get_config("ACTIVE_KEY")
    model = database.get_config("ACTIVE_MODEL", "llama-3.3-70b-versatile")
    if not api_key: return "系統尚未配置 API Key。"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            tracker.check_and_wait()
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
                model=model,
                max_tokens=8000,
                temperature=0.2
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                wait_sec = parse_wait_time(err_str)
                if wait_sec < 30 and attempt < max_retries - 1:
                    time.sleep(wait_sec)
                    continue
                return f"WAIT_REQUIRED:{wait_sec}:{err_str}"
            return f"Groq 呼叫失敗 ({model}): {str(e)}"
    return "連線失敗。"

def generate_prd(raw_text):
    system = "你是一個專業的 PM。請將需求整理成結構化的繁體中文 Markdown PRD。"
    return call_model(system, f"使用者原始需求：\n{raw_text}")

def update_prd_with_feedback(old_prd, feedback):
    system = """你是一個專業的 PM。請回傳「整份更新後的 PRD」，格式為完整的 Markdown。嚴禁只回傳修正片段。"""
    user = f"現有 PRD：\n{old_prd}\n\n修改建議：\n{feedback}"
    return call_model(system, user)

def fix_project_globally(project_path, chat_history):
    api_key = database.get_config("ACTIVE_KEY")
    model = database.get_config("ACTIVE_MODEL", "llama-3.3-70b-versatile")
    
    all_files = []
    file_contents_snippet = ""
    max_total_chars = 30000 
    max_single_file_chars = 5000 
    
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', '.venv', 'node_modules', 'dist', 'build')]
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), project_path)
            all_files.append(rel_path)
            if len(file_contents_snippet) < max_total_chars:
                if rel_path.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.env.example', 'requirements.txt')):
                    full_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(full_path) < 20000:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                snippet = content[:max_single_file_chars]
                                file_contents_snippet += f"\n--- FILE: {rel_path} ---\n{snippet}\n"
                    except: pass

    system_prompt = f"""
    你是一個資深工程師助手。
    目前專案結構：{all_files}
    關鍵檔案內容摘要：
    {file_contents_snippet}
    回傳 JSON：
    {{
      "message": "診斷說明 (繁體中文)",
      "changes": [
        {{ "path": "路徑", "content": "完整代碼", "action": "update/create" }}
      ]
    }}
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)

    try:
        tracker.check_and_wait()
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=messages, model=model, response_format={"type": "json_object"}
        )
        raw_content = chat_completion.choices[0].message.content
        return json.loads(raw_content)
    except Exception as e:
        err_str = str(e)
        if "429" in err_str:
            wait_sec = parse_wait_time(err_str)
            return { "message": f"WAIT_REQUIRED:{wait_sec}:{err_str}", "changes": [] }
        return { "message": f"診斷失敗：{err_str[:100]}", "changes": [] }
