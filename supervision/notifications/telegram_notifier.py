import requests

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def notify(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        requests.post(url, data={"chat_id": self.chat_id, "text": message})
