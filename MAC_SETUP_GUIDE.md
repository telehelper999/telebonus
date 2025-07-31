# Download and Run Telegram Bot on Mac

## Method 1: Download from Replit (Easiest)

### Step 1: Download Files from Replit
1. In your Replit project, go to the file explorer (left sidebar)
2. Select these essential files and download them:
   - `telegram_main.py`
   - `telegram_client.py`
   - `message_processor.py`
   - `filters.py` 
   - `text_replacer.py`
   - `config.py`
   - `logger.py`
   - `config.json`
   - `requirements.txt` (create this - see below)

### Step 2: Create Requirements File
Create a file called `requirements.txt` with this content:
```
telethon==1.29.3
python-dotenv==1.0.0
```

### Step 3: Set Up on Mac
Open Terminal on your Mac and run:

```bash
# Create project directory
mkdir telegram-bot
cd telegram-bot

# Create virtual environment
python3 -m venv bot_env
source bot_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
echo "TELEGRAM_API_ID=27516702" > .env
echo "TELEGRAM_API_HASH=35f1458c5be9672f428ecd63521bce5a" >> .env
echo "TELEGRAM_PHONE_NUMBER=+916283054835" >> .env
```

### Step 4: Run the Bot
```bash
python telegram_main.py
```

## Method 2: Git Clone (For Developers)

If you put your files on GitHub:
```bash
git clone https://github.com/your-username/telegram-bot.git
cd telegram-bot
python3 -m venv bot_env
source bot_env/bin/activate
pip install -r requirements.txt
python telegram_main.py
```

## Method 3: Direct File Transfer

### Download All Files Individually:
Right-click each file in Replit and select "Download":

**Core Bot Files:**
- `telegram_main.py` - Main bot entry point
- `telegram_client.py` - Telegram API client
- `message_processor.py` - Message processing logic
- `filters.py` - Message filtering system
- `text_replacer.py` - Text replacement engine
- `config.py` - Configuration management
- `logger.py` - Logging system
- `config.json` - Bot settings and configuration

**Create These Files on Mac:**

**requirements.txt:**
```
telethon==1.29.3
python-dotenv==1.0.0
```

**.env:**
```
TELEGRAM_API_ID=27516702
TELEGRAM_API_HASH=35f1458c5be9672f428ecd63521bce5a
TELEGRAM_PHONE_NUMBER=+916283054835
```

## Mac-Specific Setup Commands:

```bash
# Install Python if not already installed
brew install python3

# Create project directory
mkdir ~/telegram-bot
cd ~/telegram-bot

# Place all downloaded files here

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install telethon python-dotenv

# Make main file executable
chmod +x telegram_main.py

# Run the bot
python telegram_main.py
```

## Expected Behavior:

When you run the bot on Mac, you'll see:
1. Authentication with your Telegram account
2. Connection to all 4 source groups
3. Filtering messages for "Rain in India" only
4. Forwarding to Rain Alerts topic
5. Real-time message processing logs

## Troubleshooting:

**Python not found:**
```bash
# Install Python via Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
```

**Permission errors:**
```bash
chmod +x telegram_main.py
chmod +x *.py
```

**Module not found:**
```bash
pip install --upgrade pip
pip install telethon python-dotenv
```

## Running in Background on Mac:

To keep the bot running 24/7 on your Mac:

```bash
# Install screen
brew install screen

# Start bot in background session
screen -S telegram-bot
python telegram_main.py

# Detach: Press Ctrl+A then D
# Reattach later: screen -r telegram-bot
```

Your bot will work exactly the same on Mac as it does in Replit - filtering only "Rain in India" messages and forwarding them to the Rain Alerts topic!