
#!/usr/bin/env python3
"""
Authentication setup script - Run this locally first to create session file
"""

import asyncio
import os
import re
from telethon import TelegramClient

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def setup_auth():
    """Setup Telegram authentication locally."""
    print("🔐 Telegram Bot Authentication Setup")
    print("=" * 50)
    
    # Get credentials
    api_id_str = os.getenv('TELEGRAM_API_ID', input("Enter your API ID: "))
    api_hash = os.getenv('TELEGRAM_API_HASH', input("Enter your API Hash: "))
    phone_number = os.getenv('TELEGRAM_PHONE_NUMBER', input("Enter your phone number (with country code): "))
    
    # Parse API ID
    try:
        api_id_cleaned = api_id_str.strip().strip('"').strip("'")
        numbers = re.findall(r'\d+', api_id_cleaned)
        if numbers:
            api_id = int(numbers[-1])
        else:
            api_id = int(api_id_str)
    except ValueError:
        print("❌ Invalid API ID")
        return
    
    print(f"📱 Using phone: {phone_number}")
    print(f"🔑 Using API ID: {api_id}")
    
    # Create client
    client = TelegramClient('relay_bot_session', api_id, api_hash)
    
    try:
        print("\n🔄 Connecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print("📞 Sending authentication code...")
            await client.send_code_request(phone_number)
            
            code = input("Enter the code you received: ")
            await client.sign_in(phone_number, code)
            
        print("✅ Authentication successful!")
        print("📁 Session file 'relay_bot_session.session' created")
        print("\n📋 Next steps:")
        print("1. Upload the 'relay_bot_session.session' file to your Replit project")
        print("2. Restart your bot on Render")
        
        # Test connection
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_auth())
