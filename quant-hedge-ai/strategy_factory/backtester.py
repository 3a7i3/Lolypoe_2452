from __future__ import annotations

from agents.quant.backtest_lab import BacktestLab


class FactoryBacktester:
    """Runs synthetic backtests for strategy candidates."""

    def __init__(self) -> None:
        self._lab = BacktestLab()

    def run(self, strategies: list[dict], candles: list[dict]) -> list[dict]:
        return [self._lab.run_backtest(strategy=s, data=candles) for s in strategies]
