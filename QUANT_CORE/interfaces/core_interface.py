"""
CoreInterface stub for QUANT_CORE
"""
class CoreInterface:
    def __init__(self, quant_core):
        self.quant_core = quant_core

    def connect_dashboards(self):
        """Expose une API pour dashboards (exécution, résultats, validation)."""
        return {
            "run_strategy": self.quant_core.run_backtest_and_validate,
            "get_allocation": self.quant_core.allocate_portfolio,
        }

    def connect_agents(self):
        """Expose une API pour agents (génération, validation, allocation)."""
        return {
            "generate_strategy": self.quant_core.strategy.generate,
            "validate_strategy": self.quant_core.validator.validate,
        }

    def connect_telegram(self):
        """Expose une API pour Telegram (alertes, reporting)."""
        return {
            "send_alert": lambda msg: print(f"[Telegram] {msg}"),
            "report_results": lambda res: print(f"[Telegram Report] {res}"),
        }
