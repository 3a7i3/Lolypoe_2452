import smtplib
from email.mime.text import MIMEText
from utils.logger import logger

def notify_trade(symbol, signal, price):
    """Envoie une notification de trade."""
    try:
        message = f"[{symbol}] Signal: {signal} @ ${price:.2f}"
        logger.info(f"Trade notification: {message}")
        # TODO: Integrer Telegram/Email
    except Exception as e:
        logger.error(f"Erreur notification: {e}")

def notify_error(error_msg):
    """Envoie une notification d'erreur."""
    try:
        logger.error(f"Alert: {error_msg}")
        # TODO: Integrer alertes
    except Exception as e:
        logger.error(f"Erreur alerte: {e}")
