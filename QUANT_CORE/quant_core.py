"""
QUANT_CORE main orchestrator

Coordinates data, features, backtesting, risk, portfolio, strategy, and validation.
Secondary modules connect via interfaces.
"""

from QUANT_CORE.data import DataCollector
from QUANT_CORE.features import FeatureEngineer
from QUANT_CORE.backtesting import BacktestEngine
from QUANT_CORE.risk import RiskManager
from QUANT_CORE.portfolio import PortfolioAllocator
from QUANT_CORE.strategy import StrategyGenerator
from QUANT_CORE.validation import StrategyValidator
from QUANT_CORE.interfaces import CoreInterface

class QuantCore:
    def __init__(self):
        self.data = DataCollector()
        self.features = FeatureEngineer()
        self.backtester = BacktestEngine()
        self.risk = RiskManager()
        self.portfolio = PortfolioAllocator()
        self.strategy = StrategyGenerator()
        self.validator = StrategyValidator()
        self.interface = CoreInterface(self)

    def run_backtest_and_validate(self, strategy):
        results = self.backtester.run(strategy, self.data, self.features)
        validation = self.validator.validate(strategy, results, self.risk)
        if not validation.approved:
            print(f"Strategy blocked: {validation.reason}")
            return None
        return results

    def allocate_portfolio(self):
        return self.portfolio.allocate(self.data, self.features)

    def connect_secondary_layers(self):
        self.interface.connect_dashboards()
        self.interface.connect_agents()
        self.interface.connect_telegram()

# All strategy execution must pass through run_backtest_and_validate
