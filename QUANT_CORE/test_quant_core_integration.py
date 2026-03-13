# Test d'intégration QUANT_CORE

from QUANT_CORE.strategy_lab import StrategyGenerator, generate_simple_strategy
from QUANT_CORE.risk_engine import evaluate_risk
from QUANT_CORE.execution_engine import execute_paper_orders
from QUANT_CORE.backtest_engine import backtest


def test_strategy_generation():
    generator = StrategyGenerator()
    population = generator.generate_population(size=5, markets=["BTC/USDT"], timeframes=["1h"])
    assert len(population) == 5
    print("Population générée:", population)


def test_simple_strategy():
    strat = generate_simple_strategy()
    assert "indicator" in strat
    print("Stratégie simple:", strat)


def test_risk_evaluation():
    result = evaluate_risk(0.15)
    assert result["status"] == "OK"
    print("Évaluation du risque:", result)


def test_execution():
    signals = [{"action": "BUY", "symbol": "BTC/USDT"}]
    orders = execute_paper_orders(signals, regime="bull")
    assert orders[0]["side"] == "BUY"
    print("Ordres exécutés:", orders)


def test_backtest():
    strat = {"indicator": "RSI", "period": 14}
    score = backtest(strat)
    assert isinstance(score, float)
    print("Score backtest:", score)


if __name__ == "__main__":
    test_strategy_generation()
    test_simple_strategy()
    test_risk_evaluation()
    test_execution()
    test_backtest()
