import QUANT_CORE

def test_backtest_and_validation():
    qc = QUANT_CORE.QuantCore()
    strategy = qc.strategy.generate()
    results = qc.run_backtest_and_validate(strategy)
    assert results is not None, "Strategy should be approved and backtested"

def test_portfolio_allocation():
    qc = QUANT_CORE.QuantCore()
    allocation = qc.allocate_portfolio()
    assert "allocation" in allocation, "Portfolio allocation should return allocation dict"

def test_bot_doctor_block():
    qc = QUANT_CORE.QuantCore()
    # Simulate a strategy that fails Bot Doctor
    class FailingRiskManager:
        def validate(self, strategy):
            return {"approved": False, "reason": "Risk limit exceeded"}
    qc.risk = FailingRiskManager()
    strategy = qc.strategy.generate()
    results = qc.run_backtest_and_validate(strategy)
    assert results is None, "Strategy should be blocked by Bot Doctor"
