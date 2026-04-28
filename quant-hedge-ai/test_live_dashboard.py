"""
Tests option AH — Dashboard live equity curve.

Teste sans lancer de vrai serveur Panel (mock des imports panel/plotly).
Vérifie : SystemState equity_history, RuntimeConfig, logique LiveDashboard.
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from agents.api.system_state import SystemState


# ── Helpers pour mocker Panel/Plotly ──────────────────────────────────────────

def _make_panel_mock() -> types.ModuleType:
    """Crée un mock minimal de panel pour les tests sans UI."""
    pn = types.ModuleType("panel")
    pn.extension = MagicMock()
    pn.state = MagicMock()
    pn.state.add_periodic_callback = MagicMock(return_value=MagicMock())
    pn.state.curdoc = None

    for cls_name in ("Row", "Column", "Divider"):
        setattr(pn, cls_name, MagicMock(return_value=MagicMock()))

    pn.pane = MagicMock()
    pn.pane.Markdown = MagicMock(return_value=MagicMock())
    pn.pane.Plotly = MagicMock(return_value=MagicMock())

    pn.indicators = MagicMock()
    pn.indicators.Number = MagicMock(return_value=MagicMock())

    pn.layout = MagicMock()
    pn.layout.Divider = MagicMock(return_value=MagicMock())

    pn.template = MagicMock()
    pn.template.FastDarkTemplate = MagicMock(return_value=MagicMock())

    pn.serve = MagicMock()
    return pn


def _make_plotly_mock() -> types.ModuleType:
    go = types.ModuleType("plotly.graph_objects")
    go.Figure = MagicMock(return_value=MagicMock(
        add_trace=MagicMock(), add_hline=MagicMock(), update_layout=MagicMock()
    ))
    go.Scatter = MagicMock(return_value=MagicMock())
    plotly = types.ModuleType("plotly")
    plotly.graph_objects = go
    return plotly, go


# ── Tests SystemState — equity_history ────────────────────────────────────────

class TestSystemStateEquityHistory:
    def test_initial_history_empty(self) -> None:
        s = SystemState()
        assert s.equity_history == []

    def test_push_equity_point_adds_entry(self) -> None:
        s = SystemState()
        s.push_equity_point(cycle=1, equity=100_000.0, pnl=0.0, drawdown_pct=0.0)
        history = s.get_equity_history()
        assert len(history) == 1
        assert history[0]["cycle"] == 1
        assert history[0]["equity"] == 100_000.0

    def test_push_multiple_points(self) -> None:
        s = SystemState()
        for i in range(5):
            s.push_equity_point(cycle=i + 1, equity=100_000.0 + i * 1000, pnl=float(i * 100), drawdown_pct=0.0)
        assert len(s.get_equity_history()) == 5

    def test_history_is_bounded(self) -> None:
        s = SystemState(equity_history_max=10)
        for i in range(20):
            s.push_equity_point(cycle=i + 1, equity=float(i), pnl=0.0, drawdown_pct=0.0)
        history = s.get_equity_history()
        assert len(history) == 10
        # Doit conserver les derniers points
        assert history[-1]["cycle"] == 20

    def test_get_equity_history_returns_copy(self) -> None:
        s = SystemState()
        s.push_equity_point(cycle=1, equity=100.0, pnl=0.0, drawdown_pct=0.0)
        h1 = s.get_equity_history()
        h1.clear()
        h2 = s.get_equity_history()
        assert len(h2) == 1  # l'original n'est pas modifié

    def test_point_has_all_fields(self) -> None:
        s = SystemState()
        s.push_equity_point(cycle=3, equity=105_000.0, pnl=5_000.0, drawdown_pct=1.5)
        pt = s.get_equity_history()[0]
        assert set(pt.keys()) == {"cycle", "equity", "pnl", "drawdown_pct"}
        assert pt["drawdown_pct"] == pytest.approx(1.5)

    def test_thread_safe_push(self) -> None:
        """Plusieurs threads poussent des points sans corruption."""
        import threading
        s = SystemState(equity_history_max=1000)
        errors: list[Exception] = []

        def push_many(start: int) -> None:
            try:
                for i in range(50):
                    s.push_equity_point(cycle=start + i, equity=float(start + i), pnl=0.0, drawdown_pct=0.0)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=push_many, args=(i * 100,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(s.get_equity_history()) == 200  # 4 × 50


# ── Tests RuntimeConfig champs AH ─────────────────────────────────────────────

class TestAHRuntimeConfig:
    def test_dashboard_fields_exist(self) -> None:
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert hasattr(cfg, "dashboard_live_enabled")
        assert hasattr(cfg, "dashboard_live_port")
        assert hasattr(cfg, "dashboard_live_refresh_ms")

    def test_dashboard_defaults(self) -> None:
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.dashboard_live_enabled is False
        assert cfg.dashboard_live_port == 5012
        assert cfg.dashboard_live_refresh_ms == 2000

    def test_dashboard_env_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from runtime_config import load_runtime_config_from_env
        monkeypatch.setenv("V9_DASHBOARD_LIVE_ENABLED", "true")
        monkeypatch.setenv("V9_DASHBOARD_LIVE_PORT", "5099")
        monkeypatch.setenv("V9_DASHBOARD_LIVE_REFRESH_MS", "500")
        cfg = load_runtime_config_from_env()
        assert cfg.dashboard_live_enabled is True
        assert cfg.dashboard_live_port == 5099
        assert cfg.dashboard_live_refresh_ms == 500

    def test_dashboard_in_as_dict(self) -> None:
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "dashboard_live_enabled" in d
        assert "dashboard_live_port" in d
        assert "dashboard_live_refresh_ms" in d


# ── Tests LiveDashboard (avec mocks panel/plotly) ─────────────────────────────

class TestLiveDashboard:
    @pytest.fixture(autouse=True)
    def mock_panel_plotly(self, monkeypatch: pytest.MonkeyPatch):
        """Injecte des mocks panel et plotly avant chaque test."""
        pn_mock = _make_panel_mock()
        plotly_mock, go_mock = _make_plotly_mock()

        monkeypatch.setitem(sys.modules, "panel", pn_mock)
        monkeypatch.setitem(sys.modules, "plotly", plotly_mock)
        monkeypatch.setitem(sys.modules, "plotly.graph_objects", go_mock)

        # Recharger le module avec les mocks
        import importlib
        import dashboard.live_dashboard as _mod
        monkeypatch.setattr(_mod, "_PANEL_AVAILABLE", True)
        monkeypatch.setattr(_mod, "pn", pn_mock)
        monkeypatch.setattr(_mod, "go", go_mock)
        yield pn_mock, go_mock

    def test_live_dashboard_init_does_not_crash(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState(equity=100_000.0, cycle=1)
        d = LiveDashboard(state=state, refresh_ms=1000)
        assert d is not None

    def test_live_dashboard_refresh_calls_snapshot(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState(equity=100_000.0, cycle=5, regime="bull_trend")
        d = LiveDashboard(state=state)
        d._refresh()  # appel manuel

    def test_live_dashboard_refresh_with_history(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState()
        for i in range(10):
            state.push_equity_point(cycle=i + 1, equity=100_000 + i * 500, pnl=float(i * 50), drawdown_pct=0.0)
        d = LiveDashboard(state=state)
        d._refresh()

    def test_build_equity_figure_empty(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState()
        d = LiveDashboard(state=state)
        fig = d._build_equity_figure([])
        assert fig is not None

    def test_build_equity_figure_with_data(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState()
        d = LiveDashboard(state=state)
        history = [{"cycle": i, "equity": 100_000 + i * 100, "pnl": 0.0, "drawdown_pct": 0.0}
                   for i in range(5)]
        fig = d._build_equity_figure(history)
        assert fig is not None

    def test_build_dd_figure_empty(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState()
        d = LiveDashboard(state=state)
        fig = d._build_dd_figure([])
        assert fig is not None

    def test_servable_returns_template(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState()
        d = LiveDashboard(state=state)
        tmpl = d.servable()
        assert tmpl is not None

    def test_refresh_with_paused_state(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState(paused=True, cycle=3, regime="bear")
        d = LiveDashboard(state=state)
        d._refresh()  # ne doit pas crasher

    def test_refresh_with_scoreboard(self, mock_panel_plotly) -> None:
        from dashboard.live_dashboard import LiveDashboard
        state = SystemState()
        state.update(scoreboard_top=[
            {"type": "BOLLINGER → MACD", "sharpe": 3.45},
            {"type": "EMA → EMA", "sharpe": 2.90},
        ])
        d = LiveDashboard(state=state)
        d._refresh()

    def test_panel_not_available_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import dashboard.live_dashboard as _mod
        monkeypatch.setattr(_mod, "_PANEL_AVAILABLE", False)
        with pytest.raises(ImportError, match="panel"):
            from dashboard.live_dashboard import LiveDashboard
            LiveDashboard()


# ── Tests start_live_dashboard ────────────────────────────────────────────────

class TestStartLiveDashboard:
    def test_start_live_dashboard_launches_thread(self, monkeypatch: pytest.MonkeyPatch) -> None:
        pn_mock = _make_panel_mock()
        plotly_mock, go_mock = _make_plotly_mock()
        monkeypatch.setitem(sys.modules, "panel", pn_mock)
        monkeypatch.setitem(sys.modules, "plotly", plotly_mock)
        monkeypatch.setitem(sys.modules, "plotly.graph_objects", go_mock)

        import dashboard.live_dashboard as _mod
        monkeypatch.setattr(_mod, "_PANEL_AVAILABLE", True)
        monkeypatch.setattr(_mod, "pn", pn_mock)
        monkeypatch.setattr(_mod, "go", go_mock)

        # Patch pn.serve pour ne pas vraiment lancer
        pn_mock.serve = MagicMock()

        from dashboard.live_dashboard import start_live_dashboard
        state = SystemState()
        t = start_live_dashboard(host="127.0.0.1", port=9999, refresh_ms=1000, state=state)
        assert t.daemon is True
        assert t.name == "v91-live-dashboard"
