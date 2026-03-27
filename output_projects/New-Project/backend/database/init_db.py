import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "v2c.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            gemini_key_enc TEXT,
            groq_key_enc TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prd_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            prd_md TEXT NOT NULL,
            frozen BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS code_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prd_id INTEGER NOT NULL,
            stack TEXT NOT NULL,
            zip_path TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prd_id) REFERENCES prd_history(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()