"""
telegram_scraper.py
-------------------
Scrapes messages and media from Telegram channels using Telethon, validates and saves them as JSON files in a structured data lake. Handles rate limits, errors, and logs all actions.
"""
import asyncio
import json
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, ChannelPrivateError, UsernameNotOccupiedError
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_CHANNELS
from loguru import logger
from typing import List, Dict, Any
import time
from jsonschema import validate, ValidationError

# JSON schema for message validation
MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "message_id": {"type": "integer"},
        "channel_name": {"type": "string"},
        "message_text": {"type": "string"},
        "message_date": {"type": ["string", "null"]},
        "has_media": {"type": "boolean"},
        "media_type": {"type": ["string", "null"]},
        "scraped_at": {"type": "string"},
        "raw_data": {"type": "object"},
        "media_path": {"type": ["string", "null"]}
    },
    "required": ["message_id", "channel_name", "message_text", "message_date", "has_media", "media_type", "scraped_at", "raw_data"]
}

class TelegramScraper:

    """
    TelegramScraper uses Telethon to scrape messages and media from Telegram channels.
    Handles rate limits, errors, and downloads media to the data lake.
    Uses structured logging and validates output JSON.
    """
    def __init__(self):
        self.client = TelegramClient('session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    async def scrape_channel(self, channel_name: str, limit: int = 100) -> List[Dict[str, Any]]:

        """Scrape messages from a Telegram channel with comprehensive error handling"""

        """
        Scrape messages from a Telegram channel with retries and exponential backoff.
        Args:
            channel_name (str): The Telegram channel username or link.
            limit (int): Max number of messages to scrape.
        Returns:
            List[Dict[str, Any]]: List of message dicts with metadata and media info.
        """
        messages_data = []
        retry_count = 0
        max_retries = 5
        backoff = 5
        
        while retry_count < max_retries:
            try:
                logger.info(f"Starting scrape for channel: {channel_name} (attempt {retry_count + 1})")
                await self.client.start(phone=TELEGRAM_PHONE)
                entity = await self.client.get_entity(channel_name)
                
                message_count = 0
                async for message in self.client.iter_messages(entity, limit=limit):
                    try:
                        message_data = {
                            'message_id': message.id,
                            'channel_name': channel_name.replace('@', ''),
                            'message_text': message.text or '',
                            'message_date': message.date.isoformat() if message.date else None,
                            'has_media': message.media is not None,
                            'media_type': self._get_media_type(message.media),
                            'scraped_at': datetime.now().isoformat(),
                            'raw_data': {
                                'views': getattr(message, 'views', 0),
                                'forwards': getattr(message, 'forwards', 0),
                                'replies': getattr(message.replies, 'replies', 0) if message.replies else 0,
                                'grouped_id': getattr(message, 'grouped_id', None)
                            }
                        }
                        # Download media if present
                        if message.media and isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                            media_path = await self._download_media(message, channel_name)
                            message_data['media_path'] = media_path
                        # Validate message structure
                        try:
                            validate(instance=message_data, schema=MESSAGE_SCHEMA)
                        except ValidationError as ve:
                            logger.warning(f"Message {message.id} failed schema validation: {ve.message}")
                            continue
                        # Warn if message is empty
                        if not message_data['message_text'].strip():
                            logger.warning(f"Message {message.id} in {channel_name} is empty and will be skipped.")
                            continue
                        messages_data.append(message_data)
                        message_count += 1
                        # Rate limiting
                        if message_count % 10 == 0:
                            await asyncio.sleep(1)
                    except Exception as msg_error:
                        logger.warning(f"Error processing message {getattr(message, 'id', '?')}: {msg_error}")
                        continue
                logger.info(f"Successfully scraped {len(messages_data)} messages from {channel_name}")
                break
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                retry_count += 1
            except ChannelPrivateError:
                logger.error(f"Channel {channel_name} is private or inaccessible")
                break
            except UsernameNotOccupiedError:
                logger.error(f"Channel {channel_name} does not exist")
                break
            except Exception as e:
                logger.error(f"Error scraping channel {channel_name} (attempt {retry_count + 1}): {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying after {backoff * retry_count} seconds...")
                    await asyncio.sleep(backoff * retry_count)  # Exponential backoff
        return messages_data
    
    def _get_media_type(self, media):
        """Determine media type"""
        if not media:
            return None
        if isinstance(media, MessageMediaPhoto):
            return 'photo'
        elif isinstance(media, MessageMediaDocument):
            return 'document'
        return 'other'
    
    async def _download_media(self, message, channel_name: str) -> str:
        """Download media files with proper error handling and path management"""
        try:
            date_str = message.date.strftime('%Y-%m-%d') if message.date else 'unknown'
            clean_channel_name = channel_name.replace('@', '')
            media_dir = f"data/raw/media/{clean_channel_name}/{date_str}"
            os.makedirs(media_dir, exist_ok=True)
            # Get proper extension from media
            if isinstance(message.media, MessageMediaPhoto):
                ext = '.jpg'
            elif hasattr(message.media.document, 'mime_type'):
                mime_type = message.media.document.mime_type
                if 'image/jpeg' in mime_type:
                    ext = '.jpg'
                elif 'image/png' in mime_type:
                    ext = '.png'
                elif 'video' in mime_type:
                    ext = '.mp4'
                else:
                    ext = '.bin'  # Generic binary file
            else:
                ext = '.bin'
            filename = f"{message.id}_{int(message.date.timestamp())}{ext}"
            file_path = os.path.join(media_dir, filename)
            # Check if file already exists
            if os.path.exists(file_path):
                logger.info(f"Media file already exists: {filename}")
                return file_path
            await self.client.download_media(message, file=file_path)
            logger.info(f"Downloaded media: {filename}")
            return file_path
        except Exception as e:
            logger.error(f"Error downloading media for message {getattr(message, 'id', '?')}: {e}")
            return None
    
    def save_to_json(self, data, channel_name):

        """Save scraped data to JSON file"""

        """
        Save scraped messages to a JSON file in the data lake.
        Validates file naming and structure.
        Args:
            data (list): List of message dicts.
            channel_name (str): Channel name for file naming.
        Returns:
            None
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        # Enforce strict naming: YYYY-MM-DD/channel_name.json
        output_dir = f"data/raw/telegram_messages/{date_str}"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{channel_name}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} messages to {filename}")

async def main():
    scraper = TelegramScraper()
    for channel in TELEGRAM_CHANNELS:
        logger.info(f"Scraping channel: {channel}")
        messages = await scraper.scrape_channel(channel, limit=100)
        scraper.save_to_json(messages, channel)
    await scraper.client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Uncaught exception in main: {e}")