from AI_HEDGE_FUND_SYSTEM.ai.quant_matrix.matrix_core import QuantMatrix

class DummyModule:
    def generate(self, market_data):
        return {}
    def run(self, features):
        return [{}]
    def scan(self):
        return []
    def suggest(self, features, social, whale):
        return [{}]
    def evolve(self, strategies):
        return strategies
    def select_best(self, strategies):
        return strategies[:1]
    def choose_action(self, best):
        return 'hold'
    def execute(self, action):
        return {'pnl': 1}
    def reward(self, pnl):
        pass
    def store(self, best, result):
        pass

def test_matrix_cycle():
    matrix = QuantMatrix()
    dummy = DummyModule()
    # Patch: autoriser l’injection de mocks même si le typage original est restrictif
    setattr(matrix, 'feature_lab', dummy)
    setattr(matrix, 'strategy_farm', dummy)
    setattr(matrix, 'social_ai', dummy)
    setattr(matrix, 'whale_ai', dummy)
    setattr(matrix, 'ai_brain', dummy)
    setattr(matrix, 'evolution', dummy)
    setattr(matrix, 'alpha_vault', dummy)
    setattr(matrix, 'rl_trader', dummy)
    setattr(matrix, 'execution_engine', dummy)
    result = matrix.run_cycle({})
    assert result is not None
    print('Test passed: QuantMatrix cycle runs.')
import unittest
from AI_HEDGE_FUND_SYSTEM.ai.quant_matrix.matrix_core import QuantMatrix


class DummyFarm:
    def run(self, df):
        # Retourne des dicts pour simuler des stratégies
        return [{"name": "strat1"}, {"name": "strat2"}]


class DummyEvolution:
    def evolve(self, strategies):
        # Robuste à l'absence de clé 'name'
        result = []
        for s in strategies:
            if isinstance(s, dict) and "name" in s:
                result.append(s["name"]+"_evolved")
            else:
                result.append(str(s)+"_evolved")
        return result

class TestQuantMatrix(unittest.TestCase):
    def test_cycle(self):
        matrix = QuantMatrix()
        matrix.register('feature_lab', DummyModule())
        matrix.register('strategy_farm', DummyFarm())
        matrix.register('social_ai', DummyModule())
        matrix.register('whale_ai', DummyModule())
        matrix.register('ai_brain', DummyModule())
        matrix.register('evolution', DummyEvolution())
        matrix.register('alpha_vault', DummyModule())
        matrix.register('rl_trader', DummyModule())
        matrix.register('execution_engine', DummyModule())
        result = matrix.run_cycle(market_data={})
        self.assertEqual(result, {'pnl': 1})

if __name__ == "__main__":
    unittest.main()
