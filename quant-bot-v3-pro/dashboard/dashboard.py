import streamlit as st
import pandas as pd
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.market_data import get_data
from core.strategy_engine import generate_trade_signal
from config import SYMBOLS

st.set_page_config(page_title="Quant Bot v3 PRO", layout="wide")

st.title("[QUANT BOT] v3 PRO Dashboard")
st.divider()

# Sidebar
with st.sidebar:
    st.header("Configuration")
    symbol = st.selectbox("Selectionnez une crypto", SYMBOLS)
    interval = st.selectbox("Intervalle", ["1m", "5m", "15m", "1h"])
    period = st.selectbox("Periode", ["1d", "5d", "1mo"])

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Graphique {symbol}")
    
    data = get_data(symbol, interval, period)
    
    if data is not None and not data.empty:
        st.line_chart(data[["CLOSE"]])
        st.dataframe(data[["CLOSE", "VOLUME"]].tail(10))
    else:
        st.error("Erreur: Donnees non disponibles")

with col2:
    st.subheader("Signal de Trading")
    
    if data is not None and not data.empty:
        signal = generate_trade_signal(data)
        
        if signal == "BUY":
            st.success(f"Signal: {signal}")
        elif signal == "SELL":
            st.error(f"Signal: {signal}")
        else:
            st.info(f"Signal: {signal}")
        
        last_price = data["CLOSE"].iloc[-1]
        st.metric("Prix", f"${last_price:.2f}")

st.divider()

# Trades history
st.subheader("Historique des Trades")
try:
    trades = pd.read_csv("data/trades.csv")
    st.dataframe(trades.tail(20), use_container_width=True)
except FileNotFoundError:
    st.warning("Aucun trade enregistre")
