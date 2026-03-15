class DiagnosisEngine:
    def analyze(self, module):
        logs = module.get_logs()
        if "critical" in logs:
            return {"requires_human": True}
        return {"requires_human": False}
