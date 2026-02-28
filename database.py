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
        trial_end TIMESTAMP,
        premium_until TIMESTAMP,
        messages_today INT DEFAULT 0
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

    conn.commit()
    cur.close()
    conn.close()
