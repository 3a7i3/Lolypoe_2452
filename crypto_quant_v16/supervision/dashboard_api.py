# Squelette API REST (à compléter)
from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.get("/status")
def get_status():
    return {"status": "ok"}

@app.get("/alerts")
def get_alerts():
    # TODO: intégrer AlertManager
    return {"alerts": []}
