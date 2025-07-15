import json
import os
import glob
from datetime import datetime
from sqlalchemy import text
from database import get_engine
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
Expected JSON structure for each message:
{
    "message_id": int,           # Unique message ID
    "channel": str,              # Channel name
    "sender": str,               # Sender username or ID
    "text": str,                 # Message text
    "date": str (ISO timestamp), # Message date
    "image_url": str or None     # Image file path or URL
    ... (other fields allowed)
}
"""

class DataLoader:
    """
    Loads raw Telegram message JSON files from the data lake into the raw.telegram_messages table in PostgreSQL.
    Handles table creation and flexible field mapping for different JSON structures.
    """
    def __init__(self):
        """Initialize the DataLoader and ensure the target table exists."""
        self.engine = get_engine()
        self.create_tables()
    
    def create_tables(self):
        """
        Create required tables if they don't exist.
        The raw.telegram_messages table stores all raw message data for downstream analytics.
        """
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE SCHEMA IF NOT EXISTS raw;
                CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                    id SERIAL PRIMARY KEY,
                    message_id BIGINT,
                    channel VARCHAR(255),
                    sender VARCHAR(255),
                    text TEXT,
                    date TIMESTAMP,
                    image_url TEXT,
                    raw_data JSONB
                );
            """))
            conn.commit()

    def load_json_to_postgres(self, json_file_path):
        """
        Load a single JSON file into the raw.telegram_messages table.
        Supports both old and new JSON field names for compatibility.
        Args:
            json_file_path (str): Path to the JSON file to load.
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self.engine.connect() as conn:
                for record in data:
                    # Support both old and new JSON structures
                    message_id = record.get('message_id') or record.get('id')
                    channel = record.get('channel') or record.get('channel_name')
                    sender = record.get('sender') or record.get('from')
                    text_val = record.get('text') or record.get('message_text')
                    date_val = record.get('date') or record.get('message_date')
                    image_url = record.get('image_url') or record.get('media_url')

                    query = text("""
                        INSERT INTO raw.telegram_messages 
                        (message_id, channel, sender, text, date, image_url, raw_data)
                        VALUES (:message_id, :channel, :sender, :text, :date, :image_url, :raw_data)
                        ON CONFLICT DO NOTHING
                    """)

                    conn.execute(query, {
                        'message_id': message_id,
                        'channel': channel,
                        'sender': sender,
                        'text': text_val,
                        'date': date_val,
                        'image_url': image_url,
                        'raw_data': json.dumps(record)
                    })
                conn.commit()
                logger.info(f"Loaded {len(data)} records from {json_file_path}")
        except Exception as e:
            logger.error(f"Error loading {json_file_path}: {e}")

    def load_all_json_files(self):
        """
        Load all JSON files from the data/raw/telegram_messages directory into the database.
        Recursively finds all .json files in the expected data lake structure.
        """
        pattern = "data/raw/telegram_messages/**/*.json"
        json_files = glob.glob(pattern, recursive=True)
        
        for json_file in json_files:
            self.load_json_to_postgres(json_file)

if __name__ == "__main__":
    # Entry point: load all raw Telegram messages into PostgreSQL
    loader = DataLoader()
    loader.load_all_json_files()