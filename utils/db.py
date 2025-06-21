import sqlite3
from datetime import datetime
import os
import bcrypt


DB_NAME = "worklog.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../worklog.db")
USER_DB_NAME = "users.db"
USER_DB_PATH = os.path.join(BASE_DIR, "../users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS worklog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            start TEXT,
            end TEXT,
            title TEXT,
            memo TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_entry(username, date, start, end, title, memo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO worklog (username, date, start, end, title, memo) VALUES (?, ?, ?, ?, ?, ?)",
        (username, date, start, end, title, memo)
    )
    conn.commit()
    conn.close()


def get_entries_by_date(username, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, start, end, title, memo FROM worklog WHERE username = ? AND date = ?", (username, date))
    rows = c.fetchall()
    conn.close()
    return rows


def update_entry(entry_id, start, end, title, memo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE worklog SET start = ?, end = ?, title = ?, memo = ? WHERE id = ?",
        (start, end, title, memo, entry_id)
    )
    conn.commit()
    conn.close()


def delete_entry(entry_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM worklog WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

def init_user_db():
    conn = sqlite3.connect(USER_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(USER_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def user_exists(username):
    conn = sqlite3.connect(USER_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_user(username, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(USER_DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
    conn.commit()
    conn.close()


def get_entries_by_month(username, year_month):
    """
    指定ユーザーの指定年月（例: '2025-06'）の作業記録を日付ごとにまとめて返す
    戻り値: {'2025-06-15': [{'title': '作業A', 'duration': 60}, ...], ...}
    """
    conn = sqlite3.connect(DB_PATH)  # 必要に応じて DB_PATH に置き換えてください
    cursor = conn.cursor()

    query = """
        SELECT date, title, 
               (strftime('%H', end) - strftime('%H', start)) * 60 + 
               (strftime('%M', end) - strftime('%M', start)) as duration
        FROM worklog
        WHERE username = ? AND strftime('%Y-%m', date) = ?
        ORDER BY date
    """
    cursor.execute(query, (username, year_month))
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for date_str, title, duration in rows:
        if date_str not in result:
            result[date_str] = []
        result[date_str].append({"title": title, "duration": duration})
    return result

def init_pending_log_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_log (
            username TEXT PRIMARY KEY,
            start_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_pending_start(username, start_time):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('REPLACE INTO pending_log (username, start_time) VALUES (?, ?)', (username, start_time))
    conn.commit()
    conn.close()

def get_pending_start(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT start_time FROM pending_log WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    return datetime.fromisoformat(row[0]) if row else None

def clear_pending_start(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM pending_log WHERE username = ?', (username,))
    conn.commit()
    conn.close()
