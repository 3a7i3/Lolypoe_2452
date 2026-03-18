from .coordinator import Coordinator  # type: ignore
from .market_regime_detector import MarketRegimeDetector
from .feature_discovery_engine import FeatureDiscoveryEngine
from .meta_strategy_brain import MetaStrategyBrain
from strategy_dna_tree import StrategyDNA, EvolutionTree
from synthetic_market_simulator import SyntheticMarketSimulator
from self_designing_lab import SelfDesigningLab


import pandas as pd
import numpy as np

def main():
    # Simuler des données de marché
    np.random.seed(42)
    df = pd.DataFrame({
        "close": np.cumsum(np.random.randn(100) + 0.2),
        "rsi": np.random.uniform(30, 70, 100),
        "volume": np.random.uniform(1000, 5000, 100),
        "momentum": np.random.uniform(-1, 1, 100),
        "volatility": np.random.uniform(0.01, 0.05, 100)
    })

    # 1. Détection du régime de marché
    regime_detector = MarketRegimeDetector()
    regime = regime_detector.detect(df)
    print(f"[MarketRegime] Régime détecté : {regime}")

    # 2. Découverte de features
    feature_engine = FeatureDiscoveryEngine()
    df = feature_engine.generate(df)
    print(f"[FeatureDiscovery] Features générées : {[c for c in df.columns if 'feature' in c]}")

    # 3. Génération de stratégies simulées avec score aléatoire
    strategies = [
        {"name": f"strat_{i}", "score": np.random.uniform(0, 1)}
        for i in range(20)
    ]

    # 4. Sélection par la MetaStrategyBrain
    meta_brain = MetaStrategyBrain()
    top_strats = meta_brain.select(strategies)
    print("[MetaStrategyBrain] Top stratégies :", [s["name"] for s in top_strats])

    # 5. Exécution du cluster (pipeline classique)
    tasks = [s["name"] for s in top_strats]
    cluster = Coordinator(num_nodes=3)
    results = cluster.run_cluster(tasks)
    print("[Niveau 5] Supercluster pipeline executed.")
    print(f"Total results: {len(results)}")
    print("Sample results:", results[:5])
    # Génère un marché synthétique (bull run)
    prices = np.linspace(100, 200, 100)
    market = SyntheticMarketSimulator().generate(prices, regime="bull_run")
    print("[SyntheticMarketSimulator] Marché synthétique (bull run):", market[:5])

    # Crée un arbre génétique et ajoute quelques stratégies
    tree = EvolutionTree()
    strat1 = StrategyDNA(features=["momentum", "volatility"], score=1.2, generation=1)
    strat2 = StrategyDNA(features=["momentum", "volume"], parents=[strat1.id], score=1.5, generation=2)
    tree.add_strategy(strat1)
    tree.add_strategy(strat2)
    print("[StrategyDNA] Arbre génétique:", tree.tree)
    print("[StrategyDNA] Lignée de strat2:", tree.get_lineage(strat2.id))

    # Laboratoire autonome : génère une nouvelle stratégie selon les résultats
    lab = SelfDesigningLab()
    results = {"momentum_strategies": 3, "mean_reversion": 1}
    new_strat = lab.run(results)
    print("[SelfDesigningLab] Nouvelle stratégie générée:", new_strat)

if __name__ == "__main__":
    main()
