"""
Text replacement functionality for message processing
"""

import logging
import re
import unicodedata
from typing import Dict, List, Tuple
from config import Config

logger = logging.getLogger(__name__)

class TextReplacer:
    """Handles text replacement operations on messages."""
    
    def __init__(self, config: Config):
        """Initialize text replacer with configuration."""
        self.config = config
        self._compiled_replacements = []
        self._update_replacements()
    
    def _update_replacements(self):
        """Update compiled replacement patterns from configuration."""
        self._compiled_replacements = []
        replacements = self.config.text_replacements
        
        if not replacements:
            return
        
        for old_text, new_text in replacements.items():
            try:
                # Check if the text contains emojis or special characters
                if any(ord(char) > 127 for char in old_text):
                    # For emoji/unicode text, use simple string replacement
                    self._compiled_replacements.append((None, new_text, old_text))
                    logger.debug(f"Simple replacement pattern (emoji): '{old_text}' -> '{new_text}'")
                else:
                    # For regular text, use word boundary pattern
                    escaped_old = re.escape(old_text)
                    pattern = rf'\b{escaped_old}\b'
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    self._compiled_replacements.append((compiled_pattern, new_text, old_text))
                    logger.debug(f"Compiled replacement pattern: '{old_text}' -> '{new_text}'")
            except re.error as e:
                logger.warning(f"Invalid regex pattern for replacement '{old_text}': {e}")
    
    def _remove_emojis(self, text: str) -> str:
        """Remove all emojis and special characters from text while preserving newlines and structure."""
        # Split into lines to preserve structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ""
            for char in line:
                # Keep basic ASCII characters, spaces, and common punctuation
                if (32 <= ord(char) <= 126) or char in ' \t':
                    cleaned_line += char
                # Keep some specific Unicode characters but skip emojis
                elif unicodedata.category(char)[0] not in ('So', 'Sk'):  # Skip symbols and modifier symbols
                    # Skip known emoji ranges
                    char_code = ord(char)
                    if not (0x1F600 <= char_code <= 0x1F64F or  # Emoticons
                           0x1F300 <= char_code <= 0x1F5FF or   # Misc Symbols
                           0x1F680 <= char_code <= 0x1F6FF or   # Transport
                           0x2600 <= char_code <= 0x26FF or     # Misc symbols
                           0x2700 <= char_code <= 0x27BF):      # Dingbats
                        cleaned_line += char
            cleaned_lines.append(cleaned_line.strip())
        
        # Join lines back together, preserving empty lines
        return '\n'.join(cleaned_lines)

    def replace_text(self, text: str) -> str:
        """
        Apply all text replacements to the given text.
        
        Args:
            text: Original text to process
            
        Returns:
            Text with all replacements applied
        """
        if not text:
            return text
        
        if not self.config.enable_text_processing:
            return text
        
        # Refresh replacements if config changed
        current_replacements = self.config.text_replacements
        if self._needs_replacement_update(current_replacements):
            self._update_replacements()
        
        processed_text = text
        replacements_made = []
        
        # Debug: Log the incoming text
        logger.info(f"Processing text for replacements: {repr(text)}")
        
        # First, remove all emojis from the original text
        clean_text = self._remove_emojis(text)
        logger.info(f"Clean text (no emojis): {repr(clean_text)}")
        
        # Start with the clean text (emojis already removed)
        processed_text = clean_text
        
        # Split text into lines to process line by line
        lines = processed_text.split('\n')
        
        # Apply all replacement patterns on clean text
        for pattern, new_text, original_old_text in self._compiled_replacements:
            # Remove emojis from the pattern to match against clean text
            clean_pattern = self._remove_emojis(original_old_text)
            logger.info(f"Looking for clean pattern: {repr(clean_pattern)} in clean text")
            
            # Check each line for the pattern and replace only the matching part
            for i, line in enumerate(lines):
                if clean_pattern in line:
                    # Replace only the matching pattern in the line, keep the rest
                    lines[i] = line.replace(clean_pattern, new_text)
                    replacements_made.append((original_old_text, new_text))
                    logger.info(f"Applied replacement on line {i}: '{clean_pattern}' -> '{new_text}'")
                    logger.info(f"Line after replacement: '{lines[i]}'")
                    break  # Only replace the first matching line
            
            if replacements_made:
                break  # Only apply first matching replacement pattern
        
        # Rejoin the lines
        processed_text = '\n'.join(lines)
        logger.info(f"Final processed text: {repr(processed_text)}")
        
        if replacements_made:
            logger.info(f"Text processing complete. {len(replacements_made)} replacements made.")
        
        return processed_text
    
    def _needs_replacement_update(self, current_replacements: Dict[str, str]) -> bool:
        """Check if replacement patterns need to be updated."""
        if not self._compiled_replacements:
            return bool(current_replacements)
        
        # Simple check - if number of replacements doesn't match, update needed
        return len(self._compiled_replacements) != len(current_replacements)
    
    def add_replacement(self, old_text: str, new_text: str) -> bool:
        """
        Add a new text replacement rule.
        
        Args:
            old_text: Text to replace
            new_text: Replacement text
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            if self.config.add_text_replacement(old_text, new_text):
                self._update_replacements()
                logger.info(f"Added text replacement: '{old_text}' -> '{new_text}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding text replacement '{old_text}' -> '{new_text}': {e}")
            return False
    
    def remove_replacement(self, old_text: str) -> bool:
        """
        Remove a text replacement rule.
        
        Args:
            old_text: Old text pattern to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            replacements = self.config.text_replacements
            if old_text in replacements:
                del replacements[old_text]
                self.config.save_config()
                self._update_replacements()
                logger.info(f"Removed text replacement: '{old_text}'")
                return True
            else:
                logger.warning(f"Text replacement not found: '{old_text}'")
                return False
        except Exception as e:
            logger.error(f"Error removing text replacement '{old_text}': {e}")
            return False
    
    def get_active_replacements(self) -> Dict[str, str]:
        """Get dictionary of currently active text replacements."""
        return self.config.text_replacements.copy()
    
    def test_replacement(self, text: str) -> Dict:
        """
        Test text replacement on given text and return detailed results.
        
        Args:
            text: Text to test replacements on
            
        Returns:
            Dictionary with test results
        """
        result = {
            'original_text': text,
            'processed_text': text,
            'replacements_made': [],
            'processing_enabled': self.config.enable_text_processing,
            'total_rules': len(self.config.text_replacements)
        }
        
        if not self.config.enable_text_processing:
            result['reason'] = 'Text processing disabled'
            return result
        
        if not self.config.text_replacements:
            result['reason'] = 'No replacement rules configured'
            return result
        
        if not text:
            result['reason'] = 'No text to process'
            return result
        
        # Apply replacements and track changes
        processed_text = text
        for pattern, new_text, original_old_text in self._compiled_replacements:
            before = processed_text
            after = pattern.sub(new_text, processed_text)
            
            if before != after:
                # Count occurrences
                matches = len(pattern.findall(before))
                result['replacements_made'].append({
                    'old_text': original_old_text,
                    'new_text': new_text,
                    'occurrences': matches,
                    'before': before,
                    'after': after
                })
                processed_text = after
        
        result['processed_text'] = processed_text
        result['total_replacements'] = len(result['replacements_made'])
        result['text_changed'] = result['original_text'] != result['processed_text']
        
        return result
    
    def preview_replacement(self, old_text: str, new_text: str, sample_text: str) -> Dict:
        """
        Preview what a replacement rule would do to sample text.
        
        Args:
            old_text: Text to replace
            new_text: Replacement text
            sample_text: Sample text to test on
            
        Returns:
            Dictionary with preview results
        """
        try:
            # Create temporary pattern
            escaped_old = re.escape(old_text)
            pattern = rf'\b{escaped_old}\b'
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            # Test replacement
            result_text = compiled_pattern.sub(new_text, sample_text)
            matches = len(compiled_pattern.findall(sample_text))
            
            return {
                'original_text': sample_text,
                'result_text': result_text,
                'old_text': old_text,
                'new_text': new_text,
                'matches_found': matches,
                'text_changed': sample_text != result_text,
                'valid_pattern': True
            }
        
        except re.error as e:
            return {
                'original_text': sample_text,
                'result_text': sample_text,
                'old_text': old_text,
                'new_text': new_text,
                'matches_found': 0,
                'text_changed': False,
                'valid_pattern': False,
                'error': str(e)
            }
