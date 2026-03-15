from telegram import Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from typing import List
import logging

# -------------------------
# Configuration logging
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramIntegration:
    """
    Bot Telegram pour alertes, monitoring et commandes.
    """

    def __init__(self, token: str, chat_id: str):
        self.bot_token = token
        self.chat_id = chat_id
        self.bot = Bot(token=self.bot_token)
        self.updater = Updater(token=self.bot_token, use_context=True)
        self.dispatcher = self.updater.dispatcher

        # Commandes dynamiques
        self.dispatcher.add_handler(CommandHandler('status', self.status_command))
        self.dispatcher.add_handler(CommandHandler('alerts', self.alerts_command))
        self.dispatcher.add_handler(CommandHandler('pnl', self.pnl_command))
        self.dispatcher.add_handler(CommandHandler('portfolio', self.portfolio_command))
        self.dispatcher.add_handler(CommandHandler('sniper_status', self.sniper_status_command))

        self.alerts: List[str] = []

    # -------------------------
    # Envoyer un message
    # -------------------------
    def send_message(self, message: str):
        self.bot.send_message(chat_id=self.chat_id, text=message)

    # -------------------------
    # Ajouter une alerte
    # -------------------------
    def add_alert(self, alert: str):
        self.alerts.append(alert)
        self.send_message(f"[ALERT] {alert}")

    # -------------------------
    # Commande /status
    # -------------------------
    def status_command(self, update, context: CallbackContext):
        update.message.reply_text("AI Quant Lab status: Running")

    # -------------------------
    # Commande /alerts
    # -------------------------
    def alerts_command(self, update, context: CallbackContext):
        if not self.alerts:
            update.message.reply_text("No alerts.")
        else:
            update.message.reply_text("\n".join(self.alerts[-10:]))

    # -------------------------
    # Commande /pnl
    # -------------------------
    def pnl_command(self, update, context: CallbackContext):
        # TODO: afficher PnL des stratégies
        update.message.reply_text("PnL: +X% (exemple)")

    # -------------------------
    # Commande /portfolio
    # -------------------------
    def portfolio_command(self, update, context: CallbackContext):
        # TODO: afficher portefeuille
        update.message.reply_text("Portfolio: exemple allocation capital")

    # -------------------------
    # Commande /sniper_status
    # -------------------------
    def sniper_status_command(self, update, context: CallbackContext):
        # TODO: afficher état Sniper Bot
        update.message.reply_text("Sniper Bot: actif / en paper trading")

    # -------------------------
    # Lancer le bot
    # -------------------------
    def start_bot(self):
        self.updater.start_polling()
        self.updater.idle()

if __name__ == "__main__":
    TELEGRAM_TOKEN = "TON_TELEGRAM_BOT_TOKEN"
    CHAT_ID = "TON_CHAT_ID"

    tg = TelegramIntegration(TELEGRAM_TOKEN, CHAT_ID)
    tg.add_alert("High risk detected on TOKEN_9999")
    tg.add_alert("Strategy momentum pnl: +2.3%")

    # Lancer le bot pour commandes /status et /alerts
    tg.start_bot()
