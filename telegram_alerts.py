import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env
# dload_dotenv = load_dotenv()

load_dotenv()

def send_telegram_message(text: str):
    """
    Send a message via Telegram bot using credentials from environment variables.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram bot token or chat ID not set. Skipping sending message.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        if response.ok:
            print(f"Telegram message sent: {response.status_code}")
        else:
            print(f"Failed to send Telegram message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}") 