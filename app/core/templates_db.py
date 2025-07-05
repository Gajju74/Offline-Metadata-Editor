
import sqlite3

def init_db(db_path="templates.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            key TEXT,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_template(name, metadata_dict, db_path="templates.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for key, value in metadata_dict.items():
        cursor.execute("INSERT INTO templates (name, key, value) VALUES (?, ?, ?)", (name, key, value))
    conn.commit()
    conn.close()

def load_template(name, db_path="templates.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM templates WHERE name = ?", (name,))
    result = dict(cursor.fetchall())
    conn.close()
    return result
