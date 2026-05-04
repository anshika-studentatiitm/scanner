import sqlite3
import json

DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # USERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # HISTORY TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            website TEXT,
            result TEXT,  -- stored as JSON string
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ✅ SAVE SCAN RESULT (IMPORTANT FIX)
def save_scan(user_id, website, results):
    conn = get_db()

    conn.execute(
        "INSERT INTO history (user_id, website, result) VALUES (?, ?, ?)",
        (user_id, website, json.dumps(results))  # 🔥 convert to JSON
    )

    conn.commit()
    conn.close()


# ✅ GET HISTORY (PARSE JSON)
def get_history(user_id):
    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM history WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    ).fetchall()

    conn.close()

    data = []

    for row in rows:
        data.append({
            "website": row["website"],
            "date": row["date"],
            "results": json.loads(row["result"])  # 🔥 convert back
        })

    return data