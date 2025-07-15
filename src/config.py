"""
config.py
---------
Loads environment variables and configuration settings for the Telegram scraper, database, and API. Provides constants for use throughout the project.
"""
import os
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as e:
    print(f"Error loading .env file: {e}")

# Telegram API configuration
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')

# Database configuration
DB_HOST = os.getenv('POSTGRES_HOST')
DB_PORT = int(os.getenv('POSTGRES_PORT'))
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# API configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Database URL
from urllib.parse import quote_plus
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(str(DB_PASSWORD))}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Telegram channels to scrape
TELEGRAM_CHANNELS = [
    'CheMed123',
    'lobelia4cosmetics',
    'tikvahpharma'
]