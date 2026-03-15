class BotDoctor:
    def __init__(self, modules, notifier):
        self.modules = modules
        self.notifier = notifier

    def monitor(self):
        for module in self.modules:
            if not module.is_healthy():
                self.handle_error(module)

    def handle_error(self, module):
        for m in self.modules:
            m.stop()
        error_details = f"Module {module.name} en erreur"
        diagnosis = self.diagnose(module)
        if diagnosis["requires_human"]:
            self.notifier.notify_all(error_details + " – intervention requise")
        else:
            self.recover(module)

    def diagnose(self, module):
        logs = module.get_logs()
        if "critical" in logs:
            return {"requires_human": True}
        return {"requires_human": False}

    def recover(self, module):
        module.restart()
        self.notifier.notify_all(f"{module.name} redémarré automatiquement")
