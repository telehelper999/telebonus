"""
Message filtering functionality
"""

import logging
import re
from typing import List, Set, Optional
from config import Config

logger = logging.getLogger(__name__)

class MessageFilter:
    """Handles message filtering based on keywords and other criteria."""

    def __init__(self, config: Config):
        """Initialize message filter with configuration."""
        self.config = config
        self._compiled_patterns = None
        logger.debug("Initializing MessageFilter with config")
        self._update_patterns()

    def _update_patterns(self):
        """Update compiled regex patterns from configuration."""
        keywords = self.config.keywords
        if not keywords:
            self._compiled_patterns = []
            logger.debug("No keywords configured - empty pattern list")
            return

        flags = 0 if self.config.case_sensitive_filters else re.IGNORECASE
        self._compiled_patterns = []

        logger.debug(f"Compiling patterns for {len(keywords)} keywords (case_sensitive={not bool(flags)})")
        for keyword in keywords:
            try:
                escaped_keyword = re.escape(keyword)
                pattern = rf'\b{escaped_keyword}\b'
                compiled_pattern = re.compile(pattern, flags)
                self._compiled_patterns.append(compiled_pattern)
                logger.debug(f"Compiled filter pattern: {pattern}")
            except re.error as e:
                logger.warning(f"Invalid regex pattern for keyword '{keyword}': {e}")

    def passes_keyword_filter(self, text: str, source_group_id: Optional[int] = None) -> bool:
        """
        Check if message text passes keyword filter.

        Args:
            text: Message text to check
            source_group_id: ID of the source group for group-specific filtering

        Returns:
            True if message should be forwarded, False if filtered out
        """
        logger.debug(f"Starting filter check for message from group {source_group_id}: {text[:100]}{'...' if len(text) > 100 else ''}")

        # Check group-specific filtering first
        if source_group_id and hasattr(self.config, 'group_specific_filters'):
            group_filters = self.config.group_specific_filters.get(str(source_group_id))
            if group_filters and group_filters.get('enabled', False):
                logger.debug(f"Found group-specific filters for {source_group_id}")
                keywords = group_filters.get('keywords', [])
                if keywords:
                    logger.debug(f"Checking against group-specific keywords: {keywords}")
                    # Clean text for emoji-aware filtering
                    clean_text = self._remove_emojis(text)
                    logger.debug(f"Original text: {text}")
                    logger.debug(f"Clean text for filtering: {clean_text}")
                    result = self._check_keywords_in_text(clean_text, keywords)
                    logger.debug(f"Group-specific filter result for {source_group_id}: {'PASS' if result else 'BLOCK'}")
                    return result
                else:
                    logger.debug(f"Group {source_group_id} has empty keyword list - blocking all messages")
                    return False

        # Check global filtering if no group-specific filtering applies
        if not self.config.filters_enabled:
            logger.debug("Global filtering disabled - allowing message")
            return True

        if not self.config.keywords:
            logger.debug("No global keywords configured - allowing message")
            return True

        if not text:
            logger.debug("Empty message text - blocking message")
            return False

        # Refresh patterns if config changed
        current_keywords = set(self.config.keywords) if self.config.keywords else set()
        if self._needs_pattern_update(current_keywords):
            logger.debug("Keyword configuration changed - updating patterns")
            self._update_patterns()

        # Check if any keyword pattern matches
        if self._compiled_patterns:
            logger.debug(f"Checking against {len(self._compiled_patterns)} global patterns")
            for pattern in self._compiled_patterns:
                if pattern.search(text):
                    logger.debug(f"Message PASSED filter with pattern: {pattern.pattern}")
                    return True

        logger.debug("Message BLOCKED - no matching keywords found in global filters")
        return False

    def _check_keywords_in_text(self, text: str, keywords: List[str]) -> bool:
        """Check if any keywords are found in text."""
        logger.debug(f"Checking text against {len(keywords)} keywords")
        if not keywords or not text:
            logger.debug("Empty keywords or text - automatic block")
            return False

        flags = 0 if self.config.case_sensitive_filters else re.IGNORECASE
        for keyword in keywords:
            try:
                # For phrases like "Rain in India", use simple substring search
                if ' ' in keyword:
                    logger.debug(f"Checking phrase: {keyword}")
                    if flags & re.IGNORECASE:
                        if keyword.lower() in text.lower():
                            logger.debug(f"Found phrase match (case-insensitive): {keyword}")
                            return True
                    else:
                        if keyword in text:
                            logger.debug(f"Found phrase match (case-sensitive): {keyword}")
                            return True
                else:
                    logger.debug(f"Checking word: {keyword}")
                    escaped_keyword = re.escape(keyword)
                    pattern = rf'\b{escaped_keyword}\b'
                    if re.search(pattern, text, flags):
                        logger.debug(f"Found word match: {keyword}")
                        return True
            except re.error as e:
                logger.warning(f"Invalid regex pattern for keyword '{keyword}': {e}")
        logger.debug("No keyword matches found in text")
        return False

    def _needs_pattern_update(self, current_keywords: Set[str]) -> bool:
        """Check if patterns need to be updated based on config changes."""
        if not self._compiled_patterns:
            logger.debug("No existing patterns - update needed")
            return bool(current_keywords)

        # Simple check - if number of patterns doesn't match keywords, update needed
        needs_update = len(self._compiled_patterns) != len(current_keywords)
        if needs_update:
            logger.debug(f"Pattern count mismatch ({len(self._compiled_patterns)} vs {len(current_keywords)}) - update needed")
        return needs_update

    def add_keyword_filter(self, keyword: str) -> bool:
        """
        Add a new keyword filter.

        Args:
            keyword: Keyword to add to filters

        Returns:
            True if successfully added, False otherwise
        """
        try:
            logger.info(f"Attempting to add keyword filter: {keyword}")
            if self.config.add_keyword(keyword):
                self._update_patterns()
                logger.info(f"Successfully added keyword filter: {keyword}")
                return True
            logger.warning(f"Keyword already exists: {keyword}")
            return False
        except Exception as e:
            logger.error(f"Error adding keyword filter '{keyword}': {e}")
            return False

    def remove_keyword_filter(self, keyword: str) -> bool:
        """
        Remove a keyword filter.

        Args:
            keyword: Keyword to remove from filters

        Returns:
            True if successfully removed, False otherwise
        """
        try:
            logger.info(f"Attempting to remove keyword filter: {keyword}")
            keywords = self.config.keywords
            if keyword in keywords:
                keywords.remove(keyword)
                self.config.save_config()
                self._update_patterns()
                logger.info(f"Successfully removed keyword filter: {keyword}")
                return True
            logger.warning(f"Keyword filter not found: {keyword}")
            return False
        except Exception as e:
            logger.error(f"Error removing keyword filter '{keyword}': {e}")
            return False

    def get_active_filters(self) -> List[str]:
        """Get list of currently active keyword filters."""
        logger.debug("Retrieving active filters")
        return self.config.keywords.copy()

    def test_filter(self, text: str) -> dict:
        """
        Test text against current filters and return detailed results.

        Args:
            text: Text to test

        Returns:
            Dictionary with test results
        """
        logger.debug(f"Running filter test on text: {text[:100]}{'...' if len(text) > 100 else ''}")
        result = {
            'passes_filter': False,
            'matching_keywords': [],
            'filter_enabled': self.config.filters_enabled,
            'keywords_configured': len(self.config.keywords),
            'case_sensitive': self.config.case_sensitive_filters
        }

        if not self.config.filters_enabled:
            result['passes_filter'] = True
            result['reason'] = 'Filtering disabled'
            logger.debug("Filter test result: PASS (filtering disabled)")
            return result

        if not self.config.keywords:
            result['passes_filter'] = True
            result['reason'] = 'No keywords configured'
            logger.debug("Filter test result: PASS (no keywords configured)")
            return result

        if not text:
            result['reason'] = 'No text to filter'
            logger.debug("Filter test result: BLOCK (no text)")
            return result

        # Check each pattern
        logger.debug(f"Testing against {len(self._compiled_patterns or [])} patterns")
        for i, pattern in enumerate(self._compiled_patterns or []):
            if pattern.search(text) and self.config.keywords:
                matched_keyword = self.config.keywords[i]
                result['matching_keywords'].append(matched_keyword)
                logger.debug(f"Found pattern match: {matched_keyword}")

        result['passes_filter'] = len(result['matching_keywords']) > 0
        result['reason'] = 'Match found' if result['passes_filter'] else 'No matches found'

        logger.debug(f"Filter test result: {'PASS' if result['passes_filter'] else 'BLOCK'} ({result['reason']})")
        return result

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
