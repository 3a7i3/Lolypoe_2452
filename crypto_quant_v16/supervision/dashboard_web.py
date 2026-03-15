import streamlit as st

def render_dashboard(strategies, portfolio, trades, alerts):
    st.title("AI Quant Lab Dashboard")
    st.subheader("Strategies")
    st.table(strategies)
    st.subheader("Portfolio")
    st.json(portfolio)
    st.subheader("Latest Trades")
    st.table(trades[-10:])
    st.subheader("Alerts")
    st.table(alerts[-10:])
