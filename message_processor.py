"""
Message processing pipeline for filtering and text replacement
"""

import logging
import re
from typing import Optional, Dict, List
from telethon.types import Message

from config import Config
from filters import MessageFilter
from text_replacer import TextReplacer

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Processes messages for filtering and text replacement."""
    
    def __init__(self, config: Config):
        """Initialize message processor with configuration."""
        self.config = config
        self.filter = MessageFilter(config)
        self.text_replacer = TextReplacer(config)
        # Counter for group-specific message tracking
        self.group_message_counters = {}
        
    async def process_message(self, message: Message, source_group_id: int) -> Optional[str]:
        """
        Process a message through the filtering and text replacement pipeline.
        
        Args:
            message: Telegram message object
            source_group_id: ID of the source group
            
        Returns:
            Processed message text if it passes filters, None otherwise
        """
        try:
            # Extract message text
            message_text = self._extract_message_text(message)
            
            if not message_text:
                logger.debug(f"No text content in message from group {source_group_id}")
                return None
            
            # Since filters are disabled, all messages pass through
            logger.info(f"Message PASSED (filters disabled) from group {source_group_id}: {message_text[:50]}...")
            
            # Apply text replacements if enabled, but preserve emojis in final output
            if self.config.enable_text_processing:
                processed_text = self._apply_text_replacements_preserve_emojis(message_text, source_group_id)
                logger.debug(f"Text processed: '{message_text[:50]}...' -> '{processed_text[:50]}...'")
                return processed_text
            else:
                return message_text
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.exception("Full traceback:")
            return None
    
    def _apply_text_replacements(self, text: str, source_group_id: int) -> str:
        """Apply group-specific or global text replacements."""
        # Check for group-specific replacements first
        if hasattr(self.config, 'group_specific_replacements'):
            group_replacements = self.config.group_specific_replacements.get(str(source_group_id))
            if group_replacements:
                return self._apply_specific_replacements(text, group_replacements)
        
        # Fall back to global replacements
        return self.text_replacer.replace_text(text)
    
    def _apply_text_replacements_preserve_emojis(self, text: str, source_group_id: int) -> str:
        """Apply text replacements while preserving emojis in original text."""
        # Check for group-specific replacements first
        if hasattr(self.config, 'group_specific_replacements'):
            group_replacements = self.config.group_specific_replacements.get(str(source_group_id))
            if group_replacements:
                # Apply replacements by finding clean text matches in original text
                for old_text, new_text in group_replacements.items():
                    clean_pattern = self._remove_emojis(old_text)
                    clean_text = self._remove_emojis(text)
                    if clean_pattern in clean_text:
                        logger.info(f"Group-specific replacement applied: '{old_text}' -> '{new_text}'")
                        # Replace the clean pattern in the clean text, then return the result
                        result_text = clean_text.replace(clean_pattern, new_text)
                        return result_text
                return text  # Return original text with emojis if no replacement matched
        
        # Fall back to global replacements with emoji preservation
        clean_text = self._remove_emojis(text)
        for old_text, new_text in self.config.text_replacements.items():
            clean_pattern = self._remove_emojis(old_text)
            if clean_pattern in clean_text:
                logger.info(f"Global replacement applied: '{old_text}' -> '{new_text}'")
                # Replace the clean pattern in the clean text, then return the result
                result_text = clean_text.replace(clean_pattern, new_text)
                return result_text
        
        return text  # Return original text with emojis if no replacements
    
    def _apply_specific_replacements(self, text: str, replacements: Dict[str, str]) -> str:
        """Apply specific text replacements with emoji removal."""
        if not text or not replacements:
            return text
        
        # Remove emojis first (same logic as TextReplacer)
        cleaned_text = self._remove_emojis(text)
        logger.info(f"Group-specific processing: Clean text (no emojis): {repr(cleaned_text)}")
        
        # Apply replacements
        processed_text = cleaned_text
        for old_text, new_text in replacements.items():
            clean_pattern = self._remove_emojis(old_text)
            if clean_pattern in processed_text:
                processed_text = processed_text.replace(clean_pattern, new_text)
                logger.info(f"Group-specific replacement applied: '{old_text}' -> '{new_text}'")
                break
        
        return processed_text
    
    def _remove_emojis(self, text: str) -> str:
        """Remove all emojis and special characters from text while preserving newlines."""
        import unicodedata
        cleaned = ""
        for char in text:
            # Always keep newlines, spaces, and basic ASCII characters
            if char in '\n\r\t ' or (32 <= ord(char) <= 126):
                cleaned += char
            # Keep some common symbols but skip emojis
            elif unicodedata.category(char)[0] not in ('S', 'C'):  # Skip symbols and control chars
                if ord(char) < 0x1F600 or ord(char) > 0x1F64F:  # Skip emoji ranges
                    if ord(char) < 0x1F300 or ord(char) > 0x1F5FF:
                        if ord(char) < 0x1F680 or ord(char) > 0x1F6FF:
                            if ord(char) < 0x2600 or ord(char) > 0x26FF:
                                cleaned += char
        return cleaned.strip()
    
    def _extract_message_text(self, message: Message) -> str:
        """Extract text content from a message."""
        text_parts = []
        
        # Main message text
        if hasattr(message, 'text') and getattr(message, 'text', None):
            text_parts.append(getattr(message, 'text'))
        
        # Caption for media messages  
        if hasattr(message, 'media') and getattr(message, 'media', None):
            caption = getattr(message, 'caption', None)
            if caption:
                text_parts.append(caption)
        
        return " ".join(text_parts).strip()
    
    def _has_media(self, message: Message) -> bool:
        """Check if message contains media content."""
        return hasattr(message, 'media') and message.media is not None
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        stats = {
            "total_processed": getattr(self, '_total_processed', 0),
            "filtered_out": getattr(self, '_filtered_out', 0),
            "text_replaced": getattr(self, '_text_replaced', 0),
            "media_forwarded": getattr(self, '_media_forwarded', 0)
        }
        # Add group message counters
        for group_id, count in self.group_message_counters.items():
            stats[f"group_{group_id}_matching_count"] = count
        return stats
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._total_processed = 0
        self._filtered_out = 0
        self._text_replaced = 0
        self._media_forwarded = 0
        # Reset group message counters
        self.group_message_counters = {}
