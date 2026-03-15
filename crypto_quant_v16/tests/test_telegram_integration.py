import unittest
from unittest.mock import patch, MagicMock
from crypto_quant_v16.supervision import telegram_bot

class TestTelegramIntegration(unittest.TestCase):
    def setUp(self):
        # Patch Bot and Updater to avoid real network calls
        self.patcher_bot = patch('crypto_quant_v16.supervision.telegram_bot.Bot', autospec=True)
        self.patcher_updater = patch('crypto_quant_v16.supervision.telegram_bot.Updater', autospec=True)
        self.MockBot = self.patcher_bot.start()
        self.MockUpdater = self.patcher_updater.start()
        self.addCleanup(self.patcher_bot.stop)
        self.addCleanup(self.patcher_updater.stop)
        self.tg = telegram_bot.TelegramIntegration('FAKE_TOKEN', 'FAKE_CHAT_ID')

    def test_send_message(self):
        self.tg.send_message('Hello')
        self.tg.bot.send_message.assert_called_with(chat_id='FAKE_CHAT_ID', text='Hello')

    def test_add_alert(self):
        self.tg.add_alert('Test alert')
        self.assertIn('Test alert', self.tg.alerts)
        self.tg.bot.send_message.assert_called_with(chat_id='FAKE_CHAT_ID', text='[ALERT] Test alert')

    def test_status_command(self):
        update = MagicMock()
        context = MagicMock()
        self.tg.status_command(update, context)
        update.message.reply_text.assert_called_with('AI Quant Lab status: Running')

    def test_alerts_command(self):
        update = MagicMock()
        context = MagicMock()
        self.tg.alerts = ['A1', 'A2']
        self.tg.alerts_command(update, context)
        update.message.reply_text.assert_called()

if __name__ == '__main__':
    unittest.main()
