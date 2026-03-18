"""
Pipeline autonome AI Quant Lab V4
Orchestration complète : collecte, features, stratégie, validation, exécution, monitoring
"""

from quant_core.data.collector import DataCollector
from quant_core.features.engineer import FeatureEngineer
from ai.strategy_discovery import StrategyDiscovery
from ai.strategy_evolution import StrategyEvolution
from supervision.bot_doctor import BotDoctor
from quant_core.portfolio.allocator import PortfolioManager
from quant_core.risk.manager import RiskEngine
from memecoin_alpha.sniper_bot import SniperBot
from supervision.alert_manager import AlertManager
from supervision.telegram_bot import TelegramIntegration
from supervision.dashboard_web import render_dashboard

"""
Pipeline autonome AI Quant Lab V4

Étapes principales :
1. DataCollector : collecte les données de marché (prix, volume, orderbook, funding)
2. FeatureEngineer : calcule les features avancées (momentum, volatilité, etc)
3. StrategyDiscovery : génère et score des stratégies candidates
4. StrategyEvolution : améliore les stratégies par évolution génétique
5. BotDoctor : valide la robustesse et la conformité des stratégies
6. PortfolioManager & RiskEngine : alloue le capital, gère le risque
7. SniperBot : exécute les ordres (paper/live), gère slippage/frais
8. AlertManager, Dashboard, Telegram : monitoring et alertes temps réel
"""

# ------------------------------
# Config Telegram / AlertManager
# ------------------------------
TELEGRAM_TOKEN = "TON_TELEGRAM_BOT_TOKEN"
CHAT_ID = "TON_CHAT_ID"
tg_bot = TelegramIntegration(TELEGRAM_TOKEN, CHAT_ID)
alerts = AlertManager(telegram_bot=tg_bot)

# ------------------------------
# Modules principaux
# ------------------------------
data_collector = DataCollector(alerts=alerts)
feature_engineer = FeatureEngineer(alerts=alerts)
strategy_discovery = StrategyDiscovery(alerts=alerts)
strategy_evolution = StrategyEvolution(alerts=alerts)
bot_doctor = BotDoctor(alerts=alerts)
portfolio_manager = PortfolioManager(alerts=alerts)
risk_engine = RiskEngine(alerts=alerts)
sniper_bot = SniperBot(alerts=alerts, telegram_bot=tg_bot)

# ------------------------------
# Boucle principale du pipeline
# ------------------------------
def run_pipeline(iterations=10, mode="paper"):
    """
    Boucle principale du pipeline autonome.
    Args:
        iterations (int): nombre de cycles à exécuter
        mode (str): 'paper' ou 'live'
    """
    for i in range(iterations):
        try:
            # 1️⃣ Collecte de données
            data = data_collector.collect()
            # 2️⃣ Feature Engineering
            features = feature_engineer.compute(data)
            # 3️⃣ Découverte de stratégies
            strategies = strategy_discovery.generate(features)
            # 4️⃣ Evolution des stratégies
            strategies = strategy_evolution.evolve(strategies)
            # 5️⃣ Bot Doctor
            valid_strategies = bot_doctor.validate(strategies)
            # 6️⃣ Gestion du portefeuille & risque
            portfolio = portfolio_manager.allocate(valid_strategies)
            risk_engine.apply_rules(portfolio)
            # 7️⃣ Exécution (Sniper / trading)
            sniper_bot.execute(valid_strategies, mode=mode)
        except Exception as e:
            alerts.add_alert(f"Pipeline error: {str(e)}", severity="ERROR")

# ------------------------------
# Monitoring & Dashboard
# ------------------------------
if __name__ == "__main__":
    """
    Exemple d’exécution du pipeline autonome avec monitoring dashboard et Telegram.
    """
    run_pipeline()
    # Affichage dashboard Streamlit (exemple)
    strategies = [{"name": "Momentum", "score": 0.92}]
    portfolio = {"total_capital": 100000, "allocations": {"Momentum": 50000}}
    trades = [{"token": "TOKEN1", "type": "buy", "amount": 1000}]
    render_dashboard(strategies, portfolio, trades, alerts.get_recent_alerts())
    # Lancer Telegram Bot en parallèle
    tg_bot.start_bot()
