from .pattern_discovery import PatternDiscovery
from .hypothesis_generator import HypothesisGenerator
from .strategy_advisor import StrategyAdvisor
from .crash_pattern_analyzer import CrashPatternAnalyzer
from .report_generator import ReportGenerator

class AIResearchEngine:
    def __init__(self, market_data, strategy_results, strategy_farm=None):
        self.market_data = market_data
        self.strategy_results = strategy_results
        self.strategy_farm = strategy_farm  # Optionnel : instance de la strategy farm

    def run_research(self):
        patterns = PatternDiscovery(self.market_data).find_patterns()
        hypotheses = HypothesisGenerator(patterns).generate()
        recommendations = StrategyAdvisor(hypotheses, self.strategy_results).recommend()
        report = ReportGenerator(patterns, hypotheses, recommendations).generate()
        # Autoriser l'envoi automatique si strategy_farm est fourni
        if self.strategy_farm and recommendations:
            self.send_to_strategy_farm(recommendations)
        return report

    def send_to_strategy_farm(self, recommendations):
        """
        Envoie les recommandations à la strategy farm (pipeline d'intégration).
        """
        for rec in recommendations:
            # Ici, on suppose que la strategy_farm a une méthode 'add_strategy' ou similaire
            self.strategy_farm.add_strategy(rec)
        print(f"Recommandations envoyées à la strategy farm : {recommendations}")
