"""
Option AE — API REST FastAPI pour piloter le système V9.1 à distance.

Endpoints :
  GET  /health            — health check (toujours 200)
  GET  /status            — état courant du système (cycle, régime, equity, etc.)
  GET  /paper             — métriques paper trading
  GET  /config            — snapshot de la RuntimeConfig
  PATCH /config           — modifier des paramètres à la volée
  GET  /scoreboard        — top stratégies du scoreboard SQL
  POST /pause             — met la boucle en pause
  POST /resume            — reprend la boucle
"""
from __future__ import annotations

import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.api.system_state import SystemState, get_state

app = FastAPI(
    title="Quant Hedge AI — REST API V9.1",
    description="Pilotage et monitoring du système V9.1 en temps réel",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modèles Pydantic ───────────────────────────────────────────────────────────

class ConfigPatch(BaseModel):
    """Champs modifiables à chaud (sous-ensemble de RuntimeConfig)."""
    sleep_seconds: int | None = None
    max_cycles: int | None = None
    display_frequency: int | None = None
    report_enabled: bool | None = None
    report_frequency: int | None = None
    mtf_enabled: bool | None = None
    cb_consecutive_losses: int | None = None
    cb_daily_loss_limit: float | None = None
    sentiment_enabled: bool | None = None


class PauseResumeResponse(BaseModel):
    status: str
    paused: bool
    cycle: int
    timestamp: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Health check — répond toujours 200 si l'API est vivante."""
    return {"status": "ok", "timestamp": _now()}


@app.get("/status", tags=["system"])
def get_status() -> dict[str, Any]:
    """État complet du système (cycle, régime, equity, CB, etc.)."""
    state = get_state()
    snap = state.snapshot()
    snap["timestamp"] = _now()
    return snap


@app.get("/paper", tags=["trading"])
def get_paper() -> dict[str, Any]:
    """Métriques du paper trading (equity, PnL, drawdown, win rate)."""
    state = get_state()
    return {
        "equity": state.equity,
        "pnl": state.pnl,
        "return_pct": state.return_pct,
        "drawdown_pct": state.drawdown_pct,
        "win_rate": state.win_rate,
        "trades_count": state.trades_count,
        "timestamp": _now(),
    }


@app.get("/config", tags=["config"])
def get_config() -> dict[str, Any]:
    """Snapshot de la RuntimeConfig courante."""
    state = get_state()
    with state._lock:
        cfg = dict(state.config_snapshot)
    cfg["timestamp"] = _now()
    return cfg


@app.patch("/config", tags=["config"])
def patch_config(patch: ConfigPatch) -> dict[str, Any]:
    """
    Modifie des paramètres de la RuntimeConfig à la volée.
    Seuls les champs non-null dans le body sont appliqués.
    """
    state = get_state()
    applied: dict[str, Any] = {}
    update_payload: dict[str, Any] = {}

    for field_name, value in patch.model_dump(exclude_none=True).items():
        update_payload[field_name] = value
        # Mettre à jour aussi le config_snapshot
        applied[field_name] = value

    if not update_payload:
        raise HTTPException(status_code=400, detail="Aucun champ fourni dans le body")

    with state._lock:
        for k, v in update_payload.items():
            state.config_snapshot[k] = v
        # max_cycles propagé aussi dans l'état principal
        if "max_cycles" in update_payload:
            object.__setattr__(state, "max_cycles", update_payload["max_cycles"])

    return {"applied": applied, "timestamp": _now()}


@app.get("/scoreboard", tags=["trading"])
def get_scoreboard() -> dict[str, Any]:
    """Top stratégies du scoreboard SQL."""
    state = get_state()
    with state._lock:
        top = list(state.scoreboard_top)
    return {"count": len(top), "strategies": top, "timestamp": _now()}


@app.post("/pause", tags=["control"])
def pause_loop() -> PauseResumeResponse:
    """Met la boucle principale en pause (le cycle en cours se termine)."""
    state = get_state()
    state.pause()
    return PauseResumeResponse(
        status="paused",
        paused=True,
        cycle=state.cycle,
        timestamp=_now(),
    )


@app.post("/resume", tags=["control"])
def resume_loop() -> PauseResumeResponse:
    """Reprend la boucle principale après une pause."""
    state = get_state()
    state.resume()
    return PauseResumeResponse(
        status="running",
        paused=False,
        cycle=state.cycle,
        timestamp=_now(),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def build_app(state: SystemState | None = None) -> FastAPI:
    """
    Factory pour les tests : permet d'injecter un SystemState personnalisé.
    Retourne l'app FastAPI avec l'état substitué.
    """
    if state is not None:
        import agents.api.system_state as _mod
        _mod._state = state
    return app
