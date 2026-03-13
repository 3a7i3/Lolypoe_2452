"""
Professional Hedge Fund Dashboard
==================================
Real-time monitoring of portfolio, risk, and strategy performance
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.database import db
from utils.logger import logger

def format_currency(value):
    """Format value as currency."""
    if value >= 0:
        return f"${value:,.2f}"
    else:
        return f"-${abs(value):,.2f}"

def format_percent(value):
    """Format value as percentage."""
    color = "green" if value >= 0 else "red"
    symbol = "+" if value >= 0 else ""
    return f"{symbol}{value:.2f}%"

def create_professional_dashboard():
    """Create professional hedge fund dashboard."""
    
    st.set_page_config(
        page_title="Hedge Fund Trading System",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom styling
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .metric-title {
            font-size: 12px;
            color: #666;
            font-weight: bold;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🏦 Professional Quantitative Hedge Fund Trading System")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Refresh interval
        refresh_interval = st.slider(
            "Dashboard Refresh (seconds)",
            min_value=5,
            max_value=60,
            value=10,
            step=5
        )
        
        # Time range
        time_range = st.selectbox(
            "Time Range",
            ["1 Day", "1 Week", "1 Month", "3 Months", "YTD", "All"]
        )
        
        # Strategy filter
        st.subheader("Strategy Selection")
        strategies = st.multiselect(
            "Active Strategies",
            ["Trend Following", "Mean Reversion", "Breakout", "Volatility Trading", "Market Making"],
            default=["Trend Following", "Mean Reversion"]
        )
        
        # Risk parameters
        st.subheader("Risk Controls")
        max_drawdown = st.number_input(
            "Max Drawdown %",
            min_value=5,
            max_value=50,
            value=20,
            step=1
        )
        
        max_leverage = st.number_input(
            "Max Leverage",
            min_value=1.0,
            max_value=3.0,
            value=2.0,
            step=0.1
        )
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "💼 Portfolio",
        "📈 Risk Analysis",
        "🎯 Strategies",
        "🔄 Trades",
        "📉 Analytics"
    ])
    
    # TAB 1: OVERVIEW
    with tab1:
        st.subheader("Portfolio Overview")
        
        # Key metrics row 1
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total AUM",
                format_currency(100000),
                "+15.3%"
            )
        
        with col2:
            st.metric(
                "Daily P&L",
                format_currency(1250),
                "+1.25%"
            )
        
        with col3:
            st.metric(
                "Total Return",
                format_percent(15.3),
                "+2.1%"
            )
        
        with col4:
            st.metric(
                "Sharpe Ratio",
                "1.85",
                "+0.15"
            )
        
        # Key metrics row 2
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Max Drawdown",
                format_percent(-8.5),
                "-1.2%"
            )
        
        with col2:
            st.metric(
                "Win Rate",
                "62.5%",
                "+2.3%"
            )
        
        with col3:
            st.metric(
                "Active Positions",
                "12",
                "+2"
            )
        
        with col4:
            st.metric(
                "Exposure",
                "125%",
                "+5%"
            )
        
        # Performance chart
        st.subheader("Portfolio Performance")
        
        # Generate sample data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
        portfolio_value = 100000 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
        benchmark_value = 100000 * np.exp(np.cumsum(np.random.normal(0.0005, 0.015, 100)))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=portfolio_value,
            name='Portfolio', line=dict(color='#1f77b4', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=benchmark_value,
            name='Benchmark (BTC)', line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Portfolio Value vs Benchmark",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: PORTFOLIO
    with tab2:
        st.subheader("Position Details")
        
        # Positions table
        positions_data = {
            'Symbol': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'XRP-USD'],
            'Quantity': [0.5, 5.2, 100, 500, 2000],
            'Entry Price': [45000, 2500, 45, 0.75, 0.52],
            'Current Price': [48000, 2650, 52, 0.82, 0.55],
            'Value': [24000, 13780, 5200, 410, 1100],
            'P&L': [1500, 780, 700, 35, 60],
            'P&L %': [6.7, 6.0, 15.5, 9.3, 5.8]
        }
        
        positions_df = pd.DataFrame(positions_data)
        
        st.dataframe(
            positions_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Value": st.column_config.NumberColumn(format="$%d"),
                "P&L": st.column_config.NumberColumn(format="$%d"),
                "P&L %": st.column_config.NumberColumn(format="%.1f%%")
            }
        )
        
        # Allocation breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sector Allocation")
            allocation_data = {
                'Sector': ['Large Cap', 'Mid Cap', 'Altcoins', 'Emerging'],
                'Allocation': [40, 30, 20, 10]
            }
            fig = px.pie(
                allocation_data,
                values='Allocation',
                names='Sector',
                title='Portfolio Allocation by Sector'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Exchange Exposure")
            exchange_data = {
                'Exchange': ['Binance', 'Kraken', 'Coinbase', 'KuCoin'],
                'Exposure': [45, 30, 15, 10]
            }
            fig = px.pie(
                exchange_data,
                values='Exposure',
                names='Exchange',
                title='Exposure by Exchange'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 3: RISK ANALYSIS
    with tab3:
        st.subheader("Risk Metrics & Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Value at Risk (95%)", "-2.5%", "-0.3%")
        with col2:
            st.metric("Conditional VaR (95%)", "-3.8%", "-0.5%")
        with col3:
            st.metric("Sortino Ratio", "2.15", "+0.25")
        
        # Risk concentration
        st.subheader("Risk Concentration")
        
        # Correlation heatmap
        correlation_matrix = np.array([
            [1.0, 0.85, 0.75, 0.65, 0.55],
            [0.85, 1.0, 0.82, 0.72, 0.62],
            [0.75, 0.82, 1.0, 0.80, 0.70],
            [0.65, 0.72, 0.80, 1.0, 0.85],
            [0.55, 0.62, 0.70, 0.85, 1.0]
        ])
        
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'XRP']
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=symbols,
            y=symbols,
            colorscale='RdBu',
            zmid=0.5
        ))
        fig.update_layout(title="Position Correlation Matrix", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Monte Carlo simulation results
        st.subheader("Monte Carlo Analysis (10,000 Simulations)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Expected Return (252d)", "+18.5%", "Base Case")
        with col2:
            st.metric("95% Confidence Interval", "$85,000 - $125,000", "Range")
        with col3:
            st.metric("Worst Case (1%)", "-32.5%", "1% Probability")
        with col4:
            st.metric("Win Probability", "68.5%", "Next Year")
    
    # TAB 4: STRATEGIES
    with tab4:
        st.subheader("Strategy Performance")
        
        # Strategy comparison
        strategy_data = {
            'Strategy': ['Trend Following', 'Mean Reversion', 'Breakout', 'Volatility Trading', 'Market Making'],
            'Win Rate': [65, 58, 72, 55, 61],
            'Avg Return': [2.3, 1.8, 3.1, 1.5, 1.2],
            'Sharpe': [1.8, 1.4, 2.1, 1.2, 0.9],
            'Trades': [150, 200, 85, 120, 300]
        }
        
        strategy_df = pd.DataFrame(strategy_data)
        
        # Columns for visualization
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                strategy_df,
                x='Strategy',
                y='Win Rate',
                title='Strategy Win Rates'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                strategy_df,
                x='Strategy',
                y='Sharpe',
                title='Strategy Sharpe Ratios'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Strategy details
        st.subheader("Detailed Strategy Metrics")
        st.dataframe(
            strategy_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Win Rate": st.column_config.NumberColumn(format="%d%%"),
                "Avg Return": st.column_config.NumberColumn(format="%.2f%%"),
                "Sharpe": st.column_config.NumberColumn(format="%.2f")
            }
        )
    
    # TAB 5: TRADES
    with tab5:
        st.subheader("Recent Trades")
        
        # Trade history
        trades_data = {
            'Timestamp': pd.date_range(start='2025-03-01', periods=10, freq='4H'),
            'Symbol': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'BTC-USD', 'XRP-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'BTC-USD'],
            'Signal': ['BUY', 'BUY', 'SELL', 'BUY', 'BUY', 'SELL', 'BUY', 'BUY', 'SELL', 'BUY'],
            'Price': [48000, 2650, 52, 0.82, 48100, 0.55, 2655, 51.8, 0.81, 48200],
            'Quantity': [0.1, 1.0, 10, 50, 0.05, 200, 0.5, 20, 100, 0.15],
            'P&L': [150, 200, -100, 75, 250, -80, 120, 350, -50, 300],
            'P&L %': [3.1, 7.5, -1.9, 9.1, 5.2, -1.4, 4.5, 6.7, -6.2, 6.2]
        }
        
        trades_df = pd.DataFrame(trades_data)
        
        st.dataframe(
            trades_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "P&L": st.column_config.NumberColumn(format="$%d"),
                "Price": st.column_config.NumberColumn(format="$.2f"),
                "P&L %": st.column_config.NumberColumn(format="%.2f%%")
            }
        )
        
        # Trade statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", "10", "Today")
        with col2:
            st.metric("Winning Trades", "7", "70%")
        with col3:
            st.metric("Avg Win", format_currency(185))
        with col4:
            st.metric("Avg Loss", format_currency(-76))
    
    # TAB 6: ANALYTICS
    with tab6:
        st.subheader("Advanced Analytics")
        
        # Equity curve with drawdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Equity Curve with Drawdown")
            
            dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
            equity = np.cumprod(1 + np.random.normal(0.001, 0.02, 100))
            equity = equity * 100000
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=equity,
                fill='tozeroy',
                name='Equity Curve'
            ))
            
            fig.update_layout(
                title="Equity Curve",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Return Distribution")
            
            returns = np.random.normal(0.001, 0.02, 1000)
            
            fig = go.Figure(data=[go.Histogram(x=returns, nbinsx=50)])
            fig.update_layout(
                title="Daily Return Distribution",
                xaxis_title="Returns",
                yaxis_title="Frequency",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.caption("Professional Quantitative Hedge Fund Trading System v2.0")
    
    with col3:
        st.caption("Data provides for visualization purposes only")

if __name__ == "__main__":
    create_professional_dashboard()
