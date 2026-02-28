import os
import psycopg2
from datetime import datetime, timedelta


DATABASE_URL = os.getenv("DATABASE_URL")


# ================= CONNECTION =================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ================= CREATE TABLES =================

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        name TEXT,
        age INTEGER,
        city TEXT,
        bio TEXT,
        photo TEXT,
        gender TEXT,
        looking_for TEXT,
        trial_end TIMESTAMP,
        premium_until TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id SERIAL PRIMARY KEY,
        from_user BIGINT,
        to_user BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(from_user, to_user)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY,
        user1 BIGINT,
        user2 BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user1, user2)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        from_user BIGINT,
        to_user BIGINT,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ================= USERS =================

def user_exists(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None


def activate_premium(user_id, days=30):
    conn = get_connection()
    cur = conn.cursor()

    premium_end = datetime.now() + timedelta(days=days)

    cur.execute(
        "UPDATE users SET premium_until = %s WHERE telegram_id = %s",
        (premium_end, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()


def is_premium(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT premium_until FROM users WHERE telegram_id = %s",
        (user_id,)
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result or not result[0]:
        return False

    return result[0] > datetime.now()


def trial_active(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT trial_end FROM users WHERE telegram_id = %s",
        (user_id,)
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result or not result[0]:
        return False

    return result[0] > datetime.now()


# ================= PROFILES =================

def get_next_profile(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, name, age, city, bio, photo
        FROM users
        WHERE telegram_id != %s
        ORDER BY RANDOM()
        LIMIT 1
    """, (user_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "telegram_id": row[0],
        "name": row[1],
        "age": row[2],
        "city": row[3],
        "bio": row[4],
        "photo": row[5],
    }


# ================= LIKES & MATCHES =================

def add_like(from_user, to_user):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO likes (from_user, to_user) VALUES (%s, %s)",
            (from_user, to_user)
        )
        conn.commit()
    except:
        conn.rollback()

    cur.close()
    conn.close()


def check_match(user1, user2):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM likes
        WHERE from_user = %s AND to_user = %s
    """, (user2, user1))

    liked_back = cur.fetchone()

    if liked_back:
        u1, u2 = sorted([user1, user2])
        try:
            cur.execute(
                "INSERT INTO matches (user1, user2) VALUES (%s, %s)",
                (u1, u2)
            )
            conn.commit()
        except:
            conn.rollback()

        cur.close()
        conn.close()
        return True

    cur.close()
    conn.close()
    return False


# ================= MESSAGES =================

def save_message(from_user, to_user, text):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (from_user, to_user, text) VALUES (%s, %s, %s)",
        (from_user, to_user, text)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_chat(user1, user2):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT from_user, text, created_at
        FROM messages
        WHERE (from_user = %s AND to_user = %s)
           OR (from_user = %s AND to_user = %s)
        ORDER BY created_at ASC
    """, (user1, user2, user2, user1))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows
