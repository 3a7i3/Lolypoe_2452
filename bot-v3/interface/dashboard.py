import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.market_data import get_market_data
from core.indicators import calculate_indicators
from core.strategy import generate_signal
from core.logger import logger

st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")

st.title("[TRADING BOT] Dashboard v3")
st.divider()

# Sidebar
with st.sidebar:
    st.header("Configuration")
    symbol = st.selectbox("Selectionnez une crypto", ["BTC-USD", "ETH-USD", "BNB-USD"])
    interval = st.selectbox("Intervalle", ["1m", "5m", "15m", "1h"])
    period = st.selectbox("Periode", ["1d", "5d", "1mo"])

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Graphique {symbol}")
    
    # Recuperer et afficher les donnees
    data = get_market_data(symbol, interval, period)
    
    if data is not None and not data.empty:
        # Calculer les indicateurs
        data = calculate_indicators(data)
        
        # Afficher le graphique
        st.line_chart(data[["Close", "SMA20", "SMA50"]])
        
        # Afficher les donnees
        st.dataframe(data[["Close", "SMA20", "SMA50"]].tail(10))
    else:
        st.error("Impossible de recuperer les donnees")

with col2:
    st.subheader("Signal")
    
    if data is not None and not data.empty:
        signal = generate_signal(data)
        
        # Afficher le signal avec couleur
        if signal == "BUY":
            st.success(f"Signal: {signal}")
        elif signal == "SELL":
            st.error(f"Signal: {signal}")
        else:
            st.info(f"Signal: {signal}")
        
        # Afficher les infos
        last = data.iloc[-1]
        st.metric("Prix actuel", f"${last['Close']:.2f}")
        st.metric("SMA20", f"${last['SMA20']:.2f}" if pd.notna(last['SMA20']) else "N/A")
        st.metric("SMA50", f"${last['SMA50']:.2f}" if pd.notna(last['SMA50']) else "N/A")

st.divider()

# Afficher l'historique des trades
st.subheader("Historique des trades")
try:
    trades = pd.read_csv("data/trades.csv")
    st.dataframe(trades.tail(20), use_container_width=True)
except FileNotFoundError:
    st.warning("Aucun trade enregistre")

import pandas as pd
