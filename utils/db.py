import sqlite3
from datetime import datetime
import os

DB_NAME = "worklog.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../worklog.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
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

def add_user(username, password):
    conn = sqlite3.connect(USER_DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

import sqlite3

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
