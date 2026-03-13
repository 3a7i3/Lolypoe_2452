import QUANT_CORE

def test_dashboard_connector():
    qc = QUANT_CORE.QuantCore()
    dashboard_api = qc.interface.connect_dashboards()
    strategy = qc.strategy.generate()
    results = dashboard_api["run_strategy"](strategy)
    allocation = dashboard_api["get_allocation"]()
    print("Backtest Results:", results)
    print("Portfolio Allocation:", allocation)
    assert results is not None
    assert allocation is not None

def test_agent_connector():
    qc = QUANT_CORE.QuantCore()
    agent_api = qc.interface.connect_agents()
    strategy = agent_api["generate_strategy"]()
    validation = agent_api["validate_strategy"](strategy, {"metrics": {"sharpe": 1.2, "max_drawdown": 0.05, "win_ratio": 0.6}}, qc.risk)
    print("Strategy Validation:", validation)
    assert validation["approved"]

def test_telegram_connector():
    qc = QUANT_CORE.QuantCore()
    telegram_api = qc.interface.connect_telegram()
    telegram_api["send_alert"]("Test alert message")
    telegram_api["report_results"]({"result": "Test report"})
