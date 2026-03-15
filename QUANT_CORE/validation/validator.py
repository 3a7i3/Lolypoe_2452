class Validator:
    def __init__(self):
        pass

    def validate_strategy(self, strategy):
        print("[Validator] Validating strategy")
        return True

"""
StrategyValidator stub for QUANT_CORE
Integrates Bot Doctor
"""
class StrategyValidator:
    def __init__(self):
        pass

    def validate(self, strategy, backtest_results, risk_manager):
        """Valide la stratégie via Bot Doctor et résultats de backtest."""
        bot_doctor_result = risk_manager.validate(strategy)
        if not bot_doctor_result["approved"]:
            return {"approved": False, "reason": bot_doctor_result["reason"]}
        # Validation sur les métriques de backtest
        metrics = backtest_results.get("metrics", {})
        sharpe = metrics.get("sharpe", 1.0)
        drawdown = metrics.get("max_drawdown", 0.05)
        win_ratio = metrics.get("win_ratio", 0.5)
        if sharpe < 1.0 or drawdown > 0.15 or win_ratio < 0.45:
            return {"approved": False, "reason": "Stratégie non conforme aux critères de performance"}
        return {"approved": True, "reason": "Validée par Bot Doctor et backtest"}
