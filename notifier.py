import requests
import config

class TelegramNotifier:
    """
    Telefonunuza Telegram üzerinden anlık işlem ve durum bildirimleri gönderir.
    """
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = config.TELEGRAM_ENABLED

    def send_message(self, message: str):
        if not self.enabled or self.token == "YOUR_TELEGRAM_BOT_TOKEN":
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[-] Telegram bildirim gönderim hatası: {e}")