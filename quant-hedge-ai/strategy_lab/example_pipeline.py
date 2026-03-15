# example_pipeline.py
"""
Exemple d'intégration du pipeline de découverte de stratégies.
"""
from generator import StrategyGenerator
from parameter_space import ParameterSpace
from templates import StrategyTemplate
from signal_builder import SignalBuilder
from backtest_launcher import BacktestLauncher
from ranker import StrategyRanker
from strategy_db import StrategyDatabase

# 1. Génération d'une stratégie simple
features = ['momentum_14']
templates = ['momentum']
generator = StrategyGenerator(features, templates)
strategy_ideas = [('momentum_14', 'momentum')]

# 2. Espace de paramètres (exemple pour momentum)
param_space = ParameterSpace('momentum')
params_grid = [{'threshold': 0.03}]

# 3. Application du template
logic = "IF momentum_14 > {threshold}: BUY ELSE: HOLD"
template = StrategyTemplate('momentum', logic)

# 4. Construction du signal (mock data)
data = {'momentum_14': [0.01, 0.04, 0.02, 0.05]}
signal_builder = SignalBuilder(template, params_grid[0])
signals = ['HOLD' if v <= 0.03 else 'BUY' for v in data['momentum_14']]

# 5. Backtest (mock)
backtest_engine = None  # À remplacer par un vrai moteur
backtester = BacktestLauncher(backtest_engine)
metrics = {'return': 0.85, 'sharpe': 1.8, 'drawdown': 0.12, 'win_rate': 0.65}

# 6. Ranking
weights = {'sharpe': 0.4, 'drawdown': 0.3, 'return': 0.2, 'win_rate': 0.1}
ranker = StrategyRanker(weights)
score = 0.4*metrics['sharpe'] - 0.3*metrics['drawdown'] + 0.2*metrics['return'] + 0.1*metrics['win_rate']

# 7. Sauvegarde
strategy_db = StrategyDatabase('strategies.db')
strategy_id = 'momentum_14_thr_0.03'
strategy_db.save(strategy_id, params_grid[0], metrics, score)

print(f"Stratégie: {strategy_id}\nSignals: {signals}\nMetrics: {metrics}\nScore: {score}")
