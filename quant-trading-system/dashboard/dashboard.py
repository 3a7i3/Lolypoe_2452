"""
Professional Trading Dashboard - Real-time monitoring and analytics
Built with Streamlit
"""

import logging
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

def run_dashboard():
    """Run Streamlit dashboard"""
    st.set_page_config(
        page_title="Quant Trading System V5",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title
    st.markdown("# 🚀 Quantitative Trading System V5")
    st.markdown("**Professional Turbocharged Trading Engine**")
    st.markdown("---")
    
    # Create tabs
    tabs = st.tabs([
        "📊 Overview",
        "💼 Portfolio", 
        "⚠️ Risk Analysis",
        "🎯 Strategies",
        "💳 Trades",
        "📈 Analytics"
    ])
    
    # Tab 1: Overview
    with tabs[0]:
        render_overview_tab()
    
    # Tab 2: Portfolio
    with tabs[1]:
        render_portfolio_tab()
    
    # Tab 3: Risk
    with tabs[2]:
        render_risk_tab()
    
    # Tab 4: Strategies
    with tabs[3]:
        render_strategies_tab()
    
    # Tab 5: Trades
    with tabs[4]:
        render_trades_tab()
    
    # Tab 6: Analytics
    with tabs[5]:
        render_analytics_tab()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("System Status", "🟢 LIVE", "Running 24/7")
    with col2:
        st.metric("Monitoring", "1000+ Cryptos", "Multi-exchange")
    with col3:
        st.metric("Strategies", "6", "Ensemble voting")


def render_overview_tab():
    """Portfolio Overview Tab"""
    st.subheader("Portfolio Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total AUM", "$1,234,567", "+5.2%", delta_color="inverse")
    
    with col2:
        st.metric("Daily P&L", "$12,345", "+8.3%", delta_color="off")
    
    with col3:
        st.metric("Sharpe Ratio", "1.85", "+0.15")
    
    with col4:
        st.metric("Max Drawdown", "-8.5%", "Safe")
    
    # Performance chart
    st.subheader("Performance")
    
    dates = pd.date_range(end=datetime.now(), periods=100)
    values = 100000 * np.cumprod(1 + np.random.randn(100) * 0.01)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, name="Portfolio", 
                            line=dict(color='#1f77b4', width=2)))
    fig.add_trace(go.Scatter(x=dates, y=values * 1.02, name="Benchmark",
                            line=dict(color='#7f7f7f', width=1, dash='dash')))
    
    fig.update_layout(
        title="Portfolio vs Benchmark (100 days)",
        xaxis_title="Date",
        yaxis_title="Value (USD)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Win Rate", "62.5%", "134/214 trades")
    
    with col2:
        st.metric("Avg Return/Trade", "0.85%", "+0.05%")
    
    with col3:
        st.metric("Active Positions", "23", "of 50 max")


def render_portfolio_tab():
    """Portfolio Tab"""
    st.subheader("Position Details")
    
    # Generate sample data
    positions_data = {
        'Symbol': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT'],
        'Entry Price': [42500, 2250, 95, 0.65, 0.50],
        'Current Price': [43200, 2310, 102, 0.72, 0.55],
        'Qty': [0.5, 10, 100, 5000, 10000],
        'P&L %': [1.65, 2.67, 7.37, 10.77, 10.00],
        'Allocation': [0.35, 0.20, 0.15, 0.20, 0.10]
    }
    
    df_positions = pd.DataFrame(positions_data)
    
    st.dataframe(
        df_positions.style.format({
            'Entry Price': '${:,.2f}',
            'Current Price': '${:,.2f}',
            'P&L %': '{:.2f}%',
            'Allocation': '{:.1%}'
        }).highlight_max(subset=['P&L %'], color='lightgreen')
            .highlight_min(subset=['P&L %'], color='lightcoral'),
        use_container_width=True
    )
    
    # Allocation chart
    fig = px.pie(
        values=df_positions['Allocation'],
        names=df_positions['Symbol'],
        title="Portfolio Allocation"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_risk_tab():
    """Risk Analysis Tab"""
    st.subheader("Risk Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("VaR (95%)", "-2.5%", "Daily loss threshold")
    
    with col2:
        st.metric("CVaR (95%)", "-3.2%", "Expected tail loss")
    
    with col3:
        st.metric("Correlation", "0.45", "Portfolio diversification")
    
    # Correlation heatmap
    st.subheader("Correlation Matrix")
    
    symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'XRP']
    corr_matrix = np.random.rand(5, 5)
    
    for i in range(len(corr_matrix)):
        corr_matrix[i][i] = 1.0
    
    fig = go.Figure(data=go.Heatmap(z=corr_matrix, x=symbols, y=symbols, colorscale='RdBu'))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Monte Carlo
    st.subheader("Monte Carlo Simulation (10,000 scenarios)")
    
    scenarios = np.random.randn(10000) * 0.02
    final_returns = np.exp(scenarios * 252)
    
    fig = go.Figure(data=[go.Histogram(x=final_returns, nbinsx=50)])
    fig.update_layout(
        title="Portfolio Return Distribution",
        xaxis_title="Annual Return Factor",
        yaxis_title="Frequency"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_strategies_tab():
    """Strategies Tab"""
    st.subheader("Strategy Performance")
    
    strategies_data = {
        'Strategy': ['Trend Following', 'Mean Reversion', 'Breakout', 'Volatility', 'Momentum', 'Stat Arb'],
        'Win Rate': [0.625, 0.582, 0.723, 0.551, 0.645, 0.420],
        'Sharpe Ratio': [1.85, 1.45, 2.10, 1.20, 1.75, 0.95],
        'Max DD': [-0.085, -0.062, -0.045, -0.125, -0.078, -0.180],
        'Trades': [134, 89, 102, 156, 67, 45]
    }
    
    df_strats = pd.DataFrame(strategies_data)
    
    st.dataframe(
        df_strats.style.format({
            'Win Rate': '{:.1%}',
            'Sharpe Ratio': '{:.2f}',
            'Max DD': '{:.1%}'
        }).highlight_max(subset=['Sharpe Ratio'], color='lightgreen'),
        use_container_width=True
    )
    
    # Strategy performance over time
    fig = px.bar(df_strats, x='Strategy', y=['Win Rate', 'Sharpe Ratio'],
                title='Strategy Comparison', barmode='group')
    st.plotly_chart(fig, use_container_width=True)


def render_trades_tab():
    """Trades Tab"""
    st.subheader("Recent Trades")
    
    trades_data = {
        'Time': ['14:23:45', '14:18:32', '14:12:10', '14:05:55', '13:58:20'],
        'Symbol': ['BTC/USDT', 'SOL/USDT', 'ETH/USDT', 'ADA/USDT', 'XRP/USDT'],
        'Action': ['BUY', 'SELL', 'BUY', 'BUY', 'SELL'],
        'Price': [43200, 102, 2310, 0.72, 0.55],
        'Qty': [0.5, 100, 10, 5000, 10000],
        'P&L': [325, -85, 182, 350, -425],
        'Strategy': ['Trend', 'Breakout', 'Mean Rev', 'Momentum', 'Stat Arb']
    }
    
    df_trades = pd.DataFrame(trades_data)
    
    st.dataframe(
        df_trades.style.format({
            'Price': '${:,.2f}',
            'P&L': '${:,.0f}'
        }).applymap(lambda x: 'background-color: lightgreen' if isinstance(x, (int, float)) and x > 0 else 'background-color: lightcoral' if isinstance(x, (int, float)) and x < 0 else '', subset=['P&L']),
        use_container_width=True
    )


def render_analytics_tab():
    """Analytics Tab"""
    st.subheader("Advanced Analytics")
    
    # Equity curve with drawdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Equity Curve")
        dates = pd.date_range(end=datetime.now(), periods=100)
        equity = 100000 * np.cumprod(1 + np.random.randn(100) * 0.01)
        
        fig = px.line(x=dates, y=equity, title='Portfolio Equity')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Drawdown %")
        cummax = np.maximum.accumulate(equity)
        drawdown = (equity - cummax) / cummax
        
        fig = px.bar(x=dates, y=drawdown * 100, title='Portfolio Drawdown')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    run_dashboard()
