import streamlit as st
from supervision.alert_manager import AlertManager

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

if __name__ == "__main__":
    # Exécution autonome pour test rapide
    strategies = [{"name": "Momentum", "score": 0.87}, {"name": "RSI", "score": 0.78}]
    portfolio = {"total_capital": 100000, "allocations": {"Momentum": 50000, "RSI": 50000}}
    trades = [{"token": "TOKEN1", "type": "buy", "amount": 1000}]
    alert_manager = AlertManager()
    alert_manager.add_alert("Test dashboard alert")
    render_dashboard(strategies, portfolio, trades, alert_manager.get_recent_alerts())
