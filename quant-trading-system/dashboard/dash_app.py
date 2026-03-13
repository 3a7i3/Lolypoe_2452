"""
Professional Dashboard - Real-time trading system monitoring
Shows: P&L, trades, strategies, anomalies, risk metrics
"""

import logging
from datetime import datetime, timedelta
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Crypto AI Trading System - Dashboard"

# Color scheme
COLORS = {
    'bg': '#1a1a2e',
    'card_bg': '#16213e',
    'accent': '#0f3460',
    'profit': '#06d6a0',
    'loss': '#ef476f',
    'neutral': '#ffd166',
    'secondary': '#073b4c'
}

# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

app.layout = html.Div([
    # Interval for auto-refresh
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    
    # Main container
    html.Div([
        # Header
        html.Div([
            html.Div([
                html.H1('🤖 Crypto AI Trading System', style={'margin': 0}),
                html.P('Institutional-Grade Quantitative Trading Platform', 
                       style={'margin': '5px 0', 'opacity': 0.7})
            ], style={'flex': 1}),
            
            html.Div([
                html.Span('Status: ', style={'marginRight': '10px'}),
                html.Span('🟢 OPERATIONAL', id='status-indicator',
                         style={'color': COLORS['profit'], 'fontWeight': 'bold'})
            ], style={'fontSize': '14px'})
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '20px',
            'borderBottom': f'2px solid {COLORS["accent"]}',
            'marginBottom': '20px'
        }),
        
        # Key Metrics Cards
        html.Div([
            _create_metric_card('Total Portfolio Value', '$1,234,567', COLORS['profit']),
            _create_metric_card('Daily P&L', '+$12,345', COLORS['profit']),
            _create_metric_card('Sharpe Ratio', '1.24', COLORS['profit']),
            _create_metric_card('Max Drawdown', '-18.5%', COLORS['loss']),
            _create_metric_card('Win Rate', '58.2%', COLORS['profit']),
            _create_metric_card('Active Trades', '12', COLORS['neutral']),
        ], style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
            'gap': '15px',
            'marginBottom': '30px',
            'padding': '0 20px'
        }),
        
        # Main panels
        html.Div([
            # Left column
            html.Div([
                # Equity curve
                html.Div([
                    html.H3('Equity Curve', style={'marginTop': 0}),
                    dcc.Graph(id='equity-curve', style={'height': '400px'},
                             config={'displayModeBar': False})
                ], style=_card_style()),
                
                # P&L breakdown
                html.Div([
                    html.H3('P&L Breakdown', style={'marginTop': 0}),
                    dcc.Graph(id='pnl-breakdown', style={'height': '350px'},
                             config={'displayModeBar': False})
                ], style=_card_style()),
            ], style={'flex': '60%', 'marginRight': '20px'}),
            
            # Right column
            html.Div([
                # Strategy performance
                html.Div([
                    html.H3('Strategy Performance', style={'marginTop': 0}),
                    dcc.Graph(id='strategy-performance', style={'height': '350px'},
                             config={'displayModeBar': False})
                ], style=_card_style()),
                
                # Regime & Anomalies
                html.Div([
                    html.H3('Market Regime', style={'marginTop': 0}),
                    html.Div(id='regime-display', style={
                        'fontSize': '18px',
                        'padding': '20px',
                        'borderRadius': '8px',
                        'backgroundColor': COLORS['accent'],
                        'marginBottom': '15px',
                        'textAlign': 'center'
                    }),
                    
                    html.H4('Recent Anomalies', style={'marginTop': '20px'}),
                    html.Div(id='anomalies-list', style={
                        'maxHeight': '200px',
                        'overflowY': 'auto'
                    })
                ], style=_card_style()),
            ], style={'flex': '40%'}),
        ], style={'display': 'flex', 'gap': '20px', 'padding': '0 20px', 'marginBottom': '20px'}),
        
        # Open trades table
        html.Div([
            html.H3('Open Trades', style={'marginTop': 0}),
            html.Table(id='trades-table', style={'width': '100%'})
        ], style=_card_style()),
        
        # Trading signals recent
        html.Div([
            html.H3('Recent Signals', style={'marginTop': 0}),
            html.Table(id='signals-table', style={'width': '100%'})
        ], style=_card_style()),
        
    ], style={
        'backgroundColor': COLORS['bg'],
        'color': '#fff',
        'fontFamily': 'Arial, sans-serif',
        'minHeight': '100vh',
        'paddingBottom': '40px'
    })
], style={'margin': 0, 'padding': 0})

# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    [Output('equity-curve', 'figure'),
     Output('pnl-breakdown', 'figure'),
     Output('strategy-performance', 'figure'),
     Output('regime-display', 'children'),
     Output('anomalies-list', 'children'),
     Output('trades-table', 'children'),
     Output('signals-table', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n):
    """Update all dashboard components"""
    
    # Generate sample data (would come from API/database)
    dates = pd.date_range(end=datetime.now(), periods=365)
    equity_values = np.cumsum(np.random.randn(365) * 500 + 100) + 1000000
    
    # Equity curve
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(
        x=dates, y=equity_values,
        fill='tozeroy',
        line=dict(color=COLORS['profit'], width=2),
        name='Equity'
    ))
    fig_equity.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['bg']
    )
    
    # P&L breakdown
    strategies = ['Trend Following', 'Mean Reversion', 'Volatility', 'Arbitrage', 'Market Making']
    pnl_values = [35000, 28000, 15000, 8000, 12000]
    colors_pnl = [COLORS['profit'] if x > 0 else COLORS['loss'] for x in pnl_values]
    
    fig_pnl = go.Figure(go.Bar(
        x=strategies, y=pnl_values,
        marker_color=colors_pnl
    ))
    fig_pnl.update_layout(
        template='plotly_dark',
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['bg'],
        showlegend=False
    )
    fig_pnl.update_xaxes(showgrid=False)
    fig_pnl.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    
    # Strategy performance
    win_rates = [0.62, 0.58, 0.55, 0.60, 0.52]
    fig_strat = go.Figure(go.Bar(
        x=strategies, y=win_rates,
        marker_color=COLORS['profit']
    ))
    fig_strat.update_layout(
        template='plotly_dark',
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['bg'],
        showlegend=False
    )
    fig_strat.update_yaxes(range=[0, 1])
    
    # Regime
    regime_text = "🟢 STRONG BULL\nConfidence: 85%\nTrend: Strong Uptrend"
    
    # Anomalies
    anomalies = [
        html.Div([
            html.Span('🔴', style={'marginRight': '10px'}),
            html.Span('BTC volume spike (2.5x)', style={'flex': 1}),
            html.Span('2m ago', style={'opacity': 0.7})
        ], style={'display': 'flex', 'padding': '8px', 'borderBottom': '1px solid rgba(255,255,255,0.1)'})
    ]
    
    # Trades table
    trades_html = html.Tbody([
        html.Tr([
            html.Th('Symbol', style=_table_header_style()),
            html.Th('Entry', style=_table_header_style()),
            html.Th('Current', style=_table_header_style()),
            html.Th('P&L %', style=_table_header_style()),
            html.Th('Strategy', style=_table_header_style()),
        ]),
        html.Tr([
            html.Td('BTC/USDT', style=_table_cell_style()),
            html.Td('$45,230', style=_table_cell_style()),
            html.Td('$45,890', style=_table_cell_style()),
            html.Td(html.Span('+1.45%', style={'color': COLORS['profit']}), style=_table_cell_style()),
            html.Td('Trend Following', style=_table_cell_style()),
        ]),
        html.Tr([
            html.Td('ETH/USDT', style=_table_cell_style()),
            html.Td('$2,450', style=_table_cell_style()),
            html.Td('$2,420', style=_table_cell_style()),
            html.Td(html.Span('-1.22%', style={'color': COLORS['loss']}), style=_table_cell_style()),
            html.Td('Mean Reversion', style=_table_cell_style()),
        ]),
    ])
    
    # Signals table
    signals_html = html.Tbody([
        html.Tr([
            html.Th('Time', style=_table_header_style()),
            html.Th('Symbol', style=_table_header_style()),
            html.Th('Signal', style=_table_header_style()),
            html.Th('Confidence', style=_table_header_style()),
            html.Th('Regime', style=_table_header_style()),
        ]),
        html.Tr([
            html.Td('14:23:45', style=_table_cell_style()),
            html.Td('SOL/USDT', style=_table_cell_style()),
            html.Td(html.Span('🟢 BUY', style={'color': COLORS['profit']}), style=_table_cell_style()),
            html.Td('78%', style=_table_cell_style()),
            html.Td('BULL', style=_table_cell_style()),
        ]),
        html.Tr([
            html.Td('14:15:22', style=_table_cell_style()),
            html.Td('ADA/USDT', style=_table_cell_style()),
            html.Td(html.Span('🔴 SELL', style={'color': COLORS['loss']}), style=_table_cell_style()),
            html.Td('65%', style=_table_cell_style()),
            html.Td('BEAR', style=_table_cell_style()),
        ]),
    ])
    
    return (
        fig_equity,
        fig_pnl,
        fig_strat,
        regime_text,
        anomalies,
        trades_html,
        signals_html
    )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _create_metric_card(label: str, value: str, color: str) -> html.Div:
    """Create metric card"""
    return html.Div([
        html.P(label, style={'margin': 0, 'fontSize': '12px', 'opacity': 0.7}),
        html.P(value, style={'margin': '10px 0', 'fontSize': '24px', 'fontWeight': 'bold', 'color': color})
    ], style={
        'padding': '15px',
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '8px',
        'borderLeft': f'4px solid {color}'
    })

def _card_style():
    """Card styling"""
    return {
        'padding': '20px',
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '8px',
        'border': f'1px solid {COLORS["accent"]}',
        'marginBottom': '20px'
    }

def _table_header_style():
    """Table header styling"""
    return {
        'padding': '12px',
        'textAlign': 'left',
        'borderBottom': f'2px solid {COLORS["accent"]}',
        'fontWeight': 'bold'
    }

def _table_cell_style():
    """Table cell styling"""
    return {
        'padding': '10px 12px',
        'borderBottom': f'1px solid {COLORS["accent"]}'
    }

# ============================================================================
# RUN DASHBOARD
# ============================================================================

def run_dashboard(port: int = 8050, debug: bool = False):
    """Run Dash dashboard"""
    app.run_server(debug=debug, port=port, host='0.0.0.0')

if __name__ == '__main__':
    run_dashboard(debug=True)

logger.info("[DASHBOARD] Professional dashboard initialized")
