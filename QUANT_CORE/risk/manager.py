class RiskManager:
    def __init__(self, max_drawdown=0.2):
        self.max_drawdown = max_drawdown

    def check_risk(self, position):
        print(f"[RiskManager] Checking position {position}")
        return True
"""
RiskManager stub for QUANT_CORE
"""
class RiskManager:
    def __init__(self):
        self.max_exposure = 100000  # Exemple de limite
        self.bot_doctor = None  # Peut être injecté

    def validate(self, strategy):
        """Valide la stratégie selon les limites de risque et Bot Doctor."""
        # Exemple : vérification de l'exposition
        exposure = strategy.get('exposure', 0)
        if exposure > self.max_exposure:
            return {"approved": False, "reason": "Limite d'exposition dépassée"}
        # Intégration Bot Doctor
        if self.bot_doctor:
            bot_result = self.bot_doctor.validate(strategy)
            if not bot_result["approved"]:
                return bot_result
        return {"approved": True, "reason": ""}
