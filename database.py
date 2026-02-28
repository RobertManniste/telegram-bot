import os
import psycopg2


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id BIGINT PRIMARY KEY,
        name TEXT,
        age INT,
        bio TEXT,
        photo_file_id TEXT,
        photo_status TEXT DEFAULT 'pending',
        is_banned BOOLEAN DEFAULT FALSE,
        trial_end TIMESTAMP,
        premium_until TIMESTAMP,
        messages_today INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # LIKES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        user_id BIGINT,
        liked_user_id BIGINT,
        PRIMARY KEY (user_id, liked_user_id)
    )
    """)

    # MESSAGES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        sender_id BIGINT,
        receiver_id BIGINT,
        text TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ADMIN LOGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_logs (
        id SERIAL PRIMARY KEY,
        action TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
