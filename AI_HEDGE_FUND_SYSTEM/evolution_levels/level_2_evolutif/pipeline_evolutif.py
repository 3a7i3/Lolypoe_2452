# Pipeline évolutif — Niveau 2
import sys, os
sys.path.append(os.path.dirname(__file__))
from modules.evolution_engine import EvolutionEngine

# Réutilisation des modules du niveau 1
sys.path.append(os.path.join(os.path.dirname(__file__), '../level_1_functional'))
from modules.data_engine import DataEngine
from modules.feature_engineering import FeatureEngineering
from modules.strategy_generator import StrategyGenerator
from modules.backtesting_engine import BacktestingEngine
from modules.alpha_vault import AlphaVault

config = {
    "generations": 3,
    "population_size": 5,
    "n_best": 2
}

def run_evolution_pipeline():
    print("[PIPELINE_EVOLUTIF] Début pipeline évolutif Niveau 2")
    data = DataEngine().fetch()
    features = FeatureEngineering().transform(data)
    population = StrategyGenerator().generate(features, n=config["population_size"])
    evo = EvolutionEngine()
    for gen in range(config["generations"]):
        print(f"Génération {gen+1}")
        results = BacktestingEngine().run(population, features)
        selected = evo.select(results, n_best=config["n_best"])
        print("  Meilleurs:", selected)
        population = evo.next_generation(selected)
    print("Population finale:", population)

if __name__ == "__main__":
    run_evolution_pipeline()
