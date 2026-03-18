try:
    from AI_HEDGE_FUND_SYSTEM.ai.strategy_farm.farm import StrategyFarm
except ImportError:
    StrategyFarm = None  # Patch: module absent, neutralisation pour stabilité

class ResearchNode:
    def __init__(self):
        self.farm = StrategyFarm()

    def run_research(self, df):
        print("[ResearchNode] Running research...")
        best = self.farm.run(df)
        return best
