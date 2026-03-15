"""
Test minimal pour la boucle d'apprentissage du self-improving system.
"""
from learning_loop import LearningLoop

def test_learning_loop():
    class DummyCollector:
        def collect(self):
            return {'trades': [1, 2, 3]}
    class DummyAnalyzer:
        def analyze(self, results):
            return {'performance': 'ok', 'results': results}
    class DummyUpdater:
        def update(self, analysis):
            pass
    class DummyLauncher:
        def launch(self):
            pass
    loop = LearningLoop(DummyCollector(), DummyAnalyzer(), DummyUpdater(), DummyLauncher())
    output = loop.run_cycle()
    assert output['performance'] == 'ok'
    print('Test learning_loop OK')

if __name__ == '__main__':
    test_learning_loop()
