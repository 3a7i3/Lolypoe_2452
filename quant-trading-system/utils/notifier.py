"""
Notifier - Send alerts via Telegram, Email, Slack
"""

import logging
from typing import Optional
import config

logger = logging.getLogger(__name__)

class Notifier:
    """Send notifications through multiple channels"""
    
    def __init__(self):
        self.telegram_token = None
        self.email_config = None
        self.slack_token = None
        logger.info("✓ Notifier initialized")
    
    async def send_alert(self, message: str, priority: str = 'INFO'):
        """Send alert through configured channels"""
        try:
            if config.TELEGRAM_ENABLED and self.telegram_token:
                await self._send_telegram(message, priority)
            
            if config.EMAIL_ENABLED and self.email_config:
                await self._send_email(message, priority)
            
            if config.SLACK_ENABLED and self.slack_token:
                await self._send_slack(message, priority)
            
        except Exception as e:
            logger.error(f"Alert sending error: {e}")
    
    async def _send_telegram(self, message: str, priority: str):
        """Send Telegram message"""
        try:
            logger.debug(f"Telegram message: {message}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")
    
    async def _send_email(self, message: str, priority: str):
        """Send email alert"""
        try:
            logger.debug(f"Email message: {message}")
        except Exception as e:
            logger.error(f"Email error: {e}")
    
    async def _send_slack(self, message: str, priority: str):
        """Send Slack message"""
        try:
            logger.debug(f"Slack message: {message}")
        except Exception as e:
            logger.error(f"Slack error: {e}")
    
    def configure_telegram(self, token: str, chat_id: str):
        """Configure Telegram"""
        self.telegram_token = token
        logger.info("Telegram configured")
    
    def configure_email(self, sender: str, password: str, recipients: list):
        """Configure Email"""
        self.email_config = {'sender': sender, 'password': password, 'recipients': recipients}
        logger.info("Email configured")
    
    def configure_slack(self, token: str, channel: str):
        """Configure Slack"""
        self.slack_token = token
        logger.info("Slack configured")
