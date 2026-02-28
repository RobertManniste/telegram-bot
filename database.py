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
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        name TEXT,
        age INT,
        city TEXT,
        bio TEXT,
        photo TEXT,
        gender TEXT,
        looking_for TEXT,
        premium BOOLEAN DEFAULT FALSE,
        trial_end TIMESTAMP,
        messages_today INT DEFAULT 0,
        last_message_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # LIKES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id SERIAL PRIMARY KEY,
        from_user BIGINT,
        to_user BIGINT
    );
    """)

    # MATCHES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY,
        user1 BIGINT,
        user2 BIGINT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
