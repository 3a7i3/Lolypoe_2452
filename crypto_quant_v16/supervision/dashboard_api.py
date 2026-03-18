from fastapi import FastAPI
from typing import List
from supervision.alert_manager import AlertManager

app = FastAPI()
alert_manager = AlertManager()

@app.get("/status")
def get_status():
    return {"status": "ok"}

@app.get("/alerts")
def get_alerts(n: int = 10):
    return {"alerts": alert_manager.get_recent_alerts(n)}

@app.get("/portfolio")
def get_portfolio():
    # TODO: intégrer la vraie logique de portefeuille
    return {"portfolio": {"total_capital": 100000, "allocations": {"Momentum": 50000, "RSI": 50000}}}

@app.get("/strategies")
def get_strategies():
    # TODO: intégrer la vraie logique de stratégies
    return {"strategies": [{"name": "Momentum", "score": 0.87}, {"name": "RSI", "score": 0.78}]}

@app.get("/trades")
def get_trades(n: int = 10):
    # TODO: intégrer la vraie logique de trades
    return {"trades": [{"token": "TOKEN1", "type": "buy", "amount": 1000}]}
