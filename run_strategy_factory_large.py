from strategy_factory.generator import StrategyGenerator
from strategy_factory.backtester import Backtester
from strategy_factory.evolution import EvolutionEngine
from strategy_factory.alpha_vault import AlphaVault
import pandas as pd

# Génère un DataFrame factice (à remplacer par de vraies données marché)
df = pd.DataFrame({
    "momentum": [0.2 + 0.01*i for i in range(200)],
    "close": [100 + i*0.5 for i in range(200)]
})

generator = StrategyGenerator()
evolution = EvolutionEngine()
vault = AlphaVault()
backtester = Backtester()

strategies = generator.generate(2000)

for generation in range(30):
    scores = [backtester.evaluate(s, df) for s in strategies]
    # Sauvegarde les 10 meilleures stratégies de chaque génération
    top = sorted(zip(strategies, scores), key=lambda x: x[1], reverse=True)[:10]
    for strat, score in top:
        vault.store(strat, score)
    strategies = evolution.evolve(strategies, scores)
    print(f"Generation {generation} | Top score: {top[0][1]:.2f}")

print(f"Total stratégies sauvegardées dans l'Alpha Vault: {len(vault.database)}")
