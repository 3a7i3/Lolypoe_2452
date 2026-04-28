"""Option Z — Historical Replay (paper trading sur données historiques).

Rejoue une séquence de bougies OHLCV en ordre chronologique pour simuler
un paper trading réaliste sans appel réseau. Chaque bougie est soumise
au pipeline complet (signal → SL check → exécution) comme en production.

Utile pour :
    - Valider la logique complète sur données réelles passées
    - Comparer différentes stratégies sur la même séquence
    - Diagnostiquer des comportements inattendus en rejouant un épisode

Workflow :
    replay = HistoricalReplay(candles=historical_data, strategy=my_strategy)
    result = replay.run()
    # → ReplayResult(equity_curve, trades, final_equity, sharpe, drawdown, ...)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Callable, Any


@dataclass
class ReplayTrade:
    """Un trade enregistré pendant le replay."""

    bar_index: int
    symbol: str
    action: str        # "BUY" | "SELL"
    price: float
    size: float
    pnl: float         # PnL de ce trade (0 pour BUY)
    reason: str        # "signal" | "stop_loss" | "take_profit" | "trailing_stop"


@dataclass
class ReplayResult:
    """Résultat complet d'un replay historique."""

    initial_equity: float
    final_equity: float
    realized_pnl: float
    equity_curve: list[float]
    trades: list[ReplayTrade]
    total_trades: int
    winning_trades: int
    win_rate: float
    sharpe: float
    max_drawdown: float
    data_mode: str = "replay"

    def as_dict(self) -> dict:
        return {
            "initial_equity": self.initial_equity,
            "final_equity": self.final_equity,
            "realized_pnl": self.realized_pnl,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": round(self.win_rate, 4),
            "sharpe": round(self.sharpe, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "equity_curve_len": len(self.equity_curve),
            "data_mode": self.data_mode,
        }


def _compute_sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    avg = mean(returns)
    variance = mean((r - avg) ** 2 for r in returns)
    vol = math.sqrt(variance) if variance > 0 else 1e-9
    return round((avg / vol) * math.sqrt(252), 4)


def _compute_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        peak = max(peak, eq)
        dd = (peak - eq) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    return round(max_dd, 6)


class HistoricalReplay:
    """Rejoue un historique de bougies via une fonction de signal simple.

    Args:
        candles:          liste de bougies {close, high, low, volume, symbol}.
        strategy:         dict stratégie (entry_indicator, threshold, sl_pct, tp_pct).
        initial_equity:   capital initial.
        position_size:    fraction du capital par trade (ex. 0.1 = 10%).
        symbol:           symbole (si les candles n'ont pas de champ "symbol").
        signal_fn:        fonction optionnelle ``(candles, i) → 'BUY'|'SELL'|'HOLD'``.
                          Si None, utilise un signal simple basé sur la direction.

    Raises:
        ValueError: si les paramètres sont invalides.
    """

    def __init__(
        self,
        candles: list[dict],
        strategy: dict | None = None,
        initial_equity: float = 10_000.0,
        position_size: float = 0.1,
        symbol: str = "BTC/USDT",
        signal_fn: Callable[[list[dict], int], str] | None = None,
    ) -> None:
        if not candles:
            raise ValueError("candles ne peut pas être vide")
        if initial_equity <= 0:
            raise ValueError(f"initial_equity doit être > 0, reçu: {initial_equity}")
        if not (0.0 < position_size <= 1.0):
            raise ValueError(f"position_size doit être dans (0, 1], reçu: {position_size}")

        self.candles = candles
        self.strategy = strategy or {}
        self.initial_equity = initial_equity
        self.position_size = position_size
        self.symbol = symbol
        self.signal_fn = signal_fn or self._default_signal

    def _default_signal(self, candles: list[dict], i: int) -> str:
        """Signal simple : BUY si la bougie monte, SELL si elle descend."""
        if i < 1:
            return "HOLD"
        _TREND = {"EMA", "MACD", "VWAP", "ADX", "SMA", "MOMENTUM"}
        indicator = str(self.strategy.get("entry_indicator", "EMA")).upper()
        prev_close = float(candles[i - 1]["close"])
        curr_close = float(candles[i]["close"])
        ret = (curr_close - prev_close) / prev_close if prev_close > 0 else 0.0
        threshold = float(self.strategy.get("threshold", 0.1)) / 100.0

        if indicator in _TREND:
            if ret > threshold:
                return "BUY"
            if ret < -threshold:
                return "SELL"
        else:  # mean-reversion
            if ret < -threshold:
                return "BUY"
            if ret > threshold:
                return "SELL"
        return "HOLD"

    def run(self) -> ReplayResult:
        """Exécute le replay complet.

        Returns:
            ReplayResult avec toutes les métriques et la courbe d'équité.
        """
        equity = self.initial_equity
        position = 0.0      # unités détenues
        entry_price = 0.0   # prix d'entrée courant
        equity_curve: list[float] = [equity]
        trades: list[ReplayTrade] = []
        returns: list[float] = []

        # Paramètres SL/TP de la stratégie
        sl_pct = float(self.strategy.get("sl_pct", 0.05))
        tp_pct = float(self.strategy.get("tp_pct", 0.10))
        sl_price = 0.0
        tp_price = 0.0

        for i, candle in enumerate(self.candles):
            price = float(candle["close"])
            sym = str(candle.get("symbol", self.symbol))

            prev_equity = equity

            # 1. Vérification SL/TP si position ouverte
            if position > 0 and entry_price > 0:
                if sl_price > 0 and price <= sl_price:
                    pnl = position * (price - entry_price)
                    equity += pnl
                    trades.append(ReplayTrade(
                        bar_index=i, symbol=sym, action="SELL",
                        price=price, size=position, pnl=pnl, reason="stop_loss"
                    ))
                    position = 0.0
                    entry_price = sl_price = tp_price = 0.0
                elif tp_price > 0 and price >= tp_price:
                    pnl = position * (price - entry_price)
                    equity += pnl
                    trades.append(ReplayTrade(
                        bar_index=i, symbol=sym, action="SELL",
                        price=price, size=position, pnl=pnl, reason="take_profit"
                    ))
                    position = 0.0
                    entry_price = sl_price = tp_price = 0.0

            # 2. Signal de la stratégie
            signal = self.signal_fn(self.candles, i)

            if signal == "BUY" and position == 0 and equity > 0:
                trade_value = equity * self.position_size
                units = trade_value / price
                position = units
                entry_price = price
                equity -= trade_value  # bloque le capital
                sl_price = price * (1 - sl_pct) if sl_pct > 0 else 0.0
                tp_price = price * (1 + tp_pct) if tp_pct > 0 else 0.0
                trades.append(ReplayTrade(
                    bar_index=i, symbol=sym, action="BUY",
                    price=price, size=units, pnl=0.0, reason="signal"
                ))

            elif signal == "SELL" and position > 0:
                pnl = position * (price - entry_price)
                equity += position * price  # récupère la valeur
                trades.append(ReplayTrade(
                    bar_index=i, symbol=sym, action="SELL",
                    price=price, size=position, pnl=pnl, reason="signal"
                ))
                position = 0.0
                entry_price = sl_price = tp_price = 0.0

            # Equity totale = cash + valeur mark-to-market de la position
            total_equity = equity + (position * price if position > 0 else 0.0)
            equity_curve.append(round(total_equity, 4))

            if i > 0:
                ret = (total_equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
                returns.append(ret)

        # Clôture forcée à la dernière bougie
        if position > 0:
            final_price = float(self.candles[-1]["close"])
            pnl = position * (final_price - entry_price)
            equity += position * final_price
            trades.append(ReplayTrade(
                bar_index=len(self.candles) - 1,
                symbol=self.symbol, action="SELL",
                price=final_price, size=position, pnl=pnl, reason="close_eod"
            ))

        final_equity = equity_curve[-1] if equity_curve else self.initial_equity
        realized_pnl = final_equity - self.initial_equity

        sell_trades = [t for t in trades if t.action == "SELL"]
        winning = [t for t in sell_trades if t.pnl > 0]
        win_rate = len(winning) / len(sell_trades) if sell_trades else 0.0

        return ReplayResult(
            initial_equity=self.initial_equity,
            final_equity=round(final_equity, 4),
            realized_pnl=round(realized_pnl, 4),
            equity_curve=equity_curve,
            trades=trades,
            total_trades=len(sell_trades),
            winning_trades=len(winning),
            win_rate=round(win_rate, 4),
            sharpe=_compute_sharpe(returns),
            max_drawdown=_compute_drawdown(equity_curve),
        )
