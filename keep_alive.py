from flask import Flask
from threading import Thread
import time

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>Telegram Relay Bot - Status</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { color: #28a745; font-weight: bold; font-size: 18px; }
            .info { margin: 20px 0; padding: 15px; background: #e9ecef; border-radius: 5px; }
            .footer { margin-top: 30px; color: #6c757d; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Relay Bot</h1>
            <div class="status">✅ Bot is Running</div>
            
            <div class="info">
                <h3>Bot Status:</h3>
                <p><strong>Service:</strong> Active and monitoring groups</p>
                <p><strong>Groups:</strong> 2 source groups, 1 target group</p>
                <p><strong>Features:</strong> Message filtering, text replacement, media forwarding</p>
                <p><strong>Uptime:</strong> 24/7 monitoring enabled</p>
            </div>
            
            <div class="info">
                <h3>Text Replacement:</h3>
                <p><strong>Pattern:</strong> "Rain in India" messages</p>
                <p><strong>Replacement:</strong> 🍀 "💙 Rain 🌊Alerts 🇮🇳 💙 "🍀</p>
                <p><strong>Mode:</strong> First line only (preserves message structure)</p>
            </div>
            
            <div class="footer">
                <p>Last checked: ''' + str(time.strftime('%Y-%m-%d %H:%M:%S UTC')) + '''</p>
                <p>Use this URL for UptimeRobot monitoring</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram_relay_bot", "timestamp": time.time()}

@app.route('/ping')
def ping():
    return "pong"

def run():
    app.run(host='0.0.0.0', port=5000, debug=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

if __name__ == '__main__':
    keep_alive()
    print("Keep-alive server started on port 5000")
    while True:
        time.sleep(1)