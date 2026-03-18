# Pipeline multi-agent — Niveau 4
import sys, os
sys.path.append(os.path.dirname(__file__))
# from AI_HEDGE_FUND_SYSTEM.ai.agents.data_agent import DataAgent  # Patch: module absent, import commenté pour stabilité
from agents.feature_scientist import FeatureScientist
from agents.strategy_designer import StrategyDesigner
from agents.risk_manager import RiskManager
from agents.portfolio_manager import PortfolioManager
from simulation_matrix import SimulationMatrix

def run_ecosystem_pipeline():
    print("[PIPELINE_ECOSYSTEM] Début pipeline multi-agent Niveau 4")
    data = DataAgent().fetch()
    features = FeatureScientist().extract(data)
    strategies = StrategyDesigner().design(features, n=5)
    risk = RiskManager()
    valid = [s for s in strategies if risk.validate(s)]
    alloc = PortfolioManager().allocate(valid)
    sim = SimulationMatrix()
    results = [sim.simulate(s) for s in valid]
    print("Résultats simulation:", results)
    print("Allocation:", alloc)

if __name__ == "__main__":
    run_ecosystem_pipeline()
