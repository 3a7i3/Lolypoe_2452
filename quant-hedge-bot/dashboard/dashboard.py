"""
Dashboard - Interface Streamlit pour monitoring
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.database import db
from utils.logger import logger

def setup_page():
    """Configure la page Streamlit."""
    st.set_page_config(
        page_title="Quant Hedge Bot",
        page_icon="",
        layout="wide"
    )
    st.title("Quant Hedge Bot - Live Monitor")

def display_portfolio_stats(portfolio_manager):
    """Affiche les stats du portefeuille."""
    st.header("Portfolio Status")
    
    stats = portfolio_manager.get_portfolio_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"${stats['total_value']:.2f}")
    
    with col2:
        st.metric("Total PnL", f"${stats['total_pnl']:.2f}", f"{stats['total_pnl_percent']:.2f}%")
    
    with col3:
        st.metric("Positions", stats['num_positions'])
    
    with col4:
        st.metric("Cash", f"${stats['cash']:.2f}")

def display_positions(portfolio_manager):
    """Affiche les positions actives."""
    st.subheader("Active Positions")
    
    if portfolio_manager.positions:
        positions_data = []
        for symbol, pos in portfolio_manager.positions.items():
            positions_data.append({
                'Symbol': symbol,
                'Quantity': pos.get('quantity', 0),
                'Entry Price': f"${pos.get('entry_price', 0):.2f}",
                'Current Price': f"${pos.get('current_price', 0):.2f}",
                'PnL': f"${pos.get('pnl', 0):.2f}",
                'PnL %': f"{pos.get('pnl_percent', 0):.2f}%"
            })
        
        df_positions = pd.DataFrame(positions_data)
        st.dataframe(df_positions, use_container_width=True)
    else:
        st.info("No active positions")

def display_trade_history():
    """Affiche l'historique des trades."""
    st.subheader("Trade History")
    
    try:
        df_trades = db.get_all_trades()
        if not df_trades.empty:
            st.dataframe(df_trades, use_container_width=True)
        else:
            st.info("No trades yet")
    
    except Exception as e:
        st.error(f"Error loading trades: {e}")

def display_performance_chart(portfolio_manager):
    """Affiche le graphique de performance."""
    st.subheader("Performance Chart")
    
    try:
        df_perf = db.get_performance_stats()
        
        if not df_perf.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_perf['date'],
                y=df_perf['cumulative_return'] * 100,
                mode='lines',
                name='Cumulative Return',
                line=dict(color='green')
            ))
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data yet")
    
    except Exception as e:
        st.error(f"Error loading performance: {e}")

def main():
    """Fonction principale."""
    setup_page()
    
    # Sidebar
    st.sidebar.header("Settings")
    refresh_interval = st.sidebar.slider("Refresh Interval (sec)", 10, 300, 60)
    
    # Main content
    if st.button("Refresh"):
        st.rerun()
    
    # Placeholder for real-time updates
    st.info("Dashboard in development - Connect with bot for live updates")

if __name__ == "__main__":
    main()
