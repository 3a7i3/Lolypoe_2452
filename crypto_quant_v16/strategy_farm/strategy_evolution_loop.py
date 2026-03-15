import numpy as np
import pandas as pd
import json
from strategy_genome_engine import StrategyGenomeEngine
from strategy_evolution import StrategyEvolution
from quant.backtester import Backtester
from strategy_backtest_integration import strategy_to_signal

N_GENERATIONS = 5
POP_SIZE = 50
TOP_K = 10
MUTATION_RATE = 0.3

# Mock data (à remplacer par vos données réelles)
n = 300
np.random.seed(42)
prices = np.cumsum(np.random.randn(n)) + 100
volumes = np.random.normal(1000, 200, n)
df = pd.DataFrame({"close": prices, "volume": volumes})

engine = StrategyGenomeEngine()
try:
    with open("top_strategies.json", "r", encoding="utf-8") as f:
        top = json.load(f)
    print("Top 3 chargé depuis top_strategies.json. Nouvelle génération à partir du top.")
    pop = [s["strategy"] if isinstance(s, dict) and "strategy" in s else s for s in top] * (POP_SIZE // len(top))
    pop = pop[:POP_SIZE]
except Exception:
    print("Aucun top_strategies.json trouvé, génération aléatoire.")
    pop = engine.generate_population(POP_SIZE)

evol = StrategyEvolution(engine)
backtester = Backtester()


# --- Suivi graphique de la performance ---
import matplotlib.pyplot as plt
perf_history = []

for gen in range(N_GENERATIONS):
    print(f"\n=== Génération {gen+1} ===")
    results = []
    for strat in pop:
        signals = strategy_to_signal(strat, df)
        result = backtester.backtest(prices, signals)
        results.append({
            "strategy": strat,
            "total_return": result["total_return"],
            "sharpe": result["sharpe"]
        })
    # Sélectionne les TOP_K meilleures
    top = sorted(results, key=lambda x: (x["total_return"], x["sharpe"]), reverse=True)[:TOP_K]
    print("Top stratégies de la génération :")
    for i, strat in enumerate(top, 1):
        print(f"#{i} - {strat['strategy']}\n  Total Return: {strat['total_return']:.2%}, Sharpe: {strat['sharpe']:.2f}\n")
    # Suivi du meilleur return
    perf_history.append(top[0]["total_return"])
    # Sauvegarde
    with open("top_strategies.json", "w", encoding="utf-8") as f:
        json.dump(top, f, indent=2, ensure_ascii=False)
    # Nouvelle génération par évolution
    pop = [s["strategy"] for s in top] * (POP_SIZE // TOP_K)
    pop = pop[:POP_SIZE]
    pop = [evol.mutate(s, MUTATION_RATE) for s in pop]

# Affiche la courbe de performance
plt.figure(figsize=(10,5))
plt.plot(perf_history, marker='o')
plt.title("Top Total Return par Génération")
plt.xlabel("Génération")
plt.ylabel("Total Return")
plt.grid()
plt.show()

# --- Intégration Panel Dashboard ---
try:
    import panel as pn
    pn.extension('matplotlib')
    def show_perf():
        plt.figure(figsize=(10,5))
        plt.plot(perf_history, marker='o')
        plt.title("Top Total Return par Génération")
        plt.xlabel("Génération")
        plt.ylabel("Total Return")
        plt.grid()
        return plt.gcf()
    dashboard = pn.Column(
        pn.pane.Markdown("# Evolution des Stratégies\nSuivi du meilleur total return à chaque génération."),
        pn.pane.Matplotlib(show_perf, tight=True)
    )
    if __name__ == "__main__":
        dashboard.servable()
        pn.serve(dashboard, port=5027, show=True)
except ImportError:
    pass
