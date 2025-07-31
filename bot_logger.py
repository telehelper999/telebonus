#!/usr/bin/env python3
"""
Telegram Relay Bot - Main Entry Point
A multi-group Telegram relay bot with automatic text editing, keyword filtering, and message forwarding capabilities.
"""

import asyncio
import logging
import os
import sys
import re

from config import Config
from telegram_client import TelegramRelayClient
import logging

def setup_logging(log_level='INFO'):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def get_logger(name):
    """Get a logger with the given name."""
    return logging.getLogger(name)
from keep_alive import keep_alive

# Load environment variables from .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def main():
    """Main function to run the Telegram relay bot."""
    # Setup logging with DEBUG level from environment or default to INFO
    log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()  # Default to DEBUG for now
    logger = setup_logging(log_level=log_level)
    
    # Start the keep-alive server for 24/7 uptime monitoring
    keep_alive()
    logger.info("Keep-alive server started for 24/7 monitoring")
    
    try:
        # Load configuration
        config = Config()
        logger.debug("Configuration loaded successfully")
        
        # Validate required environment variables with debug logging
        api_id_str = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
        
        logger.debug(f"Environment variables - API_ID: {'set' if api_id_str else 'not set'}")
        logger.debug(f"Environment variables - API_HASH: {'set' if api_hash else 'not set'}")
        logger.debug(f"Environment variables - PHONE: {'set' if phone_number else 'not set'}")
        
        if not all([api_id_str, api_hash, phone_number]):
            logger.error("Missing required environment variables")
            return
        
        # Convert API ID to integer with detailed debug logging
        try:
            api_id_cleaned = api_id_str.strip().strip('"').strip("'")
            numbers = re.findall(r'\d+', api_id_cleaned)
            if numbers:
                api_id = int(numbers[-1])
                logger.debug(f"Successfully parsed API ID: {api_id} from input: {api_id_str}")
            else:
                raise ValueError("No numeric value found")
        except (ValueError, IndexError) as e:
            logger.error(f"API ID conversion failed: {str(e)}")
            logger.debug(f"Original API ID string: {api_id_str}")
            return
        
        # Initialize Telegram client with debug logging
        logger.debug("Initializing Telegram client...")
        client = TelegramRelayClient(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            config=config
        )
        
        logger.info("Starting Telegram Relay Bot...")
        
        # Start the client with debug logging
        if not await client.start():
            logger.error("Failed to start Telegram client")
            return
        
        logger.info("Bot is running. Press Ctrl+C to stop")
        logger.debug("Entering main event loop...")
        
        # Run until disconnected
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")
    finally:
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
