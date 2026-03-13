"""Backtester with realistic execution, dynamic sizing, and anti-overfit checks."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Backtester:
    """Advanced backtesting engine for single or multi-strategy experiments."""

    def __init__(self, initial_capital: float = 10000.0, fee: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = float(initial_capital)
        self.fee = float(fee)
        self.slippage = float(slippage)
        self.results: List[Dict[str, Any]] = []

    def backtest(
        self,
        prices: np.ndarray,
        signals: np.ndarray,
        max_position: float = 0.10,
        risk_per_trade: float = 0.01,
        max_drawdown_stop: float = 0.20,
    ) -> Dict[str, Any]:
        """Run realistic long-only backtest with dynamic position sizing."""
        prices = np.asarray(prices, dtype=float)
        signals = np.asarray(signals, dtype=float)
        if prices.size == 0:
            return {
                "total_return": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "calmar": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "num_trades": 0,
                "final_value": self.initial_capital,
                "trades": [],
            }

        cash = self.initial_capital
        shares = 0.0
        entry_price = 0.0
        equity_curve = [self.initial_capital]
        trades: List[Dict[str, float | int | str]] = []
        closed_pnls: List[float] = []

        for i, price in enumerate(prices):
            signal = signals[i] if i < signals.size else 0.0

            equity_now = cash + shares * price
            dd_now = self.current_drawdown(np.array(equity_curve, dtype=float))
            if dd_now >= max_drawdown_stop and shares > 0:
                sell_px = price * (1.0 - self.slippage)
                proceeds = shares * sell_px * (1.0 - self.fee)
                pnl = proceeds - (shares * entry_price)
                cash += proceeds
                trades.append({"type": "FORCED_EXIT", "price": float(sell_px), "shares": float(shares), "pnl": float(pnl), "step": i})
                closed_pnls.append(float(pnl))
                shares = 0.0

            if signal > 0 and shares == 0:
                position_fraction = self.dynamic_position_size(
                    prices=prices[: i + 1],
                    risk_per_trade=risk_per_trade,
                    max_position=max_position,
                    current_drawdown=dd_now,
                    max_drawdown=max_drawdown_stop,
                )
                buy_px = price * (1.0 + self.slippage)
                notional = cash * position_fraction
                if notional > 0:
                    qty = (notional * (1.0 - self.fee)) / buy_px
                    cash -= qty * buy_px
                    shares = qty
                    entry_price = buy_px
                    trades.append({"type": "BUY", "price": float(buy_px), "shares": float(qty), "step": i})

            elif signal < 0 and shares > 0:
                sell_px = price * (1.0 - self.slippage)
                proceeds = shares * sell_px * (1.0 - self.fee)
                pnl = proceeds - (shares * entry_price)
                cash += proceeds
                trades.append({"type": "SELL", "price": float(sell_px), "shares": float(shares), "pnl": float(pnl), "step": i})
                closed_pnls.append(float(pnl))
                shares = 0.0

            equity_curve.append(cash + shares * price)

        final_value = cash + shares * prices[-1]
        if shares > 0:
            pnl = (shares * prices[-1] * (1.0 - self.fee)) - (shares * entry_price)
            closed_pnls.append(float(pnl))

        equity_array = np.array(equity_curve, dtype=float)
        returns = np.diff(equity_array) / np.maximum(equity_array[:-1], 1e-12)
        metrics = self._compute_metrics(returns=returns, equity_curve=equity_array, closed_pnls=closed_pnls)
        metrics.update(
            {
                "final_value": float(final_value),
                "total_return": float((final_value - self.initial_capital) / self.initial_capital),
                "num_trades": int(sum(1 for t in trades if t["type"] in {"SELL", "FORCED_EXIT"})),
                "trades": trades,
                "equity_curve": equity_array,
            }
        )

        self.results.append(metrics)
        return metrics

    def dynamic_position_size(
        self,
        prices: np.ndarray,
        risk_per_trade: float,
        max_position: float,
        current_drawdown: float,
        max_drawdown: float,
    ) -> float:
        """Volatility-targeted sizing with drawdown throttle."""
        if prices.size < 10:
            return float(min(max_position, risk_per_trade * 5.0))

        rets = np.diff(prices) / np.maximum(prices[:-1], 1e-12)
        vol = float(np.std(rets) * np.sqrt(252))
        if vol <= 1e-9:
            base_size = max_position
        else:
            base_size = risk_per_trade / vol

        dd_ratio = current_drawdown / max(max_drawdown, 1e-9)
        throttle = 1.0
        if dd_ratio > 0.5:
            throttle = max(0.25, 1.0 - dd_ratio)

        return float(np.clip(base_size * throttle, 0.01, max_position))

    def current_drawdown(self, equity_curve: np.ndarray) -> float:
        if equity_curve.size < 2:
            return 0.0
        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (running_max - equity_curve) / np.maximum(running_max, 1e-12)
        return float(np.max(drawdowns))

    def _compute_metrics(self, returns: np.ndarray, equity_curve: np.ndarray, closed_pnls: List[float]) -> Dict[str, float]:
        if returns.size == 0:
            return {"sharpe": 0.0, "sortino": 0.0, "calmar": 0.0, "max_drawdown": 0.0, "win_rate": 0.0}

        mean_ret = float(np.mean(returns))
        std_ret = float(np.std(returns))
        downside = returns[returns < 0]
        downside_std = float(np.std(downside)) if downside.size else 0.0

        sharpe = (mean_ret / std_ret) * np.sqrt(252) if std_ret > 0 else 0.0
        sortino = (mean_ret / downside_std) * np.sqrt(252) if downside_std > 0 else sharpe
        max_dd = self.current_drawdown(equity_curve)
        cagr = (equity_curve[-1] / equity_curve[0]) ** (252.0 / max(len(returns), 1)) - 1.0
        calmar = float(cagr / max(max_dd, 1e-9)) if max_dd > 0 else float(cagr)

        win_rate = 0.0
        if closed_pnls:
            win_rate = float(sum(1 for p in closed_pnls if p > 0) / len(closed_pnls))

        return {
            "sharpe": float(sharpe),
            "sortino": float(sortino),
            "calmar": float(calmar),
            "max_drawdown": float(max_dd),
            "win_rate": float(win_rate),
        }

    def walk_forward(
        self,
        prices: np.ndarray,
        strategy_func: Callable[[np.ndarray], np.ndarray],
        train_size: int = 250,
        test_size: int = 50,
    ) -> Dict[str, Any]:
        """Walk-forward validation to reduce in-sample bias."""
        results: List[Dict[str, Any]] = []
        prices = np.asarray(prices, dtype=float)

        for start in range(0, max(0, prices.size - train_size - test_size + 1), test_size):
            train_data = prices[start : start + train_size]
            test_data = prices[start + train_size : start + train_size + test_size]
            if test_data.size == 0:
                continue

            combined = np.concatenate([train_data, test_data])
            combined_signals = strategy_func(combined)
            test_signals = combined_signals[-test_data.size :]
            metrics = self.backtest(test_data, test_signals)
            results.append(metrics)

        if not results:
            return {"average_sharpe": 0.0, "average_return": 0.0, "average_max_dd": 0.0, "results": []}

        return {
            "average_sharpe": float(np.mean([r["sharpe"] for r in results])),
            "average_return": float(np.mean([r["total_return"] for r in results])),
            "average_max_dd": float(np.mean([r["max_drawdown"] for r in results])),
            "results": results,
        }

    def detect_overfitting(self, train_metrics: Dict[str, float], test_metrics: Dict[str, float]) -> float:
        """Return an overfitting score in [0, 1] based on performance decay."""
        train_sharpe = float(train_metrics.get("sharpe", 0.0))
        test_sharpe = float(test_metrics.get("sharpe", 0.0))
        train_return = float(train_metrics.get("total_return", 0.0))
        test_return = float(test_metrics.get("total_return", 0.0))

        sharpe_gap = max(0.0, train_sharpe - test_sharpe)
        return_gap = max(0.0, train_return - test_return)
        raw = 0.6 * (sharpe_gap / max(abs(train_sharpe), 1.0)) + 0.4 * (return_gap / max(abs(train_return), 1.0))
        return float(np.clip(raw, 0.0, 1.0))

    def monte_carlo(self, returns: np.ndarray, num_simulations: int = 1000, num_periods: int = 252) -> Dict[str, float]:
        simulations = []
        returns = np.asarray(returns, dtype=float)
        if returns.size == 0:
            return {
                "mean_return": 0.0,
                "std_return": 0.0,
                "var_95": 0.0,
                "var_99": 0.0,
                "best_case": 0.0,
                "worst_case": 0.0,
            }

        for _ in range(num_simulations):
            sim_returns = np.random.choice(returns, num_periods, replace=True)
            simulations.append(float(np.prod(1 + sim_returns) - 1))

        sims = np.array(simulations, dtype=float)
        return {
            "mean_return": float(np.mean(sims)),
            "std_return": float(np.std(sims)),
            "var_95": float(np.percentile(sims, 5)),
            "var_99": float(np.percentile(sims, 1)),
            "best_case": float(np.max(sims)),
            "worst_case": float(np.min(sims)),
        }

    def backtest_multi_strategy(
        self,
        price_map: Dict[str, np.ndarray],
        signal_map: Dict[str, np.ndarray],
        strategy_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Aggregate multiple strategy streams across markets/timeframes."""
        metrics_per_strategy: Dict[str, Dict[str, Any]] = {}
        weighted_returns = []

        for strategy_id, prices in price_map.items():
            signals = signal_map.get(strategy_id)
            if signals is None:
                continue
            metrics = self.backtest(prices=prices, signals=signals)
            metrics_per_strategy[strategy_id] = metrics
            weighted_returns.append(float(metrics["total_return"]) * float(strategy_weights.get(strategy_id, 0.0)))

        total_weight = sum(strategy_weights.values()) or 1.0
        normalized_return = sum(weighted_returns) / total_weight
        sharpe_values = [float(m["sharpe"]) for m in metrics_per_strategy.values()]
        dd_values = [float(m["max_drawdown"]) for m in metrics_per_strategy.values()]

        return {
            "portfolio_return": float(normalized_return),
            "portfolio_sharpe": float(np.mean(sharpe_values)) if sharpe_values else 0.0,
            "portfolio_max_drawdown": float(np.max(dd_values)) if dd_values else 0.0,
            "strategies": metrics_per_strategy,
        }

    def get_results_summary(self) -> pd.DataFrame:
        if not self.results:
            return pd.DataFrame()
        return pd.DataFrame(self.results)
