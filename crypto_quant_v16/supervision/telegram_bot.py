

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from typing import List
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramIntegration:
	"""
	Bot Telegram pour alertes, monitoring et commandes (API v20+ asynchrone)
	"""
	def __init__(self, token: str = None, chat_id: str = None):
		self.bot_token = token or os.environ.get("TELEGRAM_TOKEN")
		self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
		if not self.bot_token or not isinstance(self.bot_token, str):
			raise ValueError("TELEGRAM_TOKEN is required and must be a string.")
		if not self.chat_id or not isinstance(self.chat_id, str):
			raise ValueError("TELEGRAM_CHAT_ID is required and must be a string.")
		self.bot = Bot(token=self.bot_token)
		self.alerts: List[str] = []
		self.application = ApplicationBuilder().token(self.bot_token).build()

		# Commandes dynamiques (handlers async)
		self.application.add_handler(CommandHandler('status', self.status_command))
		self.application.add_handler(CommandHandler('alerts', self.alerts_command))
		self.application.add_handler(CommandHandler('pnl', self.pnl_command))
		self.application.add_handler(CommandHandler('portfolio', self.portfolio_command))
		self.application.add_handler(CommandHandler('sniper_status', self.sniper_status_command))

	async def send_message(self, message: str):
		if not self.chat_id:
			raise ValueError("chat_id is required for sending messages.")
		await self.bot.send_message(chat_id=self.chat_id, text=message)

	async def add_alert(self, alert: str):
		self.alerts.append(alert)
		await self.send_message(f"[ALERT] {alert}")

	async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		if update.message:
			await update.message.reply_text("AI Quant Lab status: Running")

	async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		if update.message:
			if not self.alerts:
				await update.message.reply_text("No alerts.")
			else:
				await update.message.reply_text("\n".join(self.alerts[-10:]))

	async def pnl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		# TODO: afficher PnL des stratégies
		if update.message:
			await update.message.reply_text("PnL: +X% (exemple)")

	async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		# TODO: afficher portefeuille
		if update.message:
			await update.message.reply_text("Portfolio: exemple allocation capital")

	async def sniper_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		# TODO: afficher état Sniper Bot
		if update.message:
			await update.message.reply_text("Sniper Bot: actif / en paper trading")

	def start_bot(self):
		self.application.run_polling()


if __name__ == "__main__":
	tg = TelegramIntegration()

	async def main():
		await tg.add_alert("High risk detected on TOKEN_9999")
		await tg.add_alert("Strategy momentum pnl: +2.3%")

	asyncio.run(main())
	tg.start_bot()
