import pandas as pd
from ai_research_agent.research_engine import AIResearchEngine

# Génère un DataFrame de test
market_data = pd.DataFrame({
    "close": [100, 102, 101, 105, 110, 108, 112, 115, 117, 120, 119, 121, 123, 125, 127, 130, 128, 126, 124, 122, 121],
    "volume": [1000, 1200, 1100, 1500, 2000, 1800, 2500, 3000, 3500, 4000, 3900, 4100, 4200, 4300, 4400, 4500, 4200, 4100, 4000, 3900, 3800]
})

# Simule des résultats de stratégies déjà testées
strategy_results = ["volatility_expansion_strategy"]

engine = AIResearchEngine(market_data, strategy_results)
report = engine.run_research()

print("Rapport de recherche AI Research Agent :")
print(report)
