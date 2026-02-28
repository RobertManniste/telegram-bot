import os
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ================= CREATE / UPDATE TABLE =================

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
        is_banned BOOLEAN DEFAULT FALSE,
        photo_approved BOOLEAN DEFAULT TRUE,
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


# ================= PREMIUM =================

def activate_premium(user_id, days):
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


def remove_premium(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET premium_until = NULL WHERE telegram_id = %s",
        (user_id,)
    )

    conn.commit()
    cur.close()
    conn.close()


# ================= BAN =================

def ban_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_banned = TRUE WHERE telegram_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


def unban_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_banned = FALSE WHERE telegram_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


# ================= PHOTO MODERATION =================

def approve_photo(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET photo_approved = TRUE WHERE telegram_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_photo(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET photo = NULL, photo_approved = FALSE WHERE telegram_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()
