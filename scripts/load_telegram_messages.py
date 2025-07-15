import os
import json
import psycopg2
from glob import glob

DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'your_db',
    'user': 'your_user',
    'password': 'your_password'
}

DATA_DIR = os.path.join('data', 'raw', 'telegram_messages')

def get_json_files():
    # Recursively find all .json files in subfolders
    return glob(os.path.join(DATA_DIR, '*', '*.json'))

def load_json_to_postgres():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            message_id BIGINT PRIMARY KEY,
            channel_name TEXT,
            message_text TEXT,
            message_date TIMESTAMPTZ,
            has_media BOOLEAN,
            media_type TEXT,
            scraped_at TIMESTAMPTZ,
            raw_data JSONB,
            media_path TEXT
        );
    """)
    for file_path in get_json_files():
        with open(file_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)
            for msg in messages:
                cur.execute("""
                    INSERT INTO raw.telegram_messages (
                        message_id, channel_name, message_text, message_date, has_media, media_type, scraped_at, raw_data, media_path
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO NOTHING;
                """, (
                    msg.get('message_id'),
                    msg.get('channel_name'),
                    msg.get('message_text'),
                    msg.get('message_date'),
                    msg.get('has_media'),
                    msg.get('media_type'),
                    msg.get('scraped_at'),
                    json.dumps(msg.get('raw_data', {})),
                    msg.get('media_path')
                ))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_json_to_postgres() 