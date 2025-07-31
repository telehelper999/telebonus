
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
try:
    from flask import Flask, jsonify
except ImportError:
    logger.warning("Flask not available - using simple HTTP server for health checks")
    Flask = None
    jsonify = None
import time
import re

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
except ImportError as e:
    logger.error(f"Failed to import bot modules: {e}")
    sys.exit(1)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Flask app for health monitoring
if Flask:
    app = Flask(__name__)
else:
    app = None

# Bot status tracking
bot_status = {
    'running': False,
    'start_time': time.time(),
    'messages_processed': 0,
    'errors': 0
}

@app.route('/')
def home():
    status_emoji = '🟢 Running' if bot_status['running'] else '🔴 Stopped'
    uptime = int(time.time() - bot_status['start_time'])
    
    return f'''
    <html>
    <head>
        <title>Telegram Relay Bot - Render Deployment</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ font-size: 18px; margin: 10px 0; }}
            .metric {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Telegram Relay Bot - Render Deployment</h1>
            <div class="status">Status: {status_emoji}</div>
            <div class="metric">Messages Processed: {bot_status['messages_processed']}</div>
            <div class="metric">Errors: {bot_status['errors']}</div>
            <div class="metric">Uptime: {uptime} seconds</div>
            <div class="metric">Platform: Render Web Service</div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {
        "status": "healthy", 
        "service": "telegram_relay_bot", 
        "platform": "render",
        "timestamp": time.time(),
        "uptime": int(time.time() - bot_status['start_time'])
    }

@app.route('/ping')
def ping():
    return "pong"

def run_bot_thread():
    """Run bot in a separate thread."""
    try:
        asyncio.run(run_telegram_bot())
    except Exception as e:
        logger.error(f"Bot thread error: {e}")
        bot_status['running'] = False
        bot_status['errors'] += 1

async def run_telegram_bot():
    """Run the Telegram bot."""
    global bot_status
    
    try:
        logger.info("Starting Telegram bot on Render...")
        bot_status['running'] = True
        
        # Load configuration
        config = Config()
        
        # Get environment variables
        api_id_str = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        phone_number = os.environ.get('TELEGRAM_PHONE_NUMBER')
        
        if not all([api_id_str, api_hash, phone_number]):
            logger.error("Missing required environment variables")
            logger.error("Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_PHONE_NUMBER in Render environment")
            raise ValueError("Missing required environment variables")
        
        # Convert API ID to integer
        try:
            api_id_cleaned = api_id_str.strip().strip('"').strip("'")
            numbers = re.findall(r'\d+', api_id_cleaned)
            if numbers:
                api_id = int(numbers[-1])
                logger.debug(f"Extracted API ID: {api_id}")
            else:
                raise ValueError("No numeric value found")
        except (ValueError, IndexError) as e:
            logger.error(f"TELEGRAM_API_ID must be a valid integer: {e}")
            bot_status['errors'] += 1
            return
        
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
        logger.info("Telegram bot started successfully on Render")
        
        # Keep running
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_status['errors'] += 1
        bot_status['running'] = False
    finally:
        bot_status['running'] = False
        logger.info("Bot shutdown complete")

def main():
    """Main function for Render deployment."""
    logger.info("Starting Telegram Relay Bot on Render Web Service...")

    # Get the port from environment (Render sets this automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Start bot in background thread
    bot_thread = Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    logger.info("Bot thread started")

    # Start Flask app for Render
    if app:
        logger.info(f"Starting Flask app on port {port} for Render")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.warning("Flask not available - running bot without web interface")
        # Keep the main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")

if __name__ == '__main__':
    main()
