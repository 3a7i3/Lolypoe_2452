"""
Crypto AI Trading System - Panel Overview Dashboard
Real-time system monitoring and performance tracking
"""

import panel as pn
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Enable Panel extensions
pn.extension('plotly')

# Set dark theme
pn.template.FastListTemplate.param.header_background = '#1a1a2e'
pn.template.FastListTemplate.param.sidebar_background = '#16213e'

# ============================================================================
# DATA GENERATION (Simulation)
# ============================================================================

def generate_equity_data():
    """Generate simulated equity curve"""
    dates = pd.date_range(end=datetime.now(), periods=365)
    returns = np.random.randn(365) * 0.015 + 0.0005
    equity = 1000000 * np.exp(np.cumsum(returns))
    return pd.DataFrame({'date': dates, 'equity': equity})

def generate_trades_data():
    """Generate simulated open trades"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT']
    trades = []
    for sym in symbols:
        pnl = np.random.uniform(-5000, 15000)
        trades.append({
            'Symbol': sym,
            'Entry': f'${np.random.uniform(100, 50000):.2f}',
            'Current': f'${np.random.uniform(100, 50000):.2f}',
            'P&L': f'${pnl:+.2f}',
            'P&L %': f'{pnl/10000*100:+.2f}%',
            'Strategy': np.random.choice(['Trend', 'Mean Reversion', 'Volatility'])
        })
    return pd.DataFrame(trades)

def generate_metrics():
    """Generate system metrics"""
    return {
        'Portfolio Value': f'$1,234,567',
        'Daily P&L': f'+$12,345',
        'Sharpe Ratio': '1.24',
        'Max Drawdown': '-18.5%',
        'Win Rate': '58.2%',
        'Active Trades': '12'
    }

def generate_signals():
    """Generate recent signals"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT']
    signals = []
    for sym in symbols[:3]:
        signals.append({
            'Time': datetime.now().strftime('%H:%M:%S'),
            'Symbol': sym,
            'Signal': np.random.choice(['🟢 BUY', '🔴 SELL']),
            'Confidence': f'{np.random.uniform(0.6, 1.0)*100:.0f}%',
            'Regime': np.random.choice(['BULL', 'NEUTRAL', 'BEAR'])
        })
    return pd.DataFrame(signals)

def generate_anomalies():
    """Generate recent anomalies"""
    anomalies = [
        {'Time': '14:23:45', 'Type': '📊 Volume Spike', 'Symbol': 'BTC', 'Details': '2.5x increase', 'Severity': '⚠️ Medium'},
        {'Time': '14:15:22', 'Type': '💥 Gap Move', 'Symbol': 'ETH', 'Details': '5% price jump', 'Severity': '⚠️ Medium'},
        {'Time': '14:08:10', 'Type': '📈 Volatility', 'Symbol': 'SOL', 'Details': '1.8x elevation', 'Severity': '🟡 Low'},
    ]
    return pd.DataFrame(anomalies)

# ============================================================================
# FIGURES
# ============================================================================

def create_equity_figure():
    """Equity curve chart"""
    df = generate_equity_data()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['equity'],
        fill='tozeroy',
        line=dict(color='#06d6a0', width=2),
        name='Equity',
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>$%{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        title='Equity Curve',
        template='plotly_dark',
        hovermode='x unified',
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
        paper_bgcolor='#16213e',
        plot_bgcolor='#0f3460'
    )
    return fig

def create_pnl_breakdown_figure():
    """P&L by strategy"""
    strategies = ['Trend Following', 'Mean Reversion', 'Volatility', 'Arbitrage', 'Market Making']
    pnl = [35000, 28000, 15000, 8000, 12000]
    colors = ['#06d6a0' if x > 0 else '#ef476f' for x in pnl]
    
    fig = go.Figure(data=go.Bar(
        x=strategies, y=pnl,
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>$%{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        title='P&L by Strategy',
        template='plotly_dark',
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
        paper_bgcolor='#16213e',
        plot_bgcolor='#0f3460',
        showlegend=False
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    return fig

def create_drawdown_figure():
    """Drawdown chart"""
    df = generate_equity_data()
    running_max = df['equity'].expanding().max()
    drawdown = (df['equity'] - running_max) / running_max * 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=drawdown,
        fill='tozeroy',
        line=dict(color='#ef476f', width=1),
        name='Drawdown',
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>%{y:.1f}%<extra></extra>'
    ))
    fig.update_layout(
        title='Drawdown Analysis',
        template='plotly_dark',
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        paper_bgcolor='#16213e',
        plot_bgcolor='#0f3460'
    )
    return fig

# ============================================================================
# METRIC CARDS
# ============================================================================

def create_metric_card(label, value, color='#06d6a0'):
    """Create a metric card"""
    html_card = f"""
    <div style="
        padding: 15px;
        background: #16213e;
        border-radius: 8px;
        border-left: 4px solid {color};
        text-align: center;
        height: 100%;
    ">
        <div style="font-size: 12px; opacity: 0.7; margin-bottom: 8px;">{label}</div>
        <div style="font-size: 24px; font-weight: bold; color: {color};">{value}</div>
    </div>
    """
    return pn.pane.HTML(html_card, width=150, height=80)

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def create_dashboard():
    """Create main dashboard"""
    
    # Get data
    metrics = generate_metrics()
    trades_df = generate_trades_data()
    signals_df = generate_signals()
    anomalies_df = generate_anomalies()
    
    # Create figures
    equity_fig = create_equity_figure()
    pnl_fig = create_pnl_breakdown_figure()
    drawdown_fig = create_drawdown_figure()
    
    # Header
    header = pn.pane.HTML("""
    <div style="padding: 20px; text-align: center;">
        <h1 style="margin: 0; color: #06d6a0;">🤖 Crypto AI Trading System</h1>
        <p style="margin: 5px 0; opacity: 0.7;">Institutional-Grade Quantitative Trading Platform</p>
    </div>
    """)
    
    # Metrics row
    metrics_row = pn.Row(
        create_metric_card('Portfolio Value', metrics['Portfolio Value'], '#06d6a0'),
        create_metric_card('Daily P&L', metrics['Daily P&L'], '#06d6a0'),
        create_metric_card('Sharpe Ratio', metrics['Sharpe Ratio'], '#ffd166'),
        create_metric_card('Max Drawdown', metrics['Max Drawdown'], '#ef476f'),
        create_metric_card('Win Rate', metrics['Win Rate'], '#06d6a0'),
        create_metric_card('Active Trades', metrics['Active Trades'], '#ffd166'),
    )
    
    # Status indicator
    status_html = pn.pane.HTML("""
    <div style="
        padding: 15px;
        background: #16213e;
        border-radius: 8px;
        border: 2px solid #06d6a0;
        text-align: center;
    ">
        <div style="font-size: 18px;">🟢 OPERATIONAL</div>
        <div style="font-size: 12px; opacity: 0.7; margin-top: 5px;">All systems healthy</div>
    </div>
    """, width=250)
    
    # Tabs for different sections
    tabs = pn.Tabs(
        ('📊 Performance', pn.Column(
            pn.Row(
                pn.pane.Plotly(equity_fig, sizing_mode='stretch_width'),
                pn.pane.Plotly(pnl_fig, sizing_mode='stretch_width'),
            ),
            pn.pane.Plotly(drawdown_fig, sizing_mode='stretch_width')
        )),
        ('💼 Trades', pn.pane.DataFrame(
            trades_df,
            sizing_mode='stretch_width',
            height=400
        )),
        ('🔔 Signals', pn.pane.DataFrame(
            signals_df,
            sizing_mode='stretch_width',
            height=300
        )),
        ('⚠️ Anomalies', pn.pane.DataFrame(
            anomalies_df,
            sizing_mode='stretch_width',
            height=300
        )),
        tabs_location='top',
        active=0,
        sizing_mode='stretch_width'
    )
    
    # Regime display
    regime_html = pn.pane.HTML("""
    <div style="
        padding: 20px;
        background: #16213e;
        border-radius: 8px;
        border: 2px solid #06d6a0;
        text-align: center;
    ">
        <div style="font-size: 14px; opacity: 0.7; margin-bottom: 10px;">Market Regime</div>
        <div style="font-size: 28px; color: #06d6a0; font-weight: bold;">🟢 STRONG BULL</div>
        <div style="font-size: 12px; opacity: 0.7; margin-top: 10px;">Confidence: 85%</div>
    </div>
    """, width=400, height=150)
    
    # System info
    system_info = pn.pane.HTML("""
    <div style="
        padding: 20px;
        background: #16213e;
        border-radius: 8px;
        font-size: 12px;
        line-height: 1.8;
    ">
        <div style="color: #06d6a0; font-weight: bold; margin-bottom: 10px;">System Information</div>
        <div>📊 <span style="opacity: 0.7;">Active Strategies:</span> <b>5</b></div>
        <div>🔍 <span style="opacity: 0.7;">Monitoring:</span> <b>1,500+ Cryptos</b></div>
        <div>🌐 <span style="opacity: 0.7;">Exchanges:</span> <b>Binance, Bybit, Coinbase, Kraken</b></div>
        <div>📈 <span style="opacity: 0.7;">Data Frequency:</span> <b>30 seconds</b></div>
        <div>⚡ <span style="opacity: 0.7;">Workers:</span> <b>16 async</b></div>
    </div>
    """, width=400, height=auto)
    
    # Sidebar
    sidebar = pn.Column(
        status_html,
        regime_html,
        system_info,
        sizing_mode='stretch_width'
    )
    
    # Main layout
    main = pn.Column(
        header,
        pn.Row(metrics_row, sizing_mode='stretch_width'),
        tabs,
        sizing_mode='stretch_width'
    )
    
    template = pn.template.FastListTemplate(
        title='Crypto AI Trading System',
        header_background='#1a1a2e',
        sidebar_width=450,
        main=[main],
        sidebar=[sidebar],
    )
    
    return template

# ============================================================================
# SERVE
# ============================================================================

if __name__ == '__main__':
    pn.serve(
        create_dashboard(),
        title='Crypto AI Trading System - Panel Dashboard',
        show=True,
        port=5006,
        websocket_origin=['localhost:5006']
    )
