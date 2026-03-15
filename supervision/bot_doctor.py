from .monitor import Monitor
from .diagnosis_engine import DiagnosisEngine
from .recovery_engine import RecoveryEngine
from .notifications.telegram_notifier import TelegramNotifier

class BotDoctor:
    def __init__(self, modules, telegram_token, chat_id):
        self.modules = modules
        self.monitor = Monitor(modules)
        self.diagnosis = DiagnosisEngine()
        self.recovery = RecoveryEngine()
        self.notifier = TelegramNotifier(telegram_token, chat_id)

    def run(self):
        for module in self.modules:
            if not module.is_healthy():
                self.handle_error(module)

    def handle_error(self, module):
        for m in self.modules:
            m.stop()
        error_details = f"Module {module.name} en erreur"
        diag = self.diagnosis.analyze(module)
        if diag["requires_human"]:
            self.notifier.notify(error_details + " – intervention requise")
        else:
            self.recovery.recover(module)
            self.notifier.notify(f"{module.name} redémarré automatiquement")
