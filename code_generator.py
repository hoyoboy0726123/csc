import json
import re
import llm_service
import database

def generate_project_skeleton(prd_content):
    """
    第一階段：分析 PRD 並產出完整的檔案清單。
    """
    system_prompt = """
    你是一個資深架構師。請根據 PRD 列出「完整檔案路徑清單」。
    必須回傳純 JSON 陣列，例如 ["main.py", "models/user.py"]。
    「僅回傳 JSON 內容」，不要有解釋。
    """
    user_content = f"PRD 內容：\n{prd_content}"
    
    raw_json = llm_service.call_model(system_prompt, user_content)
    
    # 處理 TPD 等待協定
    if isinstance(raw_json, str) and raw_json.startswith("WAIT_REQUIRED"):
        return raw_json

    try:
        # 清洗內容
        cleaned_json = re.sub(r'^[^{[]*', '', raw_json)
        cleaned_json = re.sub(r'[^}\]]*$', '', cleaned_json)
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"Skeleton 解析錯誤: {e}, 原始內容: {raw_json}")
        return []

def generate_interface_map(prd_content, skeleton):
    """
    第二階段：建立「全域介面合約」。
    """
    system_prompt = f"""
    你是一個首席架構師。針對以下專案結構，請定義各檔案間的「開發合約」。
    包含公開函數、類別與依賴關係。
    必須回傳 JSON 物件，格式：{{"filename": "說明"}}
    """
    user_content = f"專案結構：{skeleton}\n\nPRD 內容：\n{prd_content}"
    
    raw_json = llm_service.call_model(system_prompt, user_content)
    
    # 處理 TPD 等待協定
    if isinstance(raw_json, str) and raw_json.startswith("WAIT_REQUIRED"):
        return raw_json

    try:
        cleaned_json = re.sub(r'^[^{]*', '', raw_json)
        cleaned_json = re.sub(r'[^}]*$', '', cleaned_json)
        return json.loads(cleaned_json)
    except:
        return {}

def generate_file_content(prd_content, file_path, skeleton, interface_map):
    """
    第三階段：優化後的逐檔生成。
    僅傳送相關的合約片段以節省 Token。
    """
    # 提取相關合約：包含目前檔案，以及可能被引用的核心檔案 (如 db, models, config)
    relevant_keys = [file_path]
    core_keywords = ["db", "model", "config", "util", "schema", "auth"]
    for k in interface_map.keys():
        if any(kw in k.lower() for kw in core_keywords):
            relevant_keys.append(k)

    sliced_map = {k: interface_map[k] for k in set(relevant_keys) if k in interface_map}

    system_prompt = f"""
    你是一個資深工程師。請撰寫「{file_path}」的完整內容。
    必須符合相關介面合約：{json.dumps(sliced_map)}

    要求：
    1. 參考結構：{json.dumps(skeleton[:50])}... (僅顯示部分路徑)
    2. 僅回傳代碼，不含 Markdown。
    """
    # 精簡 PRD：擷取核心開發部分 (假設 PRD 很長)
    short_prd = prd_content[:5000] 
    user_content = f"需求摘要：\n{short_prd}"

    content = llm_service.call_model(system_prompt, user_content)

    if isinstance(content, str) and content.startswith("WAIT_REQUIRED"):
        return content

    if "```" in content:
        lines = content.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines[-1].startswith("```"): lines = lines[:-1]
        content = "\n".join(lines)
    return content.strip()


def update_code_snippet(old_code, error_log):
    return llm_service.fix_code_error(old_code, error_log)
