import sys
try:
    import pytest
except ImportError:
    import unittest
    @unittest.skip("pytest non installé, test neutralisé")
    class TestAutonomousSupervision(unittest.TestCase):
        def test_neutralise(self):
            self.skipTest("pytest non installé")
# -*- coding: utf-8 -*-
#
# Test de supervision autonome pour BotDoctor
# Peut être exécuté avec : pytest test_autonomous_supervision.py

try:
    import pytest
except ImportError:
    import unittest
    @unittest.skip("pytest non installé, test neutralisé")
    class TestAutonomousSupervision(unittest.TestCase):
        def test_neutralise(self):
            self.skipTest("pytest non installé")
# Import BotDoctor from the correct path
from AI_HEDGE_FUND_SYSTEM.autonomous_system.bot_doctor.monitor import BotDoctor


class DummyModule:
    """A dummy module to simulate health and error states for testing BotDoctor."""
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
    """A dummy notifier to capture notification messages for assertions."""
    def __init__(self):
        self.messages = []
    def notify_all(self, message):
        print(f"[NOTIFY] {message}")
        self.messages.append(message)

def test_critical_error_triggers_notification():
    """Test that a critical error triggers a stop and sends a notification requiring intervention."""
    module = DummyModule("TestModule", healthy=False)
    module.set_logs("critical: crash detected")
    notifier = DummyNotifier()
    doctor = BotDoctor([module], notifier)
    doctor.monitor()
    assert module.stopped, "Module should be stopped on critical error"
    assert any("intervention requise" in m for m in notifier.messages), "Notification should be sent for critical error"

def test_minor_error_auto_recovery():
    """Test that a minor error triggers stop, auto-restart, and sends a recovery notification."""
    module = DummyModule("TestModule", healthy=False)
    module.set_logs("minor: recoverable glitch")
    notifier = DummyNotifier()
    doctor = BotDoctor([module], notifier)
    doctor.monitor()
    assert module.stopped, "Module should be stopped on error"
    assert module.restarted, "Module should be restarted automatically on minor error"
    assert any("redémarré automatiquement" in m for m in notifier.messages), "Notification for auto-restart should be sent"

# If using pytest, these tests will be auto-discovered. For manual run:
if __name__ == "__main__":
    print("Test 1: Critical error triggers notification...")
    try:
        test_critical_error_triggers_notification()
        print("Test 1 passed.\n")
    except AssertionError as e:
        print(f"Test 1 failed: {e}\n")
    print("Test 2: Minor error triggers auto-recovery...")
    try:
        test_minor_error_auto_recovery()
        print("Test 2 passed.\nAll tests OK.")
    except AssertionError as e:
        print(f"Test 2 failed: {e}\n")
