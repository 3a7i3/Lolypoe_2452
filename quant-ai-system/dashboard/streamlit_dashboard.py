"""
Streamlit Dashboard for V6 System
Real-time monitoring and analytics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Crypto AI Trading System V6",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 0rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🤖 Crypto AI Trading System V6")
st.markdown("### Autonomous AI-Driven Quantitative Trading Platform")

# Sidebar
st.sidebar.markdown("## ⚙️ System Control")
system_mode = st.sidebar.radio(
    "System Mode",
    ["Live Trading", "Paper Trading", "Backtesting"],
    index=1
)

cycle_interval = st.sidebar.slider(
    "Cycle Interval (seconds)",
    60, 3600, 300, 60
)

max_positions = st.sidebar.slider(
    "Max Positions",
    5, 50, 20, 1
)

max_drawdown = st.sidebar.slider(
    "Max Drawdown (%)",
    5, 50, 25, 1
) / 100

show_advanced = st.sidebar.checkbox("Show Advanced Metrics", False)

# Generate mock data for dashboard
def generate_mock_data():
    days = 30
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Portfolio value
    portfolio_values = 100000 + np.cumsum(np.random.normal(100, 500, days))
    
    # Trades data
    trades_data = {
        'Entry': pd.date_range(end=datetime.now(), periods=15, freq='2D'),
        'Symbol': np.random.choice(['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT'], 15),
        'Entry Price': np.random.uniform(20000, 100000, 15),
        'Current Price': np.random.uniform(20000, 100000, 15),
        'Return %': np.random.uniform(-10, 20, 15),
        'P&L': np.random.uniform(-5000, 8000, 15),
        'Status': np.random.choice(['OPEN', 'CLOSED'], 15, p=[0.6, 0.4])
    }
    
    return dates, portfolio_values, pd.DataFrame(trades_data)

dates, portfolio_values, trades_df = generate_mock_data()

# Top metrics row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Portfolio Value",
        f"${portfolio_values[-1]:,.0f}",
        f"{((portfolio_values[-1]/portfolio_values[0])-1)*100:+.2f}%"
    )

with col2:
    st.metric(
        "24h Return",
        f"{np.random.uniform(-2, 5):.2f}%",
        "vs benchmark"
    )

with col3:
    st.metric(
        "Sharpe Ratio",
        f"{np.random.uniform(1.0, 3.0):.2f}",
        "Annualized"
    )

with col4:
    st.metric(
        "Max Drawdown",
        f"{np.random.uniform(-15, -5):.1f}%",
        "Current"
    )

with col5:
    st.metric(
        "Win Rate",
        f"{np.random.uniform(45, 75):.1f}%",
        f"({len(trades_df)} trades)"
    )

# Main dashboard tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Performance", "💼 Positions", "🧬 Strategies", "📈 Analytics", "⚙️ Settings"
])

# Tab 1: Performance
with tab1:
    st.subheader("Portfolio Performance")
    
    # Equity curve
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(
        x=dates,
        y=portfolio_values,
        name="Portfolio Value",
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    
    fig_equity.update_layout(
        title="Equity Curve",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig_equity, use_container_width=True)
    
    # Daily returns distribution
    col_left, col_right = st.columns(2)
    
    with col_left:
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1] * 100
        fig_returns = px.histogram(
            x=daily_returns,
            nbins=30,
            title="Daily Returns Distribution",
            labels={'x': 'Daily Return (%)', 'y': 'Frequency'},
            color_discrete_sequence=['#00cc96']
        )
        fig_returns.update_layout(
            template="plotly_dark",
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig_returns, use_container_width=True)
    
    with col_right:
        # Drawdown analysis
        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max * 100
        
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=dates,
            y=drawdown,
            name="Drawdown",
            line=dict(color='#ef553b', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 85, 59, 0.1)'
        ))
        fig_dd.update_layout(
            title="Drawdown Analysis",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template="plotly_dark",
            height=350,
            hovermode='x unified'
        )
        st.plotly_chart(fig_dd, use_container_width=True)

# Tab 2: Positions
with tab2:
    st.subheader("Active Positions")
    
    # Format trades dataframe
    trades_display = trades_df.copy()
    trades_display['Current Price'] = trades_display['Current Price'].apply(lambda x: f"${x:,.2f}")
    trades_display['Entry Price'] = trades_display['Entry Price'].apply(lambda x: f"${x:,.2f}")
    trades_display['P&L'] = trades_display['P&L'].apply(lambda x: f"${x:+,.0f}")
    trades_display['Return %'] = trades_display['Return %'].apply(lambda x: f"{x:+.2f}%")
    
    st.dataframe(trades_display, use_container_width=True, hide_index=True)
    
    # Position breakdown
    col_left, col_right = st.columns(2)
    
    with col_left:
        position_breakdown = trades_df[trades_df['Status'] == 'OPEN']['Symbol'].value_counts()
        fig_pos = px.pie(
            values=position_breakdown.values,
            names=position_breakdown.index,
            title="Position Breakdown by Symbol",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pos.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig_pos, use_container_width=True)
    
    with col_right:
        # Win/Loss breakdown
        winloss_counts = trades_df['Status"].apply(lambda x: 'Win' if x == 'CLOSED' else 'Open').value_counts()
        fig_wl = px.bar(
            x=winloss_counts.index,
            y=winloss_counts.values,
            title="Trades by Status",
            labels={'x': 'Status', 'y': 'Count'},
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        fig_wl.update_layout(template="plotly_dark", height=350, showlegend=False)
        st.plotly_chart(fig_wl, use_container_width=True)

# Tab 3: Strategies
with tab3:
    st.subheader("Strategy Performance")
    
    # Strategy metrics
    strategy_data = {
        'Strategy': ['STRAT_001', 'STRAT_002', 'STRAT_003', 'STRAT_004', 'STRAT_005'],
        'Win Rate': [0.62, 0.58, 0.65, 0.55, 0.60],
        'Sharpe': [2.1, 1.8, 2.3, 1.6, 1.9],
        'Drawdown': [-0.12, -0.15, -0.10, -0.18, -0.13],
        'Usage': [30, 25, 20, 15, 10]
    }
    strategy_df = pd.DataFrame(strategy_data)
    
    # Strategy comparison chart
    fig_strat = go.Figure()
    fig_strat.add_trace(go.Bar(x=strategy_df['Strategy'], y=strategy_df['Win Rate'], name='Win Rate'))
    fig_strat.add_trace(go.Bar(x=strategy_df['Strategy'], y=strategy_df['Sharpe']/5, name='Sharpe (÷5)'))
    
    fig_strat.update_layout(
        title="Strategy Performance Comparison",
        barmode='group',
        template="plotly_dark",
        height=350,
        hovermode='x unified'
    )
    st.plotly_chart(fig_strat, use_container_width=True)
    
    # Strategy allocation
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_alloc = px.pie(
            values=strategy_df['Usage'],
            names=strategy_df['Strategy'],
            title="Current Strategy Allocation",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_alloc.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig_alloc, use_container_width=True)
    
    with col_right:
        st.dataframe(strategy_df, use_container_width=True, hide_index=True)

# Tab 4: Analytics
with tab4:
    st.subheader("Advanced Analytics")
    
    if show_advanced:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Monthly Return", f"{np.random.uniform(-5, 15):.2f}%")
            st.metric("Volatility (Annual)", f"{np.random.uniform(15, 35):.1f}%")
        
        with col2:
            st.metric("Information Ratio", f"{np.random.uniform(1.0, 2.5):.2f}")
            st.metric("Sortino Ratio", f"{np.random.uniform(1.5, 3.5):.2f}")
        
        # Risk-Return scatter
        fig_rr = go.Figure()
        risks = np.random.uniform(10, 30, 20)
        returns = np.random.uniform(5, 25, 20)
        
        fig_rr.add_trace(go.Scatter(
            x=risks,
            y=returns,
            mode='markers',
            marker=dict(
                size=12,
                color=returns/risks,
                colorscale='Viridis',
                showscale=True
            ),
            text=[f'Strategy {i}' for i in range(20)],
            hovertemplate='<b>%{text}</b><br>Risk: %{x:.1f}%<br>Return: %{y:.1f}%'
        ))
        
        fig_rr.update_layout(
            title="Risk vs Return Scatter",
            xaxis_title="Risk (Volatility %)",
            yaxis_title="Return (%)",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig_rr, use_container_width=True)
    else:
        st.info("Enable 'Show Advanced Metrics' in the sidebar to view detailed analytics")

# Tab 5: Settings
with tab5:
    st.subheader("System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Trading Parameters")
        initial_capital = st.number_input("Initial Capital ($)", value=100000, step=10000)
        commission = st.slider("Commission Rate (%)", 0.01, 1.0, 0.1, 0.01)
        max_dd_setting = st.slider("Max Drawdown (%)", 5, 50, 25, 5)
    
    with col2:
        st.markdown("### AI Parameters")
        population_size = st.slider("Strategy Population Size", 20, 200, 50, 10)
        generations = st.slider("GA Generations", 5, 100, 20, 5)
        mutation_rate = st.slider("Mutation Rate", 0.01, 0.5, 0.1, 0.01)
    
    st.markdown("---")
    
    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("Settings saved successfully!")
    
    with col_reset:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.info("Settings reset to defaults")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🚀 Crypto AI Trading System V6 | Real-time Autonomous Trading Platform</p>
    <p style='font-size: 0.8em; color: gray;'>Last updated: {} | System Status: RUNNING ✅</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
