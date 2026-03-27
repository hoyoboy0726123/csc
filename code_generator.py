import json
import re
import llm_service
import database

def generate_project_skeleton(prd_content):
    """
    分析 PRD 並產出完整的檔案清單 (File Tree)。
    """
    selected_model = database.get_config("ACTIVE_MODEL", "gemini-2.0-flash")
    
    system_prompt = """
    你是一個資深軟體架構師。
    請根據提供的 PRD 文件，列出實作該專案所需的「完整檔案清單」。
    你必須以 JSON 陣列格式回傳字串清單，格式嚴格如下：
    [
      "README.md",
      "requirements.txt",
      "backend/main.py",
      "frontend/src/App.js",
      ...
    ]
    請確保：
    1. 包含所有必要的設定檔 (Docker, .env.example, etc.)。
    2. 檔案路徑邏輯清晰。
    3. 「僅回傳 JSON 陣列」，不要有任何 Markdown 標記或解釋。
    """

    user_content = f"PRD 內容如下：\n{prd_content}"

    try:
        raw_json = llm_service.call_model(system_prompt, user_content)
        
        # 清洗內容
        raw_json = re.sub(r'^[^{[]*', '', raw_json)
        raw_json = re.sub(r'[^}\]]*$', '', raw_json)
        
        return json.loads(raw_json)
    except Exception as e:
        print(f"Skeleton generation error: {e}")
        return []

def generate_file_content(prd_content, file_path, skeleton):
    """
    針對單一檔案生成完整代碼。
    """
    selected_model = database.get_config("ACTIVE_MODEL", "gemini-2.0-flash")
    
    system_prompt = f"""
    你是一個資深工程師。
    請根據 PRD 與整個專案結構，撰寫檔案「{file_path}」的完整內容。
    
    專案結構如下：
    {json.dumps(skeleton, indent=2)}
    
    要求：
    1. 代碼必須完整、可執行，不可使用佔位符 (如 //...rest of code)。
    2. 確保與結構中其他檔案的引用路徑一致。
    3. 「僅回傳代碼內容」，不要有任何 Markdown 代碼塊標記 (如 ```python)。
    """

    user_content = f"PRD 內容如下：\n{prd_content}"

    try:
        content = llm_service.call_model(system_prompt, user_content)
        
        # 移除可能的 Markdown 標記
        if "```" in content:
            # 嘗試擷取中間內容
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)
            
        return content.strip()
    except Exception as e:
        print(f"File generation error ({file_path}): {e}")
        return f"# Error generating file: {str(e)}"

def update_code_snippet(old_code, error_log):
    """
    整合修復邏輯。
    """
    return llm_service.fix_code_error(old_code, error_log)
