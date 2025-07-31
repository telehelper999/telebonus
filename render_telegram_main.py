#!/usr/bin/env python3
"""
Render-optimized Telegram Relay Bot - Main Entry Point
Compatible with Python 3.11 and latest Telethon
"""

import asyncio
import logging
import os
import sys
from threading import Thread
from flask import Flask, jsonify, render_template_string
import time

# Configure logging for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Import bot modules
try:
    from config import Config
    from telegram_client import TelegramRelayClient
    from bot_logger import setup_logging  # Updated import here
except ImportError as e:
    logger.error(f"Failed to import bot modules: {e}")
    sys.exit(1)

# Flask app for health monitoring
app = Flask(__name__)

# Bot status tracking
bot_status = {
    'running': False,
    'start_time': time.time(),
    'messages_processed': 0,
    'errors': 0
}

@app.route('/')
def home():
    return '''
    <html>
    <head><title>Telegram Relay Bot - Status</title></head>
    <body>
        <h1>📊 Telegram Relay Bot Status</h1>
        <p>Status: {{ status }}</p>
        <p>Messages Processed: {{ messages_processed }}</p>
        <p>Errors: {{ errors }}</p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram_relay_bot", "timestamp": time.time()}

@app.route('/ping')
def ping():
    return "pong"

def run_flask_app():
    """Run the Flask app."""
    app.run(host='0.0.0.0', port=5000, debug=False)  # Using 0.0.0.0 for accessibility

def run_bot_thread():
    """Run bot in a separate thread."""
    try:
        asyncio.run(run_telegram_bot())  # Make sure you define this function
    except Exception as e:
        logger.error(f"Bot thread error: {e}")
        bot_status['running'] = False

async def run_telegram_bot():
    """Run the Telegram bot."""
    global bot_status
    
    try:
        logger.info("Starting Telegram bot...")
        bot_status['running'] = True
        
        # Load configuration
        config = Config()
        
        # Get environment variables
        api_id_str = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        phone_number = os.environ.get('TELEGRAM_PHONE_NUMBER')
        
        if not all([api_id_str, api_hash, phone_number]):
            raise ValueError("Missing required environment variables")
        
        # Convert API ID to integer
        import re
        numbers = re.findall(r'\d+', api_id_str.strip().strip('"').strip("'"))
        api_id = int(numbers[-1]) if numbers else int(api_id_str)
        
        logger.info(f"Initializing Telegram client with API ID: {api_id}")
        
        # Initialize client
        client = TelegramRelayClient(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            config=config
        )
        
        # Start the client
        await client.start()
        logger.info("Telegram bot started successfully")
        
        # Keep running
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_status['errors'] += 1
        bot_status['running'] = False

def main():
    """Main function for Render deployment."""
    # Setup logging
    setup_logging()
    logger.info("Starting Telegram Relay Bot on Render...")

    # Start bot in background thread
    bot_thread = Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    logger.info("Bot thread started")

    # Start Flask app
    logger.info("Starting Flask app on port 5000")
    run_flask_app()

if __name__ == '__main__':
    main()
