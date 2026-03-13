"""
Notifier - Envoi d'alertes et notifications
"""

from config import TELEGRAM_ENABLED, EMAIL_ENABLED, SLACK_ENABLED
from utils.logger import logger

def send_alert(subject, message, severity='INFO'):
    """Envoie une alerte via les canaux configures."""
    
    if TELEGRAM_ENABLED:
        try:
            send_telegram(message)
        except Exception as e:
            logger.error(f"Erreur Telegram: {e}")
    
    if EMAIL_ENABLED:
        try:
            send_email(subject, message)
        except Exception as e:
            logger.error(f"Erreur Email: {e}")
    
    if SLACK_ENABLED:
        try:
            send_slack(f"*{subject}*\n{message}")
        except Exception as e:
            logger.error(f"Erreur Slack: {e}")

def send_telegram(message):
    """Envoie une alerte Telegram."""
    # A implementer avec python-telegram-bot
    pass

def send_email(subject, body):
    """Envoie une alerte Email."""
    # A implementer
    pass

def send_slack(message):
    """Envoie une alerte Slack."""
    # A implementer avec slack-sdk
    pass

def notify_trade_opened(symbol, signal, price):
    """Notifie l'ouverture d'un trade."""
    send_alert(f"Trade Ouvert: {symbol}", f"{signal} @ ${price:.2f}")

def notify_trade_closed(symbol, pnl):
    """Notifie la fermeture d'un trade."""
    send_alert(f"Trade Ferme: {symbol}", f"PnL: {pnl:.2f}%", 
               severity='INFO' if pnl > 0 else 'WARNING')

def notify_risk_limit(description):
    """Notifie un dépassement de limite de risque."""
    send_alert("Alerte Risque!", description, severity='CRITICAL')
