import json
import os
import glob
from datetime import datetime
from sqlalchemy import text
from database import get_engine
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.engine = get_engine()
        self.create_tables()
    
    def create_tables(self):
        """Create required tables if they don't exist"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE SCHEMA IF NOT EXISTS raw;
                CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                    id SERIAL PRIMARY KEY,
                    message_id BIGINT,
                    channel_name VARCHAR(255),
                    message_text TEXT,
                    message_date TIMESTAMP,
                    has_media BOOLEAN,
                    media_type VARCHAR(50),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data JSONB
                );
            """))
            conn.commit()
    
    def load_json_to_postgres(self, json_file_path):
        """Load JSON data into PostgreSQL raw table"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with self.engine.connect() as conn:
                for record in data:
                    query = text("""
                        INSERT INTO raw.telegram_messages 
                        (message_id, channel_name, message_text, message_date, 
                         has_media, media_type, scraped_at, raw_data)
                        VALUES (:message_id, :channel_name, :message_text, :message_date,
                                :has_media, :media_type, :scraped_at, :raw_data)
                        ON CONFLICT DO NOTHING
                    """)
                    
                    conn.execute(query, {
                        'message_id': record['message_id'],
                        'channel_name': record['channel_name'],
                        'message_text': record['message_text'],
                        'message_date': record['message_date'],
                        'has_media': record['has_media'],
                        'media_type': record['media_type'],
                        'scraped_at': record['scraped_at'],
                        'raw_data': json.dumps(record['raw_data'])
                    })
                
                conn.commit()
                logger.info(f"Loaded {len(data)} records from {json_file_path}")
                
        except Exception as e:
            logger.error(f"Error loading {json_file_path}: {e}")
    
    def load_all_json_files(self):
        """Load all JSON files from raw data directory"""
        pattern = "data/raw/telegram_messages/**/*.json"
        json_files = glob.glob(pattern, recursive=True)
        
        for json_file in json_files:
            self.load_json_to_postgres(json_file)

if __name__ == "__main__":
    loader = DataLoader()
    loader.load_all_json_files()