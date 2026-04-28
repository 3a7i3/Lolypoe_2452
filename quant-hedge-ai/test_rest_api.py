"""
Tests option AE — API REST FastAPI (V9.1)

Utilise TestClient de FastAPI (httpx synchrone).
Aucun appel réseau réel, aucun thread uvicorn lancé.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agents.api.system_state import SystemState
from agents.api.rest_api import build_app


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def state() -> SystemState:
    """SystemState pré-rempli pour les tests."""
    s = SystemState(
        cycle=5,
        max_cycles=10,
        regime="bull_trend",
        symbol="BTCUSDT",
        data_source="binance",
        equity=105_000.0,
        pnl=5_000.0,
        return_pct=5.0,
        drawdown_pct=1.2,
        win_rate=0.65,
        trades_count=12,
        best_strategy_type="BOLLINGER → MACD",
        best_sharpe=3.45,
        circuit_breaker_ok=True,
        circuit_breaker_reason="",
        scoreboard_top=[
            {"rank": 1, "type": "BOLLINGER → MACD", "sharpe": 3.45},
            {"rank": 2, "type": "EMA → MACD", "sharpe": 2.90},
        ],
        config_snapshot={"max_cycles": 10, "sleep_seconds": 2, "api_enabled": True},
    )
    return s


@pytest.fixture()
def client(state: SystemState) -> TestClient:
    app = build_app(state=state)
    return TestClient(app)


# ── Tests /health ─────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_status_ok(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_has_timestamp(self, client: TestClient) -> None:
        r = client.get("/health")
        assert "timestamp" in r.json()


# ── Tests /status ─────────────────────────────────────────────────────────────

class TestStatusEndpoint:
    def test_status_returns_200(self, client: TestClient) -> None:
        assert client.get("/status").status_code == 200

    def test_status_has_cycle(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/status").json()
        assert data["cycle"] == state.cycle

    def test_status_has_regime(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/status").json()
        assert data["regime"] == state.regime

    def test_status_has_equity(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/status").json()
        assert data["equity"] == pytest.approx(state.equity)

    def test_status_has_paused_field(self, client: TestClient) -> None:
        data = client.get("/status").json()
        assert "paused" in data

    def test_status_not_paused_initially(self, client: TestClient) -> None:
        data = client.get("/status").json()
        assert data["paused"] is False

    def test_status_has_circuit_breaker_ok(self, client: TestClient) -> None:
        data = client.get("/status").json()
        assert data["circuit_breaker_ok"] is True


# ── Tests /paper ──────────────────────────────────────────────────────────────

class TestPaperEndpoint:
    def test_paper_returns_200(self, client: TestClient) -> None:
        assert client.get("/paper").status_code == 200

    def test_paper_equity(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/paper").json()
        assert data["equity"] == pytest.approx(state.equity)

    def test_paper_pnl(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/paper").json()
        assert data["pnl"] == pytest.approx(state.pnl)

    def test_paper_win_rate(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/paper").json()
        assert data["win_rate"] == pytest.approx(state.win_rate)

    def test_paper_trades_count(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/paper").json()
        assert data["trades_count"] == state.trades_count

    def test_paper_has_timestamp(self, client: TestClient) -> None:
        assert "timestamp" in client.get("/paper").json()


# ── Tests /config ─────────────────────────────────────────────────────────────

class TestConfigEndpoint:
    def test_config_get_returns_200(self, client: TestClient) -> None:
        assert client.get("/config").status_code == 200

    def test_config_has_api_enabled(self, client: TestClient) -> None:
        data = client.get("/config").json()
        assert "api_enabled" in data

    def test_config_has_max_cycles(self, client: TestClient) -> None:
        data = client.get("/config").json()
        assert data["max_cycles"] == 10

    def test_config_patch_sleep_seconds(self, client: TestClient) -> None:
        r = client.patch("/config", json={"sleep_seconds": 5})
        assert r.status_code == 200
        applied = r.json()["applied"]
        assert applied["sleep_seconds"] == 5

    def test_config_patch_reflects_in_get(self, client: TestClient) -> None:
        client.patch("/config", json={"report_enabled": True})
        data = client.get("/config").json()
        assert data["report_enabled"] is True

    def test_config_patch_empty_body_returns_400(self, client: TestClient) -> None:
        r = client.patch("/config", json={})
        assert r.status_code == 400

    def test_config_patch_max_cycles(self, client: TestClient) -> None:
        r = client.patch("/config", json={"max_cycles": 20})
        assert r.status_code == 200
        assert r.json()["applied"]["max_cycles"] == 20

    def test_config_patch_multiple_fields(self, client: TestClient) -> None:
        r = client.patch("/config", json={"sleep_seconds": 3, "display_frequency": 2})
        assert r.status_code == 200
        applied = r.json()["applied"]
        assert applied["sleep_seconds"] == 3
        assert applied["display_frequency"] == 2


# ── Tests /scoreboard ─────────────────────────────────────────────────────────

class TestScoreboardEndpoint:
    def test_scoreboard_returns_200(self, client: TestClient) -> None:
        assert client.get("/scoreboard").status_code == 200

    def test_scoreboard_has_count(self, client: TestClient) -> None:
        data = client.get("/scoreboard").json()
        assert "count" in data

    def test_scoreboard_count_matches_strategies(self, client: TestClient) -> None:
        data = client.get("/scoreboard").json()
        assert data["count"] == len(data["strategies"])

    def test_scoreboard_top_filled(self, client: TestClient, state: SystemState) -> None:
        data = client.get("/scoreboard").json()
        assert data["count"] == len(state.scoreboard_top)

    def test_scoreboard_has_timestamp(self, client: TestClient) -> None:
        assert "timestamp" in client.get("/scoreboard").json()


# ── Tests /pause et /resume ───────────────────────────────────────────────────

class TestPauseResumeEndpoints:
    def test_pause_returns_200(self, client: TestClient) -> None:
        assert client.post("/pause").status_code == 200

    def test_pause_sets_paused_true(self, client: TestClient, state: SystemState) -> None:
        client.post("/pause")
        assert state.is_paused() is True

    def test_pause_response_has_paused_true(self, client: TestClient) -> None:
        data = client.post("/pause").json()
        assert data["paused"] is True
        assert data["status"] == "paused"

    def test_resume_returns_200(self, client: TestClient) -> None:
        client.post("/pause")
        assert client.post("/resume").status_code == 200

    def test_resume_sets_paused_false(self, client: TestClient, state: SystemState) -> None:
        client.post("/pause")
        client.post("/resume")
        assert state.is_paused() is False

    def test_resume_response_has_paused_false(self, client: TestClient) -> None:
        client.post("/pause")
        data = client.post("/resume").json()
        assert data["paused"] is False
        assert data["status"] == "running"

    def test_pause_then_status_reflects_pause(self, client: TestClient) -> None:
        client.post("/pause")
        data = client.get("/status").json()
        assert data["paused"] is True

    def test_resume_then_status_reflects_running(self, client: TestClient) -> None:
        client.post("/pause")
        client.post("/resume")
        data = client.get("/status").json()
        assert data["paused"] is False


# ── Tests SystemState ─────────────────────────────────────────────────────────

class TestSystemState:
    def test_update_modifies_field(self) -> None:
        s = SystemState()
        s.update(cycle=7)
        assert s.cycle == 7

    def test_update_ignores_private_fields(self) -> None:
        s = SystemState()
        original_lock = s._lock
        s.update(_lock="oops")  # doit être ignoré
        assert s._lock is original_lock

    def test_snapshot_returns_dict(self) -> None:
        s = SystemState(cycle=3, regime="bear")
        snap = s.snapshot()
        assert snap["cycle"] == 3
        assert snap["regime"] == "bear"

    def test_pause_resume(self) -> None:
        s = SystemState()
        assert s.is_paused() is False
        s.pause()
        assert s.is_paused() is True
        s.resume()
        assert s.is_paused() is False

    def test_snapshot_does_not_include_lock(self) -> None:
        s = SystemState()
        snap = s.snapshot()
        assert "_lock" not in snap


# ── Tests RuntimeConfig champs AE ─────────────────────────────────────────────

class TestAPIRuntimeConfig:
    def test_api_fields_exist(self) -> None:
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert hasattr(cfg, "api_enabled")
        assert hasattr(cfg, "api_host")
        assert hasattr(cfg, "api_port")

    def test_api_defaults(self) -> None:
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.api_enabled is False
        assert cfg.api_host == "0.0.0.0"
        assert cfg.api_port == 8000

    def test_api_env_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from runtime_config import load_runtime_config_from_env
        monkeypatch.setenv("V9_API_ENABLED", "true")
        monkeypatch.setenv("V9_API_HOST", "127.0.0.1")
        monkeypatch.setenv("V9_API_PORT", "9001")
        cfg = load_runtime_config_from_env()
        assert cfg.api_enabled is True
        assert cfg.api_host == "127.0.0.1"
        assert cfg.api_port == 9001

    def test_api_in_as_dict(self) -> None:
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "api_enabled" in d
        assert "api_host" in d
        assert "api_port" in d
