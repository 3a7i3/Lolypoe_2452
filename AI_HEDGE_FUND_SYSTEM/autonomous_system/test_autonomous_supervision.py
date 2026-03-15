from bot_doctor.monitor import BotDoctor
from dashboard.module_status import ModuleStatus
from notifications.telegram_notifier import TelegramNotifier

class DummyModule:
    def __init__(self, name, healthy=True):
        self.name = name
        self.status = "healthy"
        self._healthy = healthy
        self._logs = ""
        self.stopped = False
        self.restarted = False

    def is_healthy(self):
        return self._healthy

    def stop(self):
        self.status = "stopped"
        self.stopped = True

    def restart(self):
        self.status = "healthy"
        self.restarted = True
        self._healthy = True

    def get_logs(self):
        return self._logs

    def set_logs(self, logs):
        self._logs = logs

class DummyNotifier:
    def __init__(self):
        self.messages = []
    def notify_all(self, message):
        print(f"[NOTIFY] {message}")
        self.messages.append(message)

def test_critical_error_triggers_notification():
    module = DummyModule("TestModule", healthy=False)
    module.set_logs("critical: crash detected")
    notifier = DummyNotifier()
    doctor = BotDoctor([module], notifier)
    doctor.monitor()
    assert module.stopped, "Module should be stopped on critical error"
    assert any("intervention requise" in m for m in notifier.messages), "Notification should be sent for critical error"

def test_minor_error_auto_recovery():
    module = DummyModule("TestModule", healthy=False)
    module.set_logs("minor: recoverable glitch")
    notifier = DummyNotifier()
    doctor = BotDoctor([module], notifier)
    doctor.monitor()
    assert module.stopped, "Module should be stopped on error"
    assert module.restarted, "Module should be restarted automatically on minor error"
    assert any("redémarré automatiquement" in m for m in notifier.messages), "Notification for auto-restart should be sent"

if __name__ == "__main__":
    print("Test 1: Critical error triggers notification...")
    test_critical_error_triggers_notification()
    print("Test 1 passed.\n")
    print("Test 2: Minor error triggers auto-recovery...")
    test_minor_error_auto_recovery()
    print("Test 2 passed.\nAll tests OK.")
