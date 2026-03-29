import sqlite3
import os
from datetime import datetime

DB_NAME = "dev_system.db"

def get_connection():
    """建立 SQLite 資料庫連線。"""
    return sqlite3.connect(DB_NAME)

def init_db():
    """初始化資料庫。"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 專案表
    cursor.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, root_path TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    # 2. PRD 紀錄
    cursor.execute('CREATE TABLE IF NOT EXISTS prd_records (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, content TEXT, version INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    # 3. 核心設定表 (金鑰、供應商、模型)
    cursor.execute('CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)')

    conn.commit()
    conn.close()

def save_config(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_config(key, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM system_config WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else default

# 專案相關 CRUD 保持不變
def create_project(name, root_path):
    """建立新專案，儲存本地時間。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO projects (name, root_path, created_at) VALUES (?, ?, ?)', (name, root_path, now))
    p_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return p_id

def get_all_projects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
    res = cursor.fetchall()
    conn.close()
    return res

def save_prd(project_id, content, version):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO prd_records (project_id, content, version) VALUES (?, ?, ?)', (project_id, content, version))
    conn.commit()
    conn.close()

def get_latest_prd(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content, version FROM prd_records WHERE project_id = ? ORDER BY version DESC LIMIT 1', (project_id,))
    res = cursor.fetchone()
    conn.close()
    return res

if __name__ == "__main__":
    init_db()
