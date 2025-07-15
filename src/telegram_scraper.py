import asyncio
import json
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, ChannelPrivateError, UsernameNotOccupiedError
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_CHANNELS
import logging
from typing import List, Dict, Any
import time

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramScraper:
    def __init__(self):
        self.client = TelegramClient('session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    async def scrape_channel(self, channel_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scrape messages from a Telegram channel with comprehensive error handling"""
        messages_data = []
        retry_count = 0
        max_retries = 3
        
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
                        
                        messages_data.append(message_data)
                        message_count += 1
                        
                        # Rate limiting
                        if message_count % 10 == 0:
                            await asyncio.sleep(1)
                            
                    except Exception as msg_error:
                        logger.warning(f"Error processing message {message.id}: {msg_error}")
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
                    await asyncio.sleep(5 * retry_count)  # Exponential backoff
        
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
            logger.error(f"Error downloading media for message {message.id}: {e}")
            return None
    
    def save_to_json(self, data, channel_name):
        """Save scraped data to JSON file"""
        date_str = datetime.now().strftime('%Y-%m-%d')
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
    asyncio.run(main())