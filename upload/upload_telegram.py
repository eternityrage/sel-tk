"""
Upload video to Telegram channel - SelTok Lens
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_telegram(video_path, caption):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_id = os.getenv('TELEGRAM_CHANNEL_ID') or os.getenv('TELEGRAM_CHAT_ID')

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else ("PLACEHOLDER (***)" if s == "***" else "MISSING")
    print(f"[telegram] Bot Token: {mask(bot_token)}")
    print(f"[telegram] Channel ID: {channel_id}")

    if not bot_token or bot_token == "***":
        print("Telegram Bot token is missing or a placeholder. Skipping Telegram upload.")
        return {'status': 'skipped', 'reason': 'missing_credentials'}
    if not channel_id or channel_id == "***":
        print("Telegram Channel ID is missing or a placeholder. Skipping Telegram upload.")
        return {'status': 'skipped', 'reason': 'missing_credentials'}

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

    with open(video_path, 'rb') as video_file:
        files = {
            'video': video_file
        }

        data = {
            'chat_id': channel_id,
            'caption': caption,
            'parse_mode': 'HTML'
        }

        print(f"Uploading to Telegram channel: {channel_id}")
        response = requests.post(url, files=files, data=data, timeout=300)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"Successfully uploaded to Telegram!")
                return result
            else:
                raise Exception(f"Telegram API error: {result.get('description')}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
