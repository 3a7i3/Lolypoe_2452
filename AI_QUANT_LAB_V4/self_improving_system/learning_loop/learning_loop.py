"""
Boucle centrale du système self-improving quant.
Orchestre l'apprentissage, l'analyse de performance, et le lancement de nouvelles recherches.
"""


try:
    from .collect_results import ResultCollector
    from .analyze_results import ResultAnalyzer
    from .update_models import ModelUpdater
    from .launch_new_research import ResearchLauncher
    from ..performance_analyzer.performance_analyzer import PerformanceAnalyzer
    from ..strategy_evolution_engine.strategy_evolution import StrategyEvolution
    from ..meta_strategy_ai.meta_strategy_ai import MetaStrategyAI
    from ..market_manipulation_detector.market_manipulation_detector import MarketManipulationDetector
    from ..global_macro_intelligence.global_macro_intelligence import GlobalMacroIntelligence
    from ..rl_trader.rl_trader import RLTrader
except ImportError:
    # Permet l'exécution directe du script
    from collect_results import ResultCollector
    from analyze_results import ResultAnalyzer
    from update_models import ModelUpdater
    from launch_new_research import ResearchLauncher
    # Import local direct pour tous les modules avancés
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'performance_analyzer')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'strategy_evolution_engine')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'meta_strategy_ai')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'market_manipulation_detector')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'global_macro_intelligence')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rl_trader')))
    from performance_analyzer import PerformanceAnalyzer
    from strategy_evolution import StrategyEvolution
    from meta_strategy_ai import MetaStrategyAI
    from market_manipulation_detector import MarketManipulationDetector
    from global_macro_intelligence import GlobalMacroIntelligence
    from rl_trader import RLTrader
except ImportError:
    # Permet l'exécution directe du script
    from collect_results import ResultCollector
    from analyze_results import ResultAnalyzer
    from update_models import ModelUpdater
    from launch_new_research import ResearchLauncher


class LearningLoop:
    def __init__(self, result_collector, analyzer, model_updater, research_launcher,
                 perf_analyzer=None, strategy_evolver=None, meta_strategy_ai=None,
                 manipulation_detector=None, macro_intel=None, rl_trader=None):
        self.result_collector = result_collector
        self.analyzer = analyzer
        self.model_updater = model_updater
        self.research_launcher = research_launcher
        self.perf_analyzer = perf_analyzer or PerformanceAnalyzer()
        self.strategy_evolver = strategy_evolver or StrategyEvolution()
        self.meta_strategy_ai = meta_strategy_ai or MetaStrategyAI()
        self.manipulation_detector = manipulation_detector or MarketManipulationDetector()
        self.macro_intel = macro_intel or GlobalMacroIntelligence()
        self.rl_trader = rl_trader or RLTrader()

    def run_cycle(self):
        print("[LearningLoop] Fetching macro data...")
        macro_data = {
            'crypto': self.macro_intel.fetch_crypto_data(),
            'stocks': self.macro_intel.fetch_stock_data(),
            'forex': self.macro_intel.fetch_forex_data(),
            'macro': self.macro_intel.fetch_macro_data()
        }
        print(f"[LearningLoop] Macro data: {macro_data}")
        print("[LearningLoop] Collecting results...")
        results = self.result_collector.collect()
        print(f"[LearningLoop] Results: {results}")
        analysis = self.analyzer.analyze(results)
        print(f"[LearningLoop] Analysis: {analysis}")
        trades = results.get('trades', [])
        perf = self.perf_analyzer.sharpe_analysis(trades)
        print(f"[LearningLoop] Sharpe: {perf}")
        evolved = self.strategy_evolver.evolution_cycle(trades)
        print(f"[LearningLoop] Evolved population: {evolved}")
        # Market manipulation detection
        whales = self.manipulation_detector.detect_whale_activity(trades)
        pump = self.manipulation_detector.detect_pump_and_dump([t.get('pnl', 0) for t in trades])
        liquidity = self.manipulation_detector.detect_liquidity_trap({'spread': 10})
        print(f"[LearningLoop] Manipulation alerts: {self.manipulation_detector.alerts}")
        # MetaStrategyAI : sélectionne et combine les meilleures stratégies
        strategies = [t['strategy'] for t in trades] if trades else []
        performances = [t['sharpe'] for t in trades] if trades else []
        selected = self.meta_strategy_ai.select_strategies(strategies, performances, top_n=2)
        weights = self.meta_strategy_ai.allocate_weights([t['sharpe'] for t in trades if t['strategy'] in selected])
        portfolio = self.meta_strategy_ai.combine_portfolio(selected, weights)
        print(f"[LearningLoop] MetaStrategy portfolio: {portfolio}")
        # RLTrader : propose une action RL sur la base du signal moyen
        avg_signal = sum([t.get('pnl', 0) for t in trades]) / len(trades) if trades else 0
        rl_action = self.rl_trader.act({'signal': avg_signal})
        print(f"[LearningLoop] RLTrader action: {rl_action}")
        # Propagation de la population évoluée dans la mise à jour
        self.model_updater.update({
            'analysis': analysis,
            'evolved_population': evolved,
            'meta_portfolio': portfolio,
            'manipulation_alerts': self.manipulation_detector.alerts,
            'macro_data': macro_data,
            'rl_action': rl_action
        })
        self.research_launcher.launch()
        return {
            'analysis': analysis,
            'sharpe': perf,
            'evolved_population': evolved,
            'meta_portfolio': portfolio,
            'manipulation_alerts': self.manipulation_detector.alerts,
            'macro_data': macro_data,
            'rl_action': rl_action
        }

# Test d'intégration avec ResultCollector réel
def test_learning_loop():
    # Import absolu pour exécution directe
    from collect_results import ResultCollector
    from analyze_results import ResultAnalyzer
    from update_models import ModelUpdater
    from launch_new_research import ResearchLauncher
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'performance_analyzer')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'strategy_evolution_engine')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'meta_strategy_ai')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'market_manipulation_detector')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'global_macro_intelligence')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rl_trader')))
    from performance_analyzer import PerformanceAnalyzer
    from strategy_evolution import StrategyEvolution
    from meta_strategy_ai import MetaStrategyAI
    from market_manipulation_detector import MarketManipulationDetector
    from global_macro_intelligence import GlobalMacroIntelligence
    from rl_trader import RLTrader
    updater = ModelUpdater()
    launcher = ResearchLauncher()
    perf_analyzer = PerformanceAnalyzer()
    strategy_evolver = StrategyEvolution()
    meta_ai = MetaStrategyAI()
    manipulation_detector = MarketManipulationDetector()
    macro_intel = GlobalMacroIntelligence()
    rl_trader = RLTrader()
    loop = LearningLoop(ResultCollector(), ResultAnalyzer(), updater, launcher, perf_analyzer, strategy_evolver, meta_ai, manipulation_detector, macro_intel, rl_trader)
    # Test normal
    output = loop.run_cycle()
    assert output['analysis']['performance'] == 'analyzed'
    assert 'summary' in output['analysis']
    assert updater.update_log[-1]['analysis']['performance'] == 'analyzed'
    assert isinstance(updater.update_log[-1]['evolved_population'], list)
    assert isinstance(updater.update_log[-1]['meta_portfolio'], list)
    assert isinstance(updater.update_log[-1]['manipulation_alerts'], list)
    assert isinstance(updater.update_log[-1]['macro_data'], dict)
    assert isinstance(updater.update_log[-1]['rl_action'], str)
    assert launcher.launch_log[-1]['launched'] is True
    assert isinstance(output['sharpe'], float)
    assert isinstance(output['evolved_population'], list)
    assert isinstance(output['meta_portfolio'], list)
    assert isinstance(output['manipulation_alerts'], list)
    assert isinstance(output['macro_data'], dict)
    assert isinstance(output['rl_action'], str)
    print('Test learning_loop (normal) OK')

    # Test avec population vide
    class EmptyCollector:
        def collect(self):
            return {'trades': []}
    loop_empty = LearningLoop(EmptyCollector(), ResultAnalyzer(), updater, launcher, perf_analyzer, strategy_evolver, meta_ai, manipulation_detector, macro_intel, rl_trader)
    output_empty = loop_empty.run_cycle()
    assert output_empty['analysis']['performance'] == 'no_data'
    assert output_empty['evolved_population'] == [] or isinstance(output_empty['evolved_population'], list)
    assert output_empty['meta_portfolio'] == [] or isinstance(output_empty['meta_portfolio'], list)
    assert isinstance(output_empty['manipulation_alerts'], list)
    assert isinstance(output_empty['macro_data'], dict)
    assert isinstance(output_empty['rl_action'], str)
    print('Test learning_loop (empty) OK')

if __name__ == '__main__':
    test_learning_loop()
