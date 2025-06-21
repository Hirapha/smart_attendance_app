import sqlite3
import hashlib

USER_DB = "users.db"

def init_user_db():
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )""")
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
              (username, hash_password(password)))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False
