

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import time
import pandas as pd
from strategy_farm.farm_engine import StrategyFarm
from strategy_farm.evolution.evolution import StrategyEvolutionLoop
from strategy_ai.dataset_builder import DatasetBuilder
from strategy_ai.model import StrategyAIModel
from strategy_ai.signal_generator import AISignalGenerator
from alpha_vault.vault import AlphaVault
from quant_matrix.matrix_core import QuantMatrix
from reinforcement.rl_agent import RLTrader
from feature_lab.feature_discovery import FeatureDiscovery
from social_ai.social_intel import SocialIntelligence
from whale_ai.whale_intel import WhaleIntelligence
from data_layer.data_loader import MarketDataLoader

# Exemple : charger BTC (crypto) ou CAC 40 (indice) via investpy
data_loader = MarketDataLoader()
# Pour BTC (crypto)
df = data_loader.load_investpy_crypto(symbol="bitcoin", interval="Daily", n=90)
# Pour CAC 40 (indice) (Investing.com)
# import investpy
# df = investpy.indices.get_index_historical_data(index="CAC 40", country="france", from_date="01/01/2023", to_date="01/04/2023")
# Pour Apple (action)
# df = data_loader.load_investpy_stock(symbol="AAPL", country="united states", interval="Daily", n=90)

# Instantiate modules
farm = StrategyFarm()
evolution = StrategyEvolutionLoop(farm)
vault = AlphaVault()
ai_dataset = DatasetBuilder()
ai_model = StrategyAIModel()
ai_signal = AISignalGenerator(ai_model)
rl_trader = RLTrader()
feature_discovery = FeatureDiscovery()
social_intel = SocialIntelligence()
whale_intel = WhaleIntelligence()

matrix = QuantMatrix()
matrix.register("strategy_farm", farm)
matrix.register("evolution", evolution)
matrix.register("alpha_vault", vault)
matrix.register("ai_brain", ai_model)

# Main research loop (demo: 2 cycles)
for cycle in range(2):
    print(f"\n=== AI Quant Matrix Cycle {cycle} ===")
    # Feature engineering
    new_features = feature_discovery.generate_combinations(df)
    df = pd.concat([df, new_features], axis=1)
    # Social/whale signals (placeholders)
    social_signals = social_intel.analyze(["tweet"], ["reddit"], ["telegram"])
    whale_signals = whale_intel.analyze(["wallet"], ["transfer"])
    # Run matrix cycle
    strategies = matrix.strategy_farm.run(df, n_strategies=20, top=5)
    for s in strategies:
        vault.store(s, 1.0)  # Score dummy
    best = vault.best(5)
    evolved = matrix.evolution.evolution.evolve([x["strategy"] if "strategy" in x else x for x in best])
    # Train AI
    dataset = ai_dataset.build(df)
    ai_model.train(dataset)
    signal = ai_signal.generate(df)
    print(f"AI Signal: {signal}")
    print(f"Best strategies: {best}")
    print(f"Evolved: {evolved[:2]}")
    print(f"RLTrader action: {rl_trader.choose_action()}")
    time.sleep(1)
print("\nAI Quant Matrix demo complete.")
