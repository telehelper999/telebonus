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
from logger import setup_logging
from keep_alive import keep_alive

# Load environment variables from .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set directly
    pass

async def main():
    """Main function to run the Telegram relay bot."""
    # Setup logging with DEBUG level
    setup_logging(level=logging.DEBUG)  # Changed to set DEBUG level
    logger = logging.getLogger(__name__)
    logger.debug("Debug logging enabled")  # Test debug message
    
    # Start the keep-alive server for 24/7 uptime monitoring
    keep_alive()
    logger.info("Keep-alive server started for 24/7 monitoring")
    
    try:
        # Load configuration
        config = Config()
        logger.debug("Configuration loaded successfully")
        
        # Validate required environment variables
        api_id_str = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
        
        logger.debug(f"Environment variables loaded: API_ID={bool(api_id_str)}, API_HASH={bool(api_hash)}, PHONE={bool(phone_number)}")
        
        if not all([api_id_str, api_hash, phone_number]):
            logger.error("Missing required environment variables.")
            logger.error("Required: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER")
            logger.error("Make sure these are set in your Render environment variables.")
            return
        
        # Type assertions - we know these are not None because of the check above
        assert api_id_str is not None
        assert api_hash is not None  
        assert phone_number is not None
        
        # Convert API ID to integer
        try:
            # Strip whitespace and quotes if present, then extract just the numeric part
            api_id_cleaned = api_id_str.strip().strip('"').strip("'")
            # Extract number from strings like "> T1STAR: 27516702" 
            numbers = re.findall(r'\d+', api_id_cleaned)
            if numbers:
                api_id = int(numbers[-1])  # Use the last/longest number found
                logger.debug(f"Extracted API ID: {api_id} from input: {api_id_str}")
            else:
                raise ValueError("No numeric value found")
        except (ValueError, IndexError) as e:
            logger.error(f"TELEGRAM_API_ID must be a valid integer. Received: '{api_id_str}'")
            logger.error("Make sure it's just the numeric ID without quotes or extra text")
            logger.debug(f"Conversion error: {str(e)}")
            return
        
        # Initialize Telegram client
        logger.debug("Initializing Telegram client...")
        client = TelegramRelayClient(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            config=config
        )
        
        logger.info("Starting Telegram Relay Bot...")
        
        # Start the client
        await client.start()
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        logger.debug("Entering main event loop...")
        
        # Call the run until disconnected method
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
