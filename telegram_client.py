"""
Telegram client wrapper for relay bot functionality
"""

import asyncio
import logging
from typing import Optional
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    FloodWaitError
)

from config import Config
from message_processor import MessageProcessor

logger = logging.getLogger(__name__)

class TelegramRelayClient:
    """Telegram client for relay bot functionality."""

    def __init__(self, api_id: int, api_hash: str, phone_number: str, config: Config):
        """Initialize Telegram client."""
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.config = config
        self.client = None
        self.message_processor = MessageProcessor(config)
        self._forwarding_queue = asyncio.Queue()
        self._is_running = False
        self.processed_message_ids = set()

    async def start(self):
        """Start the Telegram client and begin monitoring."""
        try:
            self.client = TelegramClient('relay_bot_session', self.api_id, self.api_hash)
            logger.info("Connecting to Telegram...")
            await self.client.connect()

            if not await self.client.is_user_authorized():
                logger.error("User not authorized. Please run: python simple_auth.py")
                return False

            logger.info("User already authorized, proceeding...")
            config_errors = self.config.validate_config()
            if config_errors:
                logger.error("Configuration errors found:")
                for error in config_errors:
                    logger.error(f"  - {error}")
                return False

            await self._verify_group_access()
            self._setup_message_handlers()
            self._is_running = True
            asyncio.create_task(self._forwarding_worker())
            
            # Test message reception from each group
            await self._test_message_reception()
            
            # Verify handler setup
            logger.info(f"✅ Message handlers active for groups: {self.config.source_groups}")
            logger.info("🎯 Bot is now monitoring for new messages...")
            logger.info("Telegram relay bot started successfully")
            return True

        except SessionPasswordNeededError:
            logger.error("Two-factor authentication is enabled. Please disable it or implement 2FA support.")
            return False
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            return False

    async def handle_new_message(self, event):
        """Handle new messages from source groups."""
        try:
            message = event.message
            source_group_id = event.chat_id  # Get the source group ID from the event
            
            # Get group title for better logging
            try:
                entity = await self.client.get_entity(source_group_id)
                group_title = getattr(entity, 'title', f'Group {source_group_id}')
            except:
                group_title = f'Group {source_group_id}'
            
            logger.info(f"📨 NEW MESSAGE from {group_title} ({source_group_id}): {message.text[:100] if message.text else 'Media/No text'}...")
            
            # Check if this group is in our source groups list
            if source_group_id not in self.config.source_groups:
                logger.warning(f"⚠️ Received message from non-configured group {source_group_id} - ignoring")
                return

            if message.id in self.processed_message_ids:
                logger.debug(f"Message {message.id} has already been processed. Skipping...")
                return

            # Clean up old message IDs to prevent memory issues (keep last 1000)
            if len(self.processed_message_ids) > 1000:
                old_ids = list(self.processed_message_ids)[:500]
                for old_id in old_ids:
                    self.processed_message_ids.discard(old_id)

            self.processed_message_ids.add(message.id)
            logger.debug(f"New message received from group {source_group_id}: {message.text[:50] if message.text else 'Media message'}...")

            # Check if message passes filters first
            message_text = message.text or (message.caption if hasattr(message, 'caption') else "")
            
            # If message has no text but has media, forward the media directly
            if not message_text and hasattr(message, 'media') and message.media:
                logger.info(f"📎 Forwarding media message from {source_group_id}")
                await self._forwarding_queue.put({
                    'message': message,
                    'processed_text': None,  # Will forward original media
                    'is_media_only': True
                })
                return
            
            # Process text messages through filters and replacements
            processed_text = await self.message_processor.process_message(message, source_group_id)
            if processed_text is not None:
                await self._forwarding_queue.put({
                    'message': message,
                    'processed_text': processed_text,
                    'is_media_only': False
                })

        except Exception as e:
            logger.error(f"Error handling new message: {e}")
            # Continue processing other messages even if one fails

    async def _forward_message(self, original_message, processed_text, is_media_only=False):
        """Forward a message to target groups with topic support."""
        for target_group_id in self.config.target_groups:
            retries = 0
            while retries < self.config.max_retries:
                try:
                    # Check if this group has a specific topic configured
                    target_topic = self.config.target_topics.get(str(target_group_id))

                    if target_topic and 'topic_id' in target_topic:
                        topic_id = target_topic['topic_id']
                        logger.info(f"Attempting to send message to group {target_group_id}, topic {topic_id} ({target_topic.get('topic_name', 'Unknown')})...")

                        if is_media_only and hasattr(original_message, 'media') and original_message.media:
                            # Forward original media with caption
                            await self.client.forward_messages(
                                target_group_id,
                                original_message,
                                from_peer=original_message.peer_id
                            )
                        else:
                            # Send processed text to specific topic/thread
                            await self.client.send_message(
                                target_group_id, 
                                processed_text,
                                reply_to=topic_id
                            )
                        logger.info(f"Message successfully sent to {target_group_id} topic {topic_id}.")
                    else:
                        # Send to main group chat (no topic)
                        logger.info(f"Attempting to send message to group {target_group_id} (main chat)...")
                        
                        if is_media_only and hasattr(original_message, 'media') and original_message.media:
                            # Forward original media
                            await self.client.forward_messages(
                                target_group_id,
                                original_message,
                                from_peer=original_message.peer_id
                            )
                        else:
                            await self.client.send_message(target_group_id, processed_text)
                        logger.info(f"Message successfully sent to {target_group_id}.")

                    break

                except FloodWaitError as e:
                    logger.warning(f"Flood wait error: sleeping for {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                    retries += 1

                except Exception as e:
                    logger.error(f"Error forwarding to group {target_group_id}: {e}")
                    retries += 1
                    if retries < self.config.max_retries:
                        await asyncio.sleep(2 ** retries)

    async def _verify_group_access(self):
        """Verify access to configured groups."""
        for group_id in self.config.source_groups:
            try:
                entity = await self.client.get_entity(group_id)
                logger.info(f"✅ Successfully accessed group: {group_id} (Title: {getattr(entity, 'title', 'Unknown')})")
                
                # Check if we can read messages from this group
                try:
                    messages = await self.client.get_messages(group_id, limit=1)
                    logger.info(f"✅ Can read messages from group {group_id}")
                except Exception as read_error:
                    logger.warning(f"⚠️ Cannot read messages from group {group_id}: {read_error}")
                    
            except Exception as e:
                logger.error(f"❌ Error accessing group {group_id}: {e}")

    def _setup_message_handlers(self):
        """Set up message handlers."""
        try:
            # Clear any existing handlers first
            self.client.remove_event_handler(self._message_handler, events.NewMessage)
            
            # Register handler for each group individually to ensure proper coverage
            for group_id in self.config.source_groups:
                logger.info(f"🎯 Registering message handler for group: {group_id}")
                self.client.add_event_handler(
                    self._message_handler,
                    events.NewMessage(chats=[group_id], incoming=True)
                )
            
            # Also register a general handler for all groups as backup
            self.client.add_event_handler(
                self._message_handler,
                events.NewMessage(chats=self.config.source_groups, incoming=True)
            )
            
            logger.info(f"✅ Message handlers registered for {len(self.config.source_groups)} source groups")
            logger.info(f"📋 Monitoring groups: {self.config.source_groups}")
            
        except Exception as e:
            logger.error(f"❌ Error setting up message handlers: {e}")
    
    async def _message_handler(self, event):
        """Internal message handler method."""
        await self.handle_new_message(event)
    
    async def _test_message_reception(self):
        """Test if we can receive recent messages from each group."""
        logger.info("🧪 Testing message reception from each group...")
        for group_id in self.config.source_groups:
            try:
                # Get recent messages to test accessibility
                messages = await self.client.get_messages(group_id, limit=3)
                logger.info(f"✅ Group {group_id}: Can access {len(messages)} recent messages")
                
                if messages:
                    latest_msg = messages[0]
                    logger.info(f"📋 Latest message from {group_id}: {latest_msg.text[:50] if latest_msg.text else 'Media message'}...")
                else:
                    logger.warning(f"⚠️ Group {group_id}: No recent messages found")
                    
            except Exception as e:
                logger.error(f"❌ Group {group_id}: Cannot access messages - {e}")
        logger.info("🧪 Message reception test completed")

    async def _forwarding_worker(self):
        """Forward messages from the queue to target groups."""
        while self._is_running:
            try:
                item = await self._forwarding_queue.get()
                is_media_only = item.get('is_media_only', False)
                await self._forward_message(item['message'], item['processed_text'], is_media_only)
                
                # Apply minimal delay for rate limiting
                if self.config.forward_delay > 0:
                    await asyncio.sleep(self.config.forward_delay)
                    
                self._forwarding_queue.task_done()
            except Exception as e:
                logger.error(f"Error in forwarding worker: {e}")
                self._forwarding_queue.task_done()
                await asyncio.sleep(1)  # Brief pause before continuing

    def _has_media(self, message):
        """Check if message contains media content."""
        return hasattr(message, 'media') and message.media is not None

    async def run_until_disconnected(self):
        """Run the client until disconnected with automatic reconnection."""
        logger.info("🔄 Starting message monitoring loop...")
        while True:
            try:
                logger.info("📡 Client running and listening for messages...")
                await self.client.run_until_disconnected()
                logger.warning("🚨 Client disconnected - checking if intentional...")
                break  # Exit if deliberately disconnected
            except Exception as e:
                logger.error(f"❌ Connection lost: {e}")
                logger.info("🔄 Attempting to reconnect in 30 seconds...")
                await asyncio.sleep(30)
                
                try:
                    # Attempt to reconnect
                    if self.client:
                        await self.client.disconnect()
                    
                    self.client = TelegramClient('relay_bot_session', self.api_id, self.api_hash)
                    await self.client.connect()
                    
                    if await self.client.is_user_authorized():
                        self._setup_message_handlers()
                        logger.info("Successfully reconnected to Telegram")
                    else:
                        logger.error("Authorization lost during reconnection")
                        break
                        
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
                    await asyncio.sleep(60)  # Wait longer before next attempt
