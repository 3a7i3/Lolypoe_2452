import pandas as pd
from market_analyst_ai import MarketAnalystAI
from strategy_scientist_ai import StrategyScientistAI
from backtest_engineer_ai import BacktestEngineerAI
from risk_analyst_ai import RiskAnalystAI
from portfolio_manager_ai import PortfolioManagerAI
from execution_trader_ai import ExecutionTraderAI
from chief_research_ai import ChiefResearchAI

# Génère des données fictives pour le test
def generate_fake_market_data():
    data = {
        'close': pd.Series([100 + i + (i%5)*2 for i in range(300)])
    }
    return pd.DataFrame(data)

def test_full_cycle():
    market_data = generate_fake_market_data()
    agents = {
        'market_analyst': MarketAnalystAI(),
        'strategy_scientist': StrategyScientistAI(),
        'backtest_engineer': BacktestEngineerAI(),
        'risk_analyst': RiskAnalystAI(),
        'portfolio_manager': PortfolioManagerAI(),
        'execution_trader': ExecutionTraderAI(),
    }
    chief = ChiefResearchAI(agents)
    results = chief.run_cycle(market_data)
    print('Résultats du cycle complet:')
    for k, v in results.items():
        print(f'{k}:', str(v)[:500])
    assert 'market_report' in results
    assert 'strategies' in results
    assert 'backtest' in results
    assert 'risk' in results
    assert 'allocation' in results
    assert 'execution' in results
    print('Test du cycle complet: OK')

if __name__ == '__main__':
    test_full_cycle()
