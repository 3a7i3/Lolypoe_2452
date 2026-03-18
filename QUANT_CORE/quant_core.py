"""
QUANT_CORE main orchestrator

Coordinates data, features, backtesting, risk, portfolio, strategy, and validation.
Secondary modules connect via interfaces.
"""


try:
    from QUANT_CORE.data import DataCollector
except ImportError:
    DataCollector = None
try:
    from QUANT_CORE.features import FeatureEngineer
except ImportError:
    FeatureEngineer = None
try:
    from QUANT_CORE.backtesting import BacktestEngine
except ImportError:
    BacktestEngine = None
try:
    from QUANT_CORE.risk import RiskManager
except ImportError:
    RiskManager = None
try:
    from QUANT_CORE.portfolio import PortfolioAllocator
except ImportError:
    PortfolioAllocator = None
try:
    from QUANT_CORE.strategy import StrategyGenerator
except ImportError:
    StrategyGenerator = None
try:
    from QUANT_CORE.validation import StrategyValidator
except ImportError:
    StrategyValidator = None
try:
    from QUANT_CORE.interfaces import CoreInterface
except ImportError:
    CoreInterface = None

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
