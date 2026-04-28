"""
Option AI — Backtester vectorisé numpy (simulation historique rapide).

Simule des stratégies de trading sur des données OHLCV historiques
en utilisant uniquement numpy pour la performance (pas de boucle Python).

Stratégies supportées :
- SMA crossover (fast/slow)
- RSI mean-reversion
- Bollinger Bands breakout

Usage :
    from agents.backtest.vectorized_backtester import VectorizedBacktester, BacktestConfig
    bt = VectorizedBacktester()
    result = bt.run(ohlcv=ohlcv_array, config=BacktestConfig(strategy="sma", fast=10, slow=30))
    print(result.sharpe, result.max_drawdown_pct)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class BacktestConfig:
    strategy: str = "sma"
    fast: int = 10
    slow: int = 30
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    bb_period: int = 20
    bb_std: float = 2.0
    initial_capital: float = 100_000.0
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005


@dataclass
class BacktestResult:
    strategy: str
    sharpe: float
    max_drawdown_pct: float
    win_rate: float
    total_return_pct: float
    n_trades: int
    equity_curve: np.ndarray
    config: BacktestConfig
    duration_bars: int


class VectorizedBacktester:
    """Backtester entièrement vectorisé (numpy-only, sans pandas)."""

    def run(self, ohlcv: np.ndarray, config: BacktestConfig) -> BacktestResult:
        """
        Lance le backtest sur un tableau OHLCV de forme (N, 5).

        Colonnes attendues : [open, high, low, close, volume].
        Retourne un BacktestResult vide (sharpe=0) si N est insuffisant.
        """
        ohlcv = np.asarray(ohlcv, dtype=float)
        close = ohlcv[:, 3]
        n = len(close)

        min_bars = max(config.slow, config.rsi_period, config.bb_period)
        if n < min_bars + 2:
            return BacktestResult(
                strategy=config.strategy,
                sharpe=0.0,
                max_drawdown_pct=0.0,
                win_rate=0.0,
                total_return_pct=0.0,
                n_trades=0,
                equity_curve=np.array([config.initial_capital]),
                config=config,
                duration_bars=n,
            )

        strategy = config.strategy.lower()
        if strategy == "sma":
            signals = self._sma_signals(close, config.fast, config.slow)
        elif strategy == "rsi":
            signals = self._rsi_signals(
                close, config.rsi_period, config.rsi_oversold, config.rsi_overbought
            )
        elif strategy in ("bb", "bollinger"):
            signals = self._bb_signals(close, config.bb_period, config.bb_std)
        else:
            raise ValueError(f"Stratégie inconnue : {config.strategy!r}. Choisir parmi : sma, rsi, bb")

        return self._simulate(close, signals, config)

    # ------------------------------------------------------------------
    # Signal generators
    # ------------------------------------------------------------------

    def _sma(self, arr: np.ndarray, window: int) -> np.ndarray:
        """Moyenne mobile simple via np.convolve. Retourne NaN pour les premières valeurs."""
        kernel = np.ones(window) / window
        conv = np.convolve(arr, kernel, mode="full")[: len(arr)]
        conv[: window - 1] = np.nan
        return conv

    def _sma_signals(self, close: np.ndarray, fast: int, slow: int) -> np.ndarray:
        """
        Croise la SMA rapide et la SMA lente.
        Signal +1 quand fast > slow, -1 quand fast < slow, 0 sinon (NaN).
        Décalé d'une barre pour éviter le look-ahead bias.
        """
        sma_fast = self._sma(close, fast)
        sma_slow = self._sma(close, slow)

        raw = np.where(sma_fast > sma_slow, 1.0, np.where(sma_fast < sma_slow, -1.0, 0.0))
        # Décalage d'une barre (look-ahead protection)
        signals = np.empty_like(raw)
        signals[0] = 0.0
        signals[1:] = raw[:-1]
        # Masquer les barres non définies (NaN dans les SMAs)
        signals[: slow] = 0.0
        return signals

    def _rsi_signals(
        self,
        close: np.ndarray,
        period: int,
        oversold: float,
        overbought: float,
    ) -> np.ndarray:
        """
        RSI via Wilder EMA.
        +1 (achat) quand RSI < oversold, -1 (vente) quand RSI > overbought, 0 sinon.
        Décalé d'une barre.
        """
        delta = np.diff(close, prepend=close[0])
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)

        # Wilder smoothing (EWM avec alpha=1/period)
        alpha = 1.0 / period
        avg_gain = np.zeros(len(close))
        avg_loss = np.zeros(len(close))
        avg_gain[period] = np.mean(gain[1 : period + 1])
        avg_loss[period] = np.mean(loss[1 : period + 1])
        for i in range(period + 1, len(close)):
            avg_gain[i] = avg_gain[i - 1] * (1 - alpha) + gain[i] * alpha
            avg_loss[i] = avg_loss[i - 1] * (1 - alpha) + loss[i] * alpha

        rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
        rsi = np.where(avg_loss == 0, 100.0, 100.0 - 100.0 / (1.0 + rs))
        rsi[: period] = np.nan

        raw = np.where(rsi < oversold, 1.0, np.where(rsi > overbought, -1.0, 0.0))
        signals = np.empty_like(raw)
        signals[0] = 0.0
        signals[1:] = raw[:-1]
        signals[: period + 1] = 0.0
        return signals

    def _bb_signals(self, close: np.ndarray, period: int, std: float) -> np.ndarray:
        """
        Bollinger Bands breakout.
        +1 quand close > upper band (breakout haussier), -1 quand close < lower band.
        Décalé d'une barre.
        """
        n = len(close)
        mid = np.full(n, np.nan)
        band = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = close[i - period + 1 : i + 1]
            mid[i] = window.mean()
            band[i] = window.std(ddof=1)

        upper = mid + std * band
        lower = mid - std * band

        raw = np.where(close > upper, 1.0, np.where(close < lower, -1.0, 0.0))
        signals = np.empty_like(raw)
        signals[0] = 0.0
        signals[1:] = raw[:-1]
        signals[: period] = 0.0
        return signals

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def _simulate(
        self, close: np.ndarray, signals: np.ndarray, config: BacktestConfig
    ) -> BacktestResult:
        """
        Simule le P&L bar par bar de manière vectorisée.

        Logique :
        - Position = signal (long=+1, short=-1, flat=0)
        - Changement de position → trade → coût commission + slippage
        - Equity curve construite via np.cumprod sur les rendements ajustés
        """
        n = len(close)
        cost_rate = config.commission_pct + config.slippage_pct  # cost per side

        # Rendements bruts bar à bar
        bar_returns = np.empty(n)
        bar_returns[0] = 0.0
        bar_returns[1:] = close[1:] / close[:-1] - 1.0

        # Rendements de position (signal décalé = position tenue sur la barre)
        position_returns = signals * bar_returns

        # Coût à chaque changement de position
        position_changes = np.diff(signals, prepend=0.0)
        trade_mask = position_changes != 0.0
        cost_array = np.where(trade_mask, cost_rate, 0.0)

        # Rendements nets
        net_returns = position_returns - cost_array

        # Equity curve via cumprod
        equity = config.initial_capital * np.cumprod(1.0 + net_returns)

        # Reconstruction des trades pour stats
        trade_indices = np.where(trade_mask)[0]
        trade_pnls = np.array([], dtype=float)

        if len(trade_indices) >= 2:
            trade_pnls_list = []
            for k in range(len(trade_indices) - 1):
                entry_idx = trade_indices[k]
                exit_idx = trade_indices[k + 1]
                if entry_idx < n and exit_idx < n:
                    trade_return = np.prod(1.0 + net_returns[entry_idx:exit_idx]) - 1.0
                    trade_pnls_list.append(trade_return)
            # Dernière position ouverte jusqu'à la fin
            last_idx = trade_indices[-1]
            if last_idx < n:
                trade_return = np.prod(1.0 + net_returns[last_idx:]) - 1.0
                trade_pnls_list.append(trade_return)
            trade_pnls = np.array(trade_pnls_list)

        n_trades = len(trade_indices)
        sharpe = self._compute_sharpe(net_returns) if n_trades >= 2 else 0.0
        win_rate = self._compute_win_rate(trade_pnls) if len(trade_pnls) >= 2 else 0.0
        max_dd = self._compute_max_drawdown(equity)
        total_return_pct = (equity[-1] / config.initial_capital - 1.0) * 100.0

        return BacktestResult(
            strategy=config.strategy,
            sharpe=sharpe,
            max_drawdown_pct=max_dd,
            win_rate=win_rate,
            total_return_pct=total_return_pct,
            n_trades=n_trades,
            equity_curve=equity,
            config=config,
            duration_bars=n,
        )

    # ------------------------------------------------------------------
    # Métriques
    # ------------------------------------------------------------------

    def _compute_sharpe(self, returns: np.ndarray, periods_per_year: int = 252) -> float:
        """Sharpe ratio annualisé (rendements journaliers)."""
        std = returns.std()
        if std == 0.0:
            return 0.0
        return float(returns.mean() / std * np.sqrt(periods_per_year))

    def _compute_max_drawdown(self, equity: np.ndarray) -> float:
        """Max drawdown en pourcentage (valeur positive)."""
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        return float(-drawdown.min() * 100.0)

    def _compute_win_rate(self, trade_pnls: np.ndarray) -> float:
        """Proportion de trades gagnants (P&L > 0)."""
        if len(trade_pnls) == 0:
            return 0.0
        return float(np.mean(trade_pnls > 0))
