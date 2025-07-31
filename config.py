"""
Configuration management for Telegram Relay Bot
"""

import json
import logging
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the Telegram relay bot."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration from file."""
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
                return config
            else:
                logger.warning(f"Config file {self.config_file} not found, using default configuration")
                return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "source_groups": [],
            "target_groups": [],
            "filters": {
                "keywords": [],
                "enabled": True,
                "case_sensitive": False
            },
            "text_replacements": {},
            "settings": {
                "forward_delay": 1,
                "max_retries": 3,
                "enable_media_forwarding": True,
                "enable_text_processing": True
            }
        }
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    @property
    def source_groups(self) -> List[int]:
        """Get list of source group IDs to monitor."""
        return self.config.get("source_groups", [])
    
    @property
    def target_groups(self) -> List[int]:
        """Get list of target group IDs to forward messages to."""
        return self.config.get("target_groups", [])
    
    @property
    def keywords(self) -> List[str]:
        """Get list of keywords to filter messages."""
        return self.config.get("filters", {}).get("keywords", [])
    
    @property
    def filters_enabled(self) -> bool:
        """Check if keyword filtering is enabled."""
        return self.config.get("filters", {}).get("enabled", True)
    
    @property
    def case_sensitive_filters(self) -> bool:
        """Check if keyword filtering is case sensitive."""
        return self.config.get("filters", {}).get("case_sensitive", False)
    
    @property
    def text_replacements(self) -> Dict[str, str]:
        """Get text replacement rules."""
        return self.config.get("text_replacements", {})
    
    @property
    def forward_delay(self) -> float:
        """Get delay between forwarding messages (in seconds)."""
        return self.config.get("settings", {}).get("forward_delay", 1)
    
    @property
    def max_retries(self) -> int:
        """Get maximum number of retries for failed operations."""
        return self.config.get("settings", {}).get("max_retries", 3)
    
    @property
    def enable_media_forwarding(self) -> bool:
        """Check if media forwarding is enabled."""
        return self.config.get("settings", {}).get("enable_media_forwarding", True)
    
    @property
    def enable_text_processing(self) -> bool:
        """Check if text processing is enabled."""
        return self.config.get("settings", {}).get("enable_text_processing", True)
    
    @property
    def group_specific_filters(self) -> Dict[str, Any]:
        """Get group-specific filter configurations."""
        return self.config.get("filters", {}).get("group_specific", {})
    
    @property
    def group_specific_replacements(self) -> Dict[str, Dict[str, str]]:
        """Get group-specific text replacements."""
        return self.config.get("group_specific_replacements", {})
    
    def add_keyword(self, keyword: str) -> bool:
        """Add a keyword to the filter list."""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            self.save_config()
            return True
        return False
    
    @property
    def target_topics(self) -> Dict[str, Dict[str, Any]]:
        """Get target topics configuration for forum groups."""
        return self.config.get("target_topics", {})
    
    def add_source_group(self, group_id: int) -> bool:
        """Add a source group ID."""
        if group_id not in self.source_groups:
            self.config.setdefault("source_groups", []).append(group_id)
            return self.save_config()
        return True
    
    def add_target_group(self, group_id: int) -> bool:
        """Add a target group ID."""
        if group_id not in self.target_groups:
            self.config.setdefault("target_groups", []).append(group_id)
            return self.save_config()
        return True
    
    def add_keyword(self, keyword: str) -> bool:
        """Add a keyword filter."""
        if keyword not in self.keywords:
            self.config.setdefault("filters", {}).setdefault("keywords", []).append(keyword)
            return self.save_config()
        return True
    
    def add_text_replacement(self, old_text: str, new_text: str) -> bool:
        """Add a text replacement rule."""
        self.config.setdefault("text_replacements", {})[old_text] = new_text
        return self.save_config()
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.source_groups:
            errors.append("No source groups configured")
        
        if not self.target_groups:
            errors.append("No target groups configured")
        
        if self.filters_enabled and not self.keywords and not self.group_specific_filters:
            errors.append("Keyword filtering is enabled but no keywords configured")
        
        if self.forward_delay < 0:
            errors.append("Forward delay cannot be negative")
        
        if self.max_retries < 1:
            errors.append("Max retries must be at least 1")
        
        return errors
