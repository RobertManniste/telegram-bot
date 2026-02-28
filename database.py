import os
import psycopg2

def create_tables():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id SERIAL PRIMARY KEY,
        from_user BIGINT,
        to_user BIGINT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
