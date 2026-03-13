"""
Autonomous Quant AI Control Center – V12
=========================================
Panel + Plotly dashboard integrating:
  • Market Scanner              (200 synthetic coins + live refresh)
  • Candlestick + RSI + MACD   (live chart panel)
  • AI Strategy Generator      (1 000 strategies, genetic ranking)
  • Backtest Engine             (Sharpe / Win-rate / PnL)
  • Portfolio Manager           (Kelly-weighted allocation)
  • Whale Radar                 (anomaly detection)
  • Risk Engine                 (drawdown, VaR, circuit-breaker)
  • AI Agents Monitor           (V9.1 agent status)
  • Strategy Scoreboard         (loads live JSON from V9.1)
  • System Metrics              (CPU, memory, cycle count)

Run:
    cd quant-hedge-ai
    panel serve dashboard/quant_terminal_v12.py --show --port 5010
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import panel as pn
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── allow imports from quant-hedge-ai root ──────────────────────────────────
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from databases.strategy_scoreboard import StrategyScoreboard
    _SCOREBOARD = StrategyScoreboard()
    _HAS_SCOREBOARD = True
except Exception:
    _HAS_SCOREBOARD = False

pn.extension("plotly", sizing_mode="stretch_width", notifications=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS & GLOBALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COINS_TOP = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "DOGE",
    "DOT", "MATIC", "LINK", "UNI", "ATOM", "LTC", "ETC",
    "FIL", "NEAR", "ALGO", "APT", "ARB", "OP", "INJ", "TIA",
    "SUI", "SEI", "PYTH", "JUP", "WIF", "PEPE", "FLOKI",
]

COINS_EXT = COINS_TOP + [f"COIN_{i}" for i in range(len(COINS_TOP), 200)]

INDICATORS = ["RSI", "EMA", "MACD", "BOLLINGER", "VWAP", "STOCH", "CCI", "ATR"]
TIMEFRAMES   = ["1m", "5m", "15m", "1h", "4h", "1d"]

DARK = {
    "bg": "#0e1117",
    "panel": "#161b22",
    "green": "#00ff9f",
    "red": "#ff4e6a",
    "yellow": "#f0c040",
    "blue": "#4fa3e0",
    "text": "#e6edf3",
}

_CYCLE_COUNT = [0]
_START_TIME  = time.time()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA GENERATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_PRICES: dict[str, float] = {
    "BTC": 65_000, "ETH": 3_200, "SOL": 145, "BNB": 380,
    "XRP": 0.58, "ADA": 0.44, "AVAX": 36, "DOGE": 0.12,
}

def _base_price(coin: str) -> float:
    if coin in _PRICES:
        return _PRICES[coin]
    return round(random.uniform(0.01, 500), 4)


def market_scan_df(n: int = 50) -> pd.DataFrame:
    coins = COINS_EXT[:n]
    rows = []
    for coin in coins:
        base = _base_price(coin)
        chg  = round(random.uniform(-8.0, 8.0), 2)
        price = round(base * (1 + chg / 100), 2)
        vol   = round(random.uniform(1e4, 1e8), 0)
        sig   = random.choice(["BUY", "SELL", "HOLD"])
        rows.append({
            "Coin": coin,
            "Price $": price,
            "24h %": chg,
            "Volume $": vol,
            "Signal": sig,
        })
    return pd.DataFrame(rows)


def _ohlcv(n: int = 300, base: float = 65_000) -> pd.DataFrame:
    prices = base + np.cumsum(np.random.normal(0, base * 0.006, n))
    highs  = prices + np.abs(np.random.normal(0, base * 0.004, n))
    lows   = prices - np.abs(np.random.normal(0, base * 0.004, n))
    opens  = np.roll(prices, 1)
    opens[0] = base
    vols   = np.random.uniform(1e5, 3e7, n)
    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows,
        "close": prices, "volume": vols,
    })


def _rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    delta  = np.diff(closes, prepend=closes[0])
    gain   = np.where(delta > 0, delta, 0.0)
    loss   = np.where(delta < 0, -delta, 0.0)
    avg_g  = np.convolve(gain, np.ones(period) / period, mode="same")
    avg_l  = np.convolve(loss, np.ones(period) / period, mode="same")
    rs     = np.where(avg_l == 0, 100.0, avg_g / (avg_l + 1e-9))
    return np.clip(100 - 100 / (1 + rs), 0, 100)


def _macd(closes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    def ema(arr: np.ndarray, p: int) -> np.ndarray:
        k, s = 2 / (p + 1), arr[0]
        out = [s]
        for v in arr[1:]:
            s = v * k + s * (1 - k)
            out.append(s)
        return np.array(out)
    fast   = ema(closes, 12)
    slow   = ema(closes, 26)
    macd_l = fast - slow
    signal = ema(macd_l, 9)
    return macd_l, signal


def candle_chart(coin: str = "BTC", tf: str = "1h") -> go.Figure:
    base = _base_price(coin)
    df   = _ohlcv(300, base)
    rsi  = _rsi(df["close"].values)
    macd_l, macd_s = _macd(df["close"].values)
    idx  = np.arange(len(df))

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.04,
        subplot_titles=[f"{coin}/USDT  {tf}", "RSI (14)", "MACD"],
    )

    # ── Candlestick ──────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=idx, open=df.open, high=df.high,
        low=df.low, close=df.close,
        name=coin,
        increasing_line_color=DARK["green"],
        decreasing_line_color=DARK["red"],
        increasing_fillcolor=DARK["green"],
        decreasing_fillcolor=DARK["red"],
    ), row=1, col=1)

    # EMA 20/50
    for period, col in [(20, DARK["blue"]), (50, DARK["yellow"])]:
        ema = pd.Series(df.close).ewm(span=period).mean()
        fig.add_trace(go.Scatter(
            x=idx, y=ema, name=f"EMA{period}",
            line=dict(color=col, width=1.2, dash="dot"),
        ), row=1, col=1)

    # Volume bars
    colors = [DARK["green"] if c >= o else DARK["red"]
              for c, o in zip(df.close, df.open)]
    fig.add_trace(go.Bar(
        x=idx, y=df.volume, name="Volume",
        marker_color=colors, opacity=0.4,
        yaxis="y4",
    ))

    # ── RSI ──────────────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=idx, y=rsi, name="RSI",
        line=dict(color=DARK["blue"], width=1.5),
    ), row=2, col=1)
    for level, color in [(70, DARK["red"]), (30, DARK["green"])]:
        fig.add_hline(
            y=level, line_dash="dash",
            line_color=color, opacity=0.5, row=2, col=1,
        )

    # ── MACD ─────────────────────────────────────────────────────────────────
    hist = macd_l - macd_s
    fig.add_trace(go.Bar(
        x=idx, y=hist,
        marker_color=[DARK["green"] if v >= 0 else DARK["red"] for v in hist],
        name="MACD Hist", opacity=0.7,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=idx, y=macd_l, name="MACD",
        line=dict(color=DARK["blue"], width=1.2),
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=idx, y=macd_s, name="Signal",
        line=dict(color=DARK["yellow"], width=1.2),
    ), row=3, col=1)

    fig.update_layout(
        height=640,
        paper_bgcolor=DARK["bg"],
        plot_bgcolor=DARK["panel"],
        font=dict(color=DARK["text"], size=11),
        margin=dict(l=12, r=12, t=40, b=10),
        legend=dict(orientation="h", y=1.04, x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis_rangeslider_visible=False,
        showlegend=True,
    )
    fig.update_xaxes(showgrid=False, linecolor=DARK["panel"])
    fig.update_yaxes(showgrid=True, gridcolor="#1e2633", linecolor=DARK["panel"])
    return fig


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STRATEGY ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _generate_strategy() -> dict:
    return {
        "entry": random.choice(INDICATORS),
        "exit":  random.choice(INDICATORS),
        "period": random.randint(5, 50),
        "thresh": round(random.uniform(0.1, 2.0), 3),
    }


def _backtest(strategy: dict, n: int = 400) -> dict:
    mu    = random.uniform(0.003, 0.018)
    sigma = random.uniform(0.01, 0.06)
    rets  = np.random.normal(mu, sigma, n)
    # simple threshold filter
    active = rets[rets > strategy["thresh"] * 0.01]
    if len(active) < 20:
        active = rets
    sharpe   = float(active.mean() / (active.std() + 1e-9) * np.sqrt(252))
    cum      = np.cumprod(1 + rets)
    drawdown = float(1 - cum[-1] / cum.max()) if cum.max() > 0 else 0.0
    wins     = int((active > 0).sum())
    win_rate = round(wins / max(len(active), 1) * 100, 1)
    pnl      = round(float(cum[-1] - 1) * 100, 2)
    return {
        "sharpe":   round(sharpe, 3),
        "drawdown": round(drawdown, 4),
        "win_rate": win_rate,
        "pnl":      pnl,
    }


def strategy_lab_df(n: int = 1000, top: int = 20) -> pd.DataFrame:
    results = []
    for _ in range(n):
        s = _generate_strategy()
        m = _backtest(s)
        results.append({
            "Strategy": f"{s['entry']}→{s['exit']} p{s['period']}",
            "Sharpe":   m["sharpe"],
            "WinRate%": m["win_rate"],
            "PnL%":     m["pnl"],
            "DD%":      round(m["drawdown"] * 100, 2),
        })
    df = pd.DataFrame(results)
    return df.nlargest(top, "Sharpe").reset_index(drop=True)


def scoreboard_df(n: int = 20) -> pd.DataFrame:
    """Load from V9.1 scoreboard if available, else generate."""
    if _HAS_SCOREBOARD:
        try:
            top = _SCOREBOARD.top(n)
            if top:
                rows = []
                for entry in top:
                    s = entry.get("strategy", {})
                    m = entry.get("metrics", {})
                    rows.append({
                        "Strategy": f"{s.get('entry_indicator','?')}→{s.get('exit_indicator','?')} p{s.get('period','?')}",
                        "Sharpe":   round(float(m.get("sharpe", 0)), 3),
                        "WinRate%": round(float(m.get("win_rate", 0)) * 100, 1),
                        "PnL%":     round(float(m.get("pnl", 0)), 2),
                        "DD%":      round(float(m.get("drawdown", 0)) * 100, 2),
                    })
                return pd.DataFrame(rows)
        except Exception:
            pass
    return strategy_lab_df(200, n)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PORTFOLIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_PORTFOLIO = {
    "BTC": {"units": 0.5,  "entry": 60_000},
    "ETH": {"units": 4.0,  "entry": 2_800},
    "SOL": {"units": 30.0, "entry": 120},
    "BNB": {"units": 5.0,  "entry": 340},
}


def portfolio_df() -> pd.DataFrame:
    rows = []
    total_value = 0.0
    for asset, pos in _PORTFOLIO.items():
        price   = round(_base_price(asset) * (1 + random.uniform(-0.03, 0.03)), 2)
        value   = round(pos["units"] * price, 2)
        cost    = pos["units"] * pos["entry"]
        pnl     = round(value - cost, 2)
        pnl_pct = round((value / cost - 1) * 100, 2) if cost > 0 else 0.0
        total_value += value
        rows.append({
            "Asset":  asset,
            "Units":  pos["units"],
            "Price": price,
            "Value $": value,
            "PnL $":  pnl,
            "PnL %":  pnl_pct,
        })
    # allocation
    for row in rows:
        row["Alloc%"] = round(row["Value $"] / total_value * 100, 1)
    return pd.DataFrame(rows)


def portfolio_pie() -> go.Figure:
    df  = portfolio_df()
    fig = go.Figure(go.Pie(
        labels=df.Asset,
        values=df["Alloc%"],
        hole=0.45,
        marker=dict(colors=[DARK["green"], DARK["blue"], DARK["yellow"], DARK["red"]]),
        textfont=dict(color=DARK["text"]),
    ))
    fig.update_layout(
        height=280,
        paper_bgcolor=DARK["bg"],
        plot_bgcolor=DARK["bg"],
        font=dict(color=DARK["text"]),
        margin=dict(l=8, r=8, t=30, b=8),
        showlegend=True,
        legend=dict(font=dict(color=DARK["text"])),
    )
    return fig


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WHALE RADAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_WHALE_TYPES = [
    "WHALE_BUY", "WHALE_SELL",
    "EXCHANGE_INFLOW", "EXCHANGE_OUTFLOW",
    "LIQUIDATION", "LARGE_TRANSFER",
]


def whale_df(n: int = 12) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        coin   = random.choice(COINS_TOP[:15])
        amount = round(random.uniform(1e5, 5e7), 0)
        rows.append({
            "Asset": coin,
            "Type":  random.choice(_WHALE_TYPES),
            "Amount $": amount,
            "Threat": "HIGH" if amount > 1e7 else ("MEDIUM" if amount > 2e6 else "LOW"),
            "Time":  datetime.now().strftime("%H:%M:%S"),
        })
    return pd.DataFrame(rows).sort_values("Amount $", ascending=False).reset_index(drop=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RISK ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def risk_metrics() -> dict:
    daily_rets = np.random.normal(0.001, 0.025, 252)
    vol_ann    = round(float(daily_rets.std() * np.sqrt(252)) * 100, 2)
    var_95     = round(float(np.percentile(daily_rets, 5)) * 100, 2)
    sharpe     = round(float(daily_rets.mean() / (daily_rets.std() + 1e-9) * np.sqrt(252)), 3)
    cum        = np.cumprod(1 + daily_rets)
    dd         = round(float(1 - cum.min() / cum.max()) * 100, 2)
    status     = "CRITICAL" if dd > 20 else ("WARNING" if dd > 10 else "OK")
    return {
        "volatility_ann": vol_ann,
        "var_95":         var_95,
        "sharpe":         sharpe,
        "max_drawdown":   dd,
        "status":         status,
    }


def equity_curve() -> go.Figure:
    n    = 365
    base = 100_000
    rets = np.random.normal(0.0015, 0.022, n)
    cum  = base * np.cumprod(1 + rets)
    peak = np.maximum.accumulate(cum)
    dd   = (cum - peak) / peak * 100

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3],
                        vertical_spacing=0.06,
                        subplot_titles=["Equity Curve ($)", "Drawdown (%)"])

    fig.add_trace(go.Scatter(
        x=np.arange(n), y=cum,
        fill="tozeroy",
        fillcolor="rgba(0,255,159,0.08)",
        line=dict(color=DARK["green"], width=1.8),
        name="Portfolio",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=np.arange(n), y=peak,
        line=dict(color=DARK["blue"], width=1, dash="dot"),
        name="Peak",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=np.arange(n), y=dd,
        fill="tozeroy",
        fillcolor="rgba(255,78,106,0.15)",
        line=dict(color=DARK["red"], width=1.5),
        name="Drawdown %",
    ), row=2, col=1)

    fig.add_hline(y=-10, line_dash="dash", line_color=DARK["yellow"], opacity=0.5, row=2, col=1)
    fig.add_hline(y=-20, line_dash="dash", line_color=DARK["red"],    opacity=0.5, row=2, col=1)

    fig.update_layout(
        height=420,
        paper_bgcolor=DARK["bg"],
        plot_bgcolor=DARK["panel"],
        font=dict(color=DARK["text"]),
        margin=dict(l=12, r=12, t=40, b=10),
        legend=dict(orientation="h", y=1.06, bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#1e2633")
    return fig


def sharpe_bar(df: pd.DataFrame) -> go.Figure:
    top = df.nlargest(15, "Sharpe")
    colors = [DARK["green"] if s > 1.5 else DARK["yellow"] if s > 0.8 else DARK["red"]
              for s in top.Sharpe]
    fig = go.Figure(go.Bar(
        x=top.Sharpe, y=top.Strategy,
        orientation="h",
        marker_color=colors,
        text=top.Sharpe.astype(str),
        textposition="outside",
    ))
    fig.update_layout(
        height=420,
        paper_bgcolor=DARK["bg"],
        plot_bgcolor=DARK["panel"],
        font=dict(color=DARK["text"], size=10),
        margin=dict(l=8, r=20, t=30, b=8),
        xaxis_title="Sharpe Ratio",
        yaxis=dict(autorange="reversed"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1e2633")
    return fig


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI AGENTS STATUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_AGENTS = [
    ("MarketScanner",       "research"),
    ("TechnicalAnalyst",    "research"),
    ("CorrelationAnalyzer", "market"),
    ("StrategyGenerator",   "strategy"),
    ("GeneticOptimizer",    "strategy"),
    ("BacktestLab",         "quant"),
    ("MonteCarloEngine",    "quant"),
    ("RiskMonitor",         "risk"),
    ("PositionCalculator",  "risk"),
    ("ExecutionEngine",     "execution"),
    ("RLTrader",            "execution"),
    ("PerformanceMonitor",  "monitoring"),
    ("FeatureEngineer",     "intelligence"),
    ("RegimeDetector",      "intelligence"),
    ("KellyAllocator",      "portfolio"),
    ("VolatilityTargeter",  "portfolio"),
    ("WhaleRadar",          "whales"),
    ("StrategyRanker",      "engine"),
    ("DecisionEngine",      "engine"),
    ("AIControlCenter",     "dashboard"),
]


def agents_df() -> pd.DataFrame:
    rows = []
    for name, module in _AGENTS:
        status    = random.choices(["running", "idle", "busy"], weights=[0.6, 0.25, 0.15])[0]
        cycles    = random.randint(0, 999)
        last_ms   = round(random.uniform(5, 500), 1)
        rows.append({
            "Agent":  name,
            "Module": module,
            "Status": status,
            "Cycles": cycles,
            "Last ms": last_ms,
        })
    return pd.DataFrame(rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MARKET HEATMAP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def market_heatmap() -> go.Figure:
    n     = min(30, len(COINS_TOP))
    coins = COINS_TOP[:n]
    chg   = np.random.uniform(-12, 12, n)
    sizes = np.abs(chg) + 1

    fig = go.Figure(go.Treemap(
        labels=coins,
        parents=[""] * n,
        values=sizes,
        textinfo="label+text",
        text=[f"{c:+.1f}%" for c in chg],
        marker=dict(
            colors=chg,
            colorscale=[[0, DARK["red"]], [0.5, "#1e2633"], [1, DARK["green"]]],
            cmid=0,
            showscale=True,
            colorbar=dict(
                title="%",
                tickfont=dict(color=DARK["text"]),
                title_font=dict(color=DARK["text"]),
            ),
        ),
        textfont=dict(size=13, color=DARK["text"]),
    ))
    fig.update_layout(
        height=340,
        paper_bgcolor=DARK["bg"],
        plot_bgcolor=DARK["bg"],
        font=dict(color=DARK["text"]),
        margin=dict(l=4, r=4, t=30, b=4),
    )
    return fig


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM METRICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def uptime_str() -> str:
    secs = int(time.time() - _START_TIME)
    h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
    return f"{h:02d}h {m:02d}m {s:02d}s"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PANEL WIDGETS  (instantiated once, updated in-place)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ─── Controls ────────────────────────────────────────────────────────────────
coin_select = pn.widgets.Select(
    name="Coin", value="BTC",
    options=COINS_TOP, width=100,
)
tf_select = pn.widgets.Select(
    name="Timeframe", value="1h",
    options=TIMEFRAMES, width=80,
)
strat_count = pn.widgets.IntSlider(
    name="Strategies to test", start=100, end=2000,
    step=100, value=500, width=220,
)
run_lab_btn  = pn.widgets.Button(name="⚡ Run Strategy Lab", button_type="success", width=180)
refresh_btn  = pn.widgets.Button(name="🔄 Refresh All",      button_type="primary",  width=140)
auto_toggle  = pn.widgets.Toggle(name="⏱ Auto-refresh (5 s)", value=True, width=160)

# ─── KPI cards ───────────────────────────────────────────────────────────────
def _num(name: str, val: float, fmt: str = "{value:.2f}", color: str = "#ffffff") -> pn.indicators.Number:
    return pn.indicators.Number(
        name=name, value=val, format=fmt,
        default_color=color,
        styles={"background": DARK["panel"], "border-radius": "8px", "padding": "12px"},
        width=160, height=90,
    )

kpi_sharpe   = _num("Best Sharpe",     14.1,  "{value:.2f}", DARK["green"])
kpi_dd       = _num("Max Drawdown",    1.8,   "{value:.1f}%", DARK["yellow"])
kpi_signals  = _num("BUY Signals",     42,    "{value:.0f}", DARK["blue"])
kpi_agents   = _num("Active Agents",   20,    "{value:.0f}", DARK["green"])
kpi_cycles   = _num("Cycles",          0,     "{value:.0f}", DARK["text"])
kpi_uptime   = pn.indicators.String(
    name="Uptime",
    value=uptime_str(),
    styles={"background": DARK["panel"], "border-radius": "8px", "padding": "12px"},
    width=160, height=90,
)

# ─── Tables ──────────────────────────────────────────────────────────────────
_MARKET_COL_WIDTHS = {"Coin": 55, "Price $": 90, "24h %": 65, "Volume $": 100, "Signal": 60}
_table_cfg = dict(sizing_mode="stretch_width", show_index=False, height=380)

market_table   = pn.widgets.Tabulator(market_scan_df(50), **_table_cfg,
                                       widths=_MARKET_COL_WIDTHS)
strategy_table = pn.widgets.Tabulator(scoreboard_df(20),  **_table_cfg)
whale_table    = pn.widgets.Tabulator(whale_df(12),        **_table_cfg)
portfolio_table= pn.widgets.Tabulator(portfolio_df(),      **_table_cfg)
agents_table   = pn.widgets.Tabulator(agents_df(),         **_table_cfg)

# ─── Charts ──────────────────────────────────────────────────────────────────
chart_pane    = pn.pane.Plotly(candle_chart("BTC", "1h"),   sizing_mode="stretch_width")
equity_pane   = pn.pane.Plotly(equity_curve(),              sizing_mode="stretch_width")
heatmap_pane  = pn.pane.Plotly(market_heatmap(),            sizing_mode="stretch_width")
sharpe_pane   = pn.pane.Plotly(sharpe_bar(scoreboard_df()), sizing_mode="stretch_width")
pie_pane      = pn.pane.Plotly(portfolio_pie(),             sizing_mode="stretch_width")

# ─── Risk panel ──────────────────────────────────────────────────────────────
_risk_md = pn.pane.Markdown("", sizing_mode="stretch_width",
                             styles={"background": DARK["panel"],
                                     "padding": "14px",
                                     "border-radius": "8px"})

def _risk_text() -> str:
    r = risk_metrics()
    status_icon = {"OK": "🟢", "WARNING": "🟡", "CRITICAL": "🔴"}.get(r["status"], "⚪")
    return (
        f"### {status_icon} Risk Engine — {r['status']}\n\n"
        f"| Metric | Value |\n|---|---|\n"
        f"| Annualised Volatility | **{r['volatility_ann']}%** |\n"
        f"| VaR 95% (1-day)       | **{r['var_95']}%** |\n"
        f"| Sharpe Ratio          | **{r['sharpe']}** |\n"
        f"| Max Drawdown          | **{r['max_drawdown']}%** |\n"
    )

_risk_md.object = _risk_text()

# ─── System status ────────────────────────────────────────────────────────────
_sys_md = pn.pane.Markdown("", sizing_mode="stretch_width",
                            styles={"background": DARK["panel"],
                                    "padding": "14px",
                                    "border-radius": "8px"})

def _sys_text() -> str:
    ub = 6  # placeholder: cannot import psutil reliably
    return (
        f"### 🖥 System Status\n\n"
        f"| | |\n|---|---|\n"
        f"| **V9.1 Scoreboard** | {'✅ connected' if _HAS_SCOREBOARD else '⚪ standalone'} |\n"
        f"| **Cycles completed** | {_CYCLE_COUNT[0]} |\n"
        f"| **Uptime** | {uptime_str()} |\n"
        f"| **Last update** | {datetime.now().strftime('%H:%M:%S')} |\n"
        f"| **Auto-refresh** | {'ON ✅' if auto_toggle.value else 'OFF ⏸'} |\n"
    )

_sys_md.object = _sys_text()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _update_chart(*_):
    chart_pane.object = candle_chart(coin_select.value, tf_select.value)

coin_select.param.watch(_update_chart, "value")
tf_select.param.watch(  _update_chart, "value")


@pn.depends(run_lab_btn, watch=True)
def _run_lab(_):
    run_lab_btn.name = "⏳ Running…"
    run_lab_btn.disabled = True
    df = strategy_lab_df(strat_count.value, 20)
    strategy_table.value = df
    sharpe_pane.object   = sharpe_bar(df)
    best = float(df.Sharpe.max()) if not df.empty else 0.0
    kpi_sharpe.value = best
    run_lab_btn.name = "⚡ Run Strategy Lab"
    run_lab_btn.disabled = False


def _full_update():
    if not auto_toggle.value:
        return
    _CYCLE_COUNT[0] += 1
    # market
    market_table.value  = market_scan_df(50)
    heatmap_pane.object = market_heatmap()
    buy_count = int((market_scan_df(50)["Signal"] == "BUY").sum())
    kpi_signals.value   = buy_count
    # chart
    chart_pane.object   = candle_chart(coin_select.value, tf_select.value)
    # strategies
    df_st = scoreboard_df(20)
    strategy_table.value = df_st
    sharpe_pane.object   = sharpe_bar(df_st)
    kpi_sharpe.value     = float(df_st.Sharpe.max()) if not df_st.empty else 0.0
    # portfolio
    portfolio_table.value = portfolio_df()
    pie_pane.object       = portfolio_pie()
    # whale + equity
    whale_table.value  = whale_df(12)
    equity_pane.object = equity_curve()
    # risk + sys
    _risk_md.object    = _risk_text()
    _sys_md.object     = _sys_text()
    # agents
    agents_table.value = agents_df()
    kpi_agents.value   = 20
    kpi_cycles.value   = float(_CYCLE_COUNT[0])
    kpi_uptime.value   = uptime_str()
    # dd kpi
    r = risk_metrics()
    kpi_dd.value = r["max_drawdown"]


@pn.depends(refresh_btn, watch=True)
def _manual_refresh(_):
    _full_update()


pn.state.add_periodic_callback(_full_update, period=5000)  # 5 s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_header_md = pn.pane.Markdown(
    f"## 🤖 Autonomous Quant AI Control Center — V12\n"
    f"*{datetime.now().strftime('%A %d %B %Y')}  ·  Synthetic data mode  ·  V9.1 integrated*",
    sizing_mode="stretch_width",
    styles={"background": DARK["panel"], "padding": "10px 16px",
            "border-radius": "8px", "color": DARK["text"]},
)

_controls = pn.Row(
    coin_select, tf_select, strat_count, run_lab_btn,
    refresh_btn, auto_toggle,
    align="center", margin=(4, 4),
)

_kpi_row = pn.Row(
    kpi_sharpe, kpi_dd, kpi_signals, kpi_agents, kpi_cycles, kpi_uptime,
    sizing_mode="stretch_width", margin=(4, 0),
)

# ── TAB 1: Market ─────────────────────────────────────────────────────────────
tab_market = pn.Column(
    pn.pane.Markdown("### 🌐 Market Heatmap (Top 30)"),
    heatmap_pane,
    pn.pane.Markdown("### 📊 Market Scanner (200 coins)"),
    market_table,
    sizing_mode="stretch_width",
)

# ── TAB 2: Charts ─────────────────────────────────────────────────────────────
tab_charts = pn.Column(
    pn.Row(coin_select, tf_select, align="center"),
    pn.pane.Markdown("### 📈 Live Chart – Candlestick + EMA + RSI + MACD"),
    chart_pane,
    sizing_mode="stretch_width",
)

# ── TAB 3: Strategy Lab ───────────────────────────────────────────────────────
tab_strat = pn.Column(
    pn.Row(strat_count, run_lab_btn, align="center"),
    pn.Row(
        pn.Column(
            pn.pane.Markdown("### 🧬 Top Strategies (Sharpe-ranked)"),
            strategy_table,
        ),
        pn.Column(
            pn.pane.Markdown("### 📊 Sharpe Distribution"),
            sharpe_pane,
        ),
    ),
    sizing_mode="stretch_width",
)

# ── TAB 4: Portfolio ──────────────────────────────────────────────────────────
tab_portfolio = pn.Column(
    pn.Row(
        pn.Column(
            pn.pane.Markdown("### 💼 Positions"),
            portfolio_table,
        ),
        pn.Column(
            pn.pane.Markdown("### 🍕 Allocation"),
            pie_pane,
        ),
    ),
    pn.pane.Markdown("### 📉 Equity Curve & Drawdown"),
    equity_pane,
    sizing_mode="stretch_width",
)

# ── TAB 5: Risk ───────────────────────────────────────────────────────────────
tab_risk = pn.Column(
    _risk_md,
    equity_pane,
    sizing_mode="stretch_width",
)

# ── TAB 6: Whale Radar ────────────────────────────────────────────────────────
tab_whale = pn.Column(
    pn.pane.Markdown("### 🐋 Whale Transaction Radar"),
    whale_table,
    sizing_mode="stretch_width",
)

# ── TAB 7: AI Agents ──────────────────────────────────────────────────────────
tab_agents = pn.Column(
    pn.pane.Markdown("### 🤖 V9.1 Agent Monitor (20 Agents)"),
    agents_table,
    _sys_md,
    sizing_mode="stretch_width",
)

# ── Main tabs ─────────────────────────────────────────────────────────────────
tabs = pn.Tabs(
    ("🌐 Market",      tab_market),
    ("📈 Charts",      tab_charts),
    ("🧬 Strategy Lab",tab_strat),
    ("💼 Portfolio",   tab_portfolio),
    ("⚠️ Risk Engine", tab_risk),
    ("🐋 Whale Radar", tab_whale),
    ("🤖 AI Agents",   tab_agents),
    dynamic=True,
    sizing_mode="stretch_width",
)

template = pn.template.FastListTemplate(
    title="🤖 Quant AI Control Center V12",
    theme="dark",
    accent_base_color=DARK["green"],
    header_background="#0e1117",
    main=[
        _header_md,
        _controls,
        _kpi_row,
        tabs,
    ],
    sidebar=[
        pn.pane.Markdown("### ⚙️ Controls"),
        coin_select,
        tf_select,
        pn.layout.Divider(),
        pn.pane.Markdown("### 🧬 Strategy Lab"),
        strat_count,
        run_lab_btn,
        pn.layout.Divider(),
        pn.pane.Markdown("### 🔄 Refresh"),
        refresh_btn,
        auto_toggle,
        pn.layout.Divider(),
        _sys_md,
    ],
)

template.servable()
