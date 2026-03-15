class DiagnosisEngine:
    def analyze(self, logs):
        # Analyse simple, à étendre avec ML
        if "critical" in logs:
            return {"requires_human": True, "reason": "critical error"}
        return {"requires_human": False, "reason": "minor"}
