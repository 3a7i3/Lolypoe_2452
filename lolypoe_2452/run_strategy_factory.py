from data_engine.market_data import MarketData
from data_engine.feature_engine import FeatureEngine
from strategy_factory.generator import StrategyGenerator
from strategy_factory.backtester import Backtester
from strategy_factory.evolution import Evolution

data = MarketData()
df = data.load_dummy()
features = FeatureEngine()
df = features.compute(df)
generator = StrategyGenerator()
backtester = Backtester()
evolution = Evolution()

strategies = generator.generate(200)

for generation in range(10):
    scores = []
    for strat in strategies:
        pnl = backtester.run(strat, df)
        scores.append(pnl)
    strategies = evolution.evolve(strategies, scores)
    print("Generation:", generation)
