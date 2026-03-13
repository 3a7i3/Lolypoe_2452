"""
Dashboard Components – Reusable UI widgets for Quant V16
Charts, tables, gauges, and real-time monitors
"""

import panel as pn
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

pn.extension("plotly", sizing_mode="stretch_width")


def create_market_table(data: pd.DataFrame) -> pn.widgets.Tabulator:
    """Create market data table"""
    if data.empty:
        data = pd.DataFrame({
            'symbol': ['BTC', 'ETH'],
            'price': [40000, 2500],
            'change_24h': [2.5, -1.3],
            'volume': [1e9, 5e8]
        })
    
    return pn.widgets.Tabulator(
        data,
        pagination=25,
        sizing_mode="stretch_width",
        height=400
    )


def create_candlestick_chart(data: dict) -> go.Figure:
    """Create candlestick chart with RSI and MACD"""
    
    if not data or 'closes' not in data:
        # Dummy data
        data = {
            'opens': [40000 + i*100 for i in range(100)],
            'highs': [40100 + i*100 for i in range(100)],
            'lows': [39900 + i*100 for i in range(100)],
            'closes': [40050 + i*100 for i in range(100)],
        }
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=("Candlestick", "RSI(14)", "MACD"),
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=list(range(len(data['closes']))),
            open=data['opens'],
            high=data['highs'],
            low=data['lows'],
            close=data['closes'],
            name="Candlestick"
        ),
        row=1, col=1
    )

    # RSI (dummy)
    rsi = 50 + np.random.randn(len(data['closes'])) * 10
    fig.add_trace(
        go.Scatter(
            y=rsi, mode='lines',
            name="RSI(14)",
            line=dict(color="orange")
        ),
        row=2, col=1
    )

    # MACD (dummy)
    macd = np.random.randn(len(data['closes'])) * 100
    fig.add_trace(
        go.Bar(
            y=macd, name="MACD Histogram",
            marker=dict(color="gray")
        ),
        row=3, col=1
    )

    fig.update_layout(height=600, template="plotly_dark", hovermode="x unified")
    return fig


def create_portfolio_pie(allocation: dict) -> go.Figure:
    """Create portfolio allocation pie chart"""
    
    if not allocation:
        allocation = {"BTC": 0.35, "ETH": 0.30, "SOL": 0.20, "AVAX": 0.15}
    
    fig = go.Figure(data=[go.Pie(
        labels=list(allocation.keys()),
        values=list(allocation.values()),
        hole=0.4,
        marker=dict(colors=['#00ff9f', '#ff006e', '#ffd60a', '#3a86ff'])
    )])
    
    fig.update_layout(
        template="plotly_dark",
        title="Portfolio Allocation",
        height=400
    )
    return fig


def create_equity_curve(equity: list) -> go.Figure:
    """Create equity curve chart"""
    
    if not equity:
        equity = [10000 * (1.01 ** i) for i in range(100)]
    
    dd_values = []
    peak = equity[0]
    for val in equity:
        if val > peak:
            peak = val
        dd = (peak - val) / peak if peak > 0 else 0
        dd_values.append(dd)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Equity Curve", "Drawdown"),
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}]]
    )

    fig.add_trace(
        go.Scatter(y=equity, mode='lines', name='Equity', 
                  line=dict(color='#00ff9f'), fill='tozeroy'),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(y=dd_values, mode='lines', name='Drawdown',
                  line=dict(color='#ff006e'), fill='tozeroy'),
        row=2, col=1
    )

    fig.update_layout(height=500, template="plotly_dark", hovermode="x unified")
    return fig


def create_kpi_indicators(metrics: dict) -> pn.pane.HTML:
    """Create KPI indicator cards"""
    
    kpis = f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
        <div style="background:#1a1a1a;padding:15px;border-radius:5px;border-left:4px solid #00ff9f;">
            <div style="font-size:12px;color:#888;">Best Sharpe</div>
            <div style="font-size:24px;color:#00ff9f;font-weight:bold;">{metrics.get('best_sharpe', 0):.2f}</div>
        </div>
        <div style="background:#1a1a1a;padding:15px;border-radius:5px;border-left:4px solid #ff006e;">
            <div style="font-size:12px;color:#888;">Max Drawdown</div>
            <div style="font-size:24px;color:#ff006e;font-weight:bold;">{metrics.get('max_dd', 0):.2%}</div>
        </div>
        <div style="background:#1a1a1a;padding:15px;border-radius:5px;border-left:4px solid #ffd60a;">
            <div style="font-size:12px;color:#888;">Active Signals</div>
            <div style="font-size:24px;color:#ffd60a;font-weight:bold;">{metrics.get('active_signals', 0)}</div>
        </div>
    </div>
    """
    return pn.pane.HTML(kpis, width=1200, height=120)
