import sqlite3

DB_NAME = "lovia.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            age TEXT,
            city TEXT,
            premium INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ===== ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ =====
def add_user(telegram_id, name, age, city):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users (telegram_id, name, age, city)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, name, age, city))

    conn.commit()
    conn.close()


# ===== ПОЛУЧИТЬ ПОЛЬЗОВАТЕЛЯ =====
def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users WHERE telegram_id = ?
    """, (telegram_id,))

    user = cursor.fetchone()
    conn.close()

    return user


# ===== АКТИВИРОВАТЬ PREMIUM =====
def activate_premium(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users SET premium = 1 WHERE telegram_id = ?
    """, (telegram_id,))

    conn.commit()
    conn.close()