from __future__ import annotations

from quant_hedge_ai.engine.decision_engine import DecisionEngine



def test_should_trade_false_when_no_strategy() -> None:
    engine = DecisionEngine()
    assert engine.should_trade(None, regime="bull", whale_alerts=[]) is False



def test_should_trade_false_in_flash_crash() -> None:
    engine = DecisionEngine()
    best = {"sharpe": 3.0, "drawdown": 0.05}
    assert engine.should_trade(best, regime="flash_crash", whale_alerts=[]) is False



def test_should_trade_false_when_too_many_whale_alerts() -> None:
    engine = DecisionEngine()
    best = {"sharpe": 3.0, "drawdown": 0.05}
    alerts = ["a", "b", "c"]
    assert engine.should_trade(best, regime="bull", whale_alerts=alerts) is False



def test_should_trade_true_with_good_metrics() -> None:
    engine = DecisionEngine()
    best = {"sharpe": 2.5, "drawdown": 0.08}
    assert engine.should_trade(best, regime="bull", whale_alerts=["a"]) is True



def test_should_trade_false_with_low_sharpe_or_high_drawdown() -> None:
    engine = DecisionEngine()
    low_sharpe = {"sharpe": 1.9, "drawdown": 0.05}
    high_dd = {"sharpe": 3.0, "drawdown": 0.15}
    assert engine.should_trade(low_sharpe, regime="bull", whale_alerts=[]) is False
    assert engine.should_trade(high_dd, regime="bull", whale_alerts=[]) is False



def test_compute_risk_limits_scales_with_volatility() -> None:
    engine = DecisionEngine()
    limits = engine.compute_risk_limits(portfolio_vol=0.04, max_risk=0.02)

    assert limits["max_position_size"] == 0.5
    assert limits["stop_loss_pct"] == 0.04
    assert limits["take_profit_pct"] == 0.08


def test_configurable_thresholds_allow_trade_when_relaxed() -> None:
    engine = DecisionEngine(min_sharpe=1.0, max_drawdown_for_trade=0.2, whale_block_threshold=5)
    best = {"sharpe": 1.5, "drawdown": 0.15}
    alerts = ["a", "b", "c"]
    assert engine.should_trade(best, regime="bull", whale_alerts=alerts) is True


def test_configurable_thresholds_block_trade_when_strict() -> None:
    engine = DecisionEngine(min_sharpe=3.0, max_drawdown_for_trade=0.05, whale_block_threshold=0)
    best = {"sharpe": 2.9, "drawdown": 0.04}
    alerts = ["a"]
    assert engine.should_trade(best, regime="bull", whale_alerts=alerts) is False
