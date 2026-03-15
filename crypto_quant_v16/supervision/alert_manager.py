from typing import List
import datetime

class AlertManager:
    """
    Centralise toutes les alertes (Telegram, Email, Webhook)
    """
    def __init__(self, telegram_bot=None):
        self.alerts: List[dict] = []
        self.telegram_bot = telegram_bot

    def add_alert(self, message: str, severity: str = "INFO"):
        alert = {
            "timestamp": datetime.datetime.now().isoformat(),
            "message": message,
            "severity": severity
        }
        self.alerts.append(alert)

        # Envoyer sur Telegram si configuré
        if self.telegram_bot:
            self.telegram_bot.send_message(f"[{severity}] {message}")

        # TODO: ajouter email / webhook si besoin
        print(f"[{severity}] {message}")

    def get_recent_alerts(self, n: int = 10):
        return self.alerts[-n:]
