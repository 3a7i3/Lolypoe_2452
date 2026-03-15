
import sys
import os
import time
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_market_brain.market_brain_core import GlobalMarketBrain
from global_market_brain.crypto_analyzer import CryptoAnalyzer
from global_market_brain.stocks_analyzer import StocksAnalyzer
from global_market_brain.forex_analyzer import ForexAnalyzer
from global_market_brain.macro_analyzer import MacroAnalyzer
from global_market_brain.news_analyzer import NewsAnalyzer
from global_market_brain.social_analyzer import SocialAnalyzer

from quant_ai_brain.brain_core import QuantAIBrain
from quant_ai_brain.research_director import ResearchDirector
from quant_ai_brain.strategy_director import StrategyDirector
from quant_ai_brain.risk_director import RiskDirector
from quant_ai_brain.portfolio_director import PortfolioDirector
from quant_ai_brain.learning_director import LearningDirector
from quant_ai_brain.decision_engine import DecisionEngine

# Import simulated execution engine
from execution_system.simulated_execution_engine import SimulatedExecutionEngine

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("QuantAI")

# --- MODULES INSTANTIATION ---
crypto = CryptoAnalyzer()
stocks = StocksAnalyzer()
forex = ForexAnalyzer()
macro = MacroAnalyzer()
news = NewsAnalyzer()
social = SocialAnalyzer()
global_brain = GlobalMarketBrain()
global_brain.connect_modules(crypto, stocks, forex, macro, news, social)

research = ResearchDirector()
strategy = StrategyDirector()
risk = RiskDirector()
portfolio = PortfolioDirector()
learning = LearningDirector()
decision_engine = DecisionEngine()
quant_brain = QuantAIBrain()
quant_brain.connect_modules(research, strategy, risk, portfolio, learning)

execution_engine = SimulatedExecutionEngine()

# --- SIMULATION LOOP ---
for cycle in range(5):
    logger.info(f"\n=== CYCLE {cycle+1} ===")
    # 1. Données de marché simulées (varient à chaque cycle)
    market_data = {
        'crypto': {'bull_market': cycle % 2 == 0},
        'stocks': {'crash_risk': cycle % 3 == 0},
        'forex': {'macro_shift': cycle % 4 == 0},
        'macro': {'growth': cycle % 2 == 1},
        'news': {'bullish_news': cycle % 2 == 0},
        'social': {'hype': cycle % 3 == 1}
    }
    global_signals = global_brain.analyze(market_data)
    logger.info(f"Signaux globaux : {global_signals}")

    # 2. Décision de recherche
    if global_signals['stocks'] == 'bullish':
        market_state = 'TREND'
    elif global_signals['stocks'] == 'bearish':
        market_state = 'HIGH_VOLATILITY'
    else:
        market_state = 'STABLE'
    research_action = quant_brain.research.decide_research(market_state)
    logger.info(f"Action de recherche décidée : {research_action}")

    # 3. Génération de stratégies fictives (ranked)
    ranked_strategies = [
        {"name": f"strat_{i}", "score": 1.0 - i*0.07 + 0.02*cycle, "drawdown": 0.1 + i*0.04 + 0.01*cycle, "atout": "momentum" if i%2==0 else "mean-revert"}
        for i in range(15)
    ]
    logger.info(f"Stratégies classées : {[s['name'] for s in ranked_strategies]}")

    # 4. Sélection des meilleures stratégies
    selected = quant_brain.strategy.select_strategies(ranked_strategies)
    logger.info(f"Top stratégies sélectionnées : {[s['name'] for s in selected]}")

    # 5. Liste des moins performantes
    least_performant = ranked_strategies[-5:]
    logger.info(f"Moins performantes : {[s['name'] for s in least_performant]}")

    # 6. Allocation du capital
    allocation = quant_brain.portfolio.allocate(selected)
    logger.info(f"Allocation du capital : {allocation}")

    # 7. Évaluation du risque et filtrage
    accepted = []
    rejected = []
    for s in selected:
        verdict = quant_brain.risk.evaluate(s)
        if verdict == "accept":
            accepted.append(s)
        else:
            rejected.append(s)
    logger.info(f"Stratégies acceptées : {[s['name'] for s in accepted]}")
    logger.info(f"Stratégies rejetées (drawdown > 25%) : {[s['name'] for s in rejected]}")

    # 8. Exécution simulée et feedback réel
    if accepted:
        exec_alloc = {s["name"]: allocation[s["name"]] for s in accepted}
        exec_result = execution_engine.execute_trades(exec_alloc)
        logger.info(f"Résultat d'exécution simulée (PnL): {exec_result}")
        perf = execution_engine.get_performance()
    else:
        perf = {"profit": 0.0}
    insights = quant_brain.learning.learn(perf)
    logger.info(f"Insights d'apprentissage (feedback réel): {insights}")

    # 9. Suggestion d'analyse alternative si rejet
    if rejected:
        atouts_rejetes = set(s["atout"] for s in rejected)
        logger.info(f"Suggestion : explorer d'autres stratégies avec atouts différents de : {atouts_rejetes}")

    # 10. Test : si aucune stratégie n'est acceptée, relancer une recherche
    if not accepted:
        logger.warning("Aucune stratégie acceptée, relance d'une recherche alternative...")
        alt_action = quant_brain.research.decide_research("HIGH_VOLATILITY")
        logger.info(f"Nouvelle action de recherche : {alt_action}")


if rejected:
    atouts_rejetes = set(s["atout"] for s in rejected)
    print("\nSuggestion : explorer d'autres stratégies avec atouts différents de :", atouts_rejetes)

# 9. Test : si aucune stratégie n'est acceptée, relancer une recherche
if not accepted:
    print("\nAucune stratégie acceptée, relance d'une recherche alternative...")
    alt_action = quant_brain.research.decide_research("HIGH_VOLATILITY")
    print(f"Nouvelle action de recherche : {alt_action}")
