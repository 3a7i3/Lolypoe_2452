from typing import List
import datetime
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AlertManager")

class AlertManager:
    """
    Centralise toutes les alertes (Telegram, Email, Webhook)
    """
    def __init__(self, telegram_bot=None):
        self.alerts: List[dict] = []
        self.telegram_bot = telegram_bot
        self.env = os.environ

    def add_alert(self, message: str, severity: str = "INFO"):
        alert = {
            "timestamp": datetime.datetime.now().isoformat(),
            "message": message,
            "severity": severity
        }
        self.alerts.append(alert)

        # Envoyer sur Telegram si configuré
        if self.telegram_bot:
            # Supporte async si besoin
            try:
                send = getattr(self.telegram_bot, "send_message", None)
                if send:
                    if callable(send):
                        if hasattr(send, "__code__") and send.__code__.co_flags & 0x80:
                            import asyncio
                            asyncio.create_task(self.telegram_bot.send_message(f"[{severity}] {message}"))
                        else:
                            self.telegram_bot.send_message(f"[{severity}] {message}")
            except Exception as e:
                logger.error(f"Erreur envoi Telegram: {e}")

        # TODO: ajouter email / webhook si besoin
        if severity == "ERROR":
            logger.error(message)
        elif severity == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

    def get_recent_alerts(self, n: int = 10):
        return self.alerts[-n:]
