from AI_HEDGE_FUND_SYSTEM.ai.simulation_matrix.market_simulator import MarketSimulator
from AI_HEDGE_FUND_SYSTEM.ai.simulation_matrix.risk_engine import RiskEngine
from AI_HEDGE_FUND_SYSTEM.ai.simulation_matrix.stress_tests import StressTests
from AI_HEDGE_FUND_SYSTEM.ai.simulation_matrix.paper_trading import PaperTrading

class SimulationMatrix:
    def __init__(self):
        self.market_simulator = MarketSimulator()
        self.risk_engine = RiskEngine()
        self.stress_tests = StressTests()
        self.paper_trading = PaperTrading()

    def run_cycle(self, strategies):
        print("SimulationMatrix: simulating strategies...")
        simulated = self.market_simulator.simulate(strategies)
        risk_checked = self.risk_engine.check(simulated)
        stressed = self.stress_tests.run(risk_checked)
        paper_results = self.paper_trading.test(stressed)
        return paper_results
