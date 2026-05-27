import sqlite3
import pandas as pd

DB_NAME = "knowledge_base.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            keywords TEXT,
            subject TEXT,
            legal_basis TEXT,
            description TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_entry(category, keywords, subject, legal_basis, description, source="Manual"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO knowledge (category, keywords, subject, legal_basis, description, source)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (category, keywords, subject, legal_basis, description, source))
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM knowledge ORDER BY created_at DESC", conn)
    conn.close()
    return df

def search_data(query):
    conn = sqlite3.connect(DB_NAME)
    # 模糊搜尋所有主要欄位
    sql = """
        SELECT * FROM knowledge 
        WHERE category LIKE ? OR keywords LIKE ? OR subject LIKE ? OR legal_basis LIKE ? OR description LIKE ?
        ORDER BY created_at DESC
    """
    search_term = f"%{query}%"
    df = pd.read_sql_query(sql, conn, params=(search_term, search_term, search_term, search_term, search_term))
    conn.close()
    return df

def delete_entry(entry_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM knowledge WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
