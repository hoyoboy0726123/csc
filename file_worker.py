import os
import shutil
from datetime import datetime

OUTPUT_DIR = "output_projects"

def ensure_output_dir():
    """確保輸出目錄存在。"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def init_project_dir(project_name):
    """建立唯一專案根目錄 (加入時間戳記) 並回傳路徑。"""
    ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (" ", "-", "_")]).strip()
    folder_name = f"{safe_name}_{timestamp}"
    project_path = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(project_path, exist_ok=True)
    return project_path

def write_single_file(project_path, rel_path, content):
    """將單一檔案寫入專案目錄。"""
    full_file_path = os.path.join(project_path, rel_path)
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
    with open(full_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return rel_path

def get_project_file_content(project_path, file_rel_path):
    """讀取專案內特定檔案內容。"""
    full_path = os.path.join(project_path, file_rel_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def update_specific_file(project_path, file_rel_path, new_content):
    """更新專案內的單一檔案。"""
    full_path = os.path.join(project_path, file_rel_path)
    if os.path.exists(full_path):
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False

def delete_project_folder(project_path):
    """物理刪除專案資料夾及其所有內容。"""
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        return True
    return False
