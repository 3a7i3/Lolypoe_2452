"""
Option AH — Dashboard live equity curve (Panel + Plotly).

Lance un serveur Panel autonome qui lit le SystemState partagé
et se rafraîchit automatiquement toutes les N millisecondes.

Usage autonome :
    panel serve dashboard/live_dashboard.py --port 5012 --show

Usage programmatique (main_v91.py) :
    from dashboard.live_dashboard import start_live_dashboard
    start_live_dashboard(host="0.0.0.0", port=5012)
"""
from __future__ import annotations

import threading
from typing import Any

try:
    import panel as pn
    import plotly.graph_objects as go
    _PANEL_AVAILABLE = True
except ImportError:
    _PANEL_AVAILABLE = False

from agents.api.system_state import SystemState, get_state


# ── Constantes ────────────────────────────────────────────────────────────────

_DARK_BG = "#1a1a2e"
_CARD_BG = "#16213e"
_ACCENT = "#0f3460"
_GREEN = "#00d4aa"
_RED = "#e94560"
_YELLOW = "#f5a623"
_WHITE = "#e0e0e0"
_FONT = "Courier New, monospace"


# ── Composants Panel ──────────────────────────────────────────────────────────

class LiveDashboard:
    """
    Dashboard Panel temps réel : equity curve, métriques, statut système.

    Fonctionne avec ou sans données réelles (affiche des placeholders si vide).
    """

    def __init__(self, state: SystemState | None = None, refresh_ms: int = 2000) -> None:
        self._state = state or get_state()
        self._refresh_ms = refresh_ms

        if not _PANEL_AVAILABLE:
            raise ImportError("panel et plotly sont requis pour le dashboard live (pip install panel plotly)")

        pn.extension("plotly", sizing_mode="stretch_width", theme="dark")
        self._build()

    # ── Construction des widgets ───────────────────────────────────────────────

    def _build(self) -> None:
        """Initialise tous les widgets Panel."""
        # Métriques statiques (indicateurs)
        self._equity_ind = pn.indicators.Number(
            name="Equity ($)", value=0.0, format="{value:,.0f}",
            colors=[(0, _RED), (90_000, _YELLOW), (100_000, _GREEN)],
            font_size="28pt", title_size="12pt",
        )
        self._pnl_ind = pn.indicators.Number(
            name="PnL ($)", value=0.0, format="{value:+,.0f}",
            colors=[(-1e9, _RED), (0, _GREEN)],
            font_size="24pt", title_size="12pt",
        )
        self._dd_ind = pn.indicators.Number(
            name="Drawdown (%)", value=0.0, format="{value:.2f}%",
            colors=[(0, _GREEN), (5, _YELLOW), (10, _RED)],
            font_size="24pt", title_size="12pt",
        )
        self._winrate_ind = pn.indicators.Number(
            name="Win Rate", value=0.0, format="{value:.1%}",
            colors=[(0, _RED), (0.4, _YELLOW), (0.5, _GREEN)],
            font_size="24pt", title_size="12pt",
        )

        # Texte statut
        self._status_md = pn.pane.Markdown("**Démarrage...**", styles={"color": _WHITE, "font-family": _FONT})

        # Graphique equity curve
        self._equity_fig = pn.pane.Plotly(self._build_equity_figure([]), sizing_mode="stretch_width", height=320)

        # Graphique drawdown
        self._dd_fig = pn.pane.Plotly(self._build_dd_figure([]), sizing_mode="stretch_width", height=200)

        # Scoreboard table
        self._scoreboard_md = pn.pane.Markdown("*Scoreboard vide*", styles={"font-family": _FONT})

        # Callback de rafraîchissement périodique
        self._cb = pn.state.add_periodic_callback(self._refresh, period=self._refresh_ms, start=True)

    # ── Figures Plotly ─────────────────────────────────────────────────────────

    def _build_equity_figure(self, history: list[dict[str, Any]]) -> go.Figure:
        cycles = [p["cycle"] for p in history]
        equities = [p["equity"] for p in history]

        fig = go.Figure()
        if cycles:
            fig.add_trace(go.Scatter(
                x=cycles, y=equities,
                mode="lines+markers",
                line=dict(color=_GREEN, width=2),
                marker=dict(size=4),
                name="Equity",
                hovertemplate="Cycle %{x}<br>$%{y:,.0f}<extra></extra>",
            ))
            # Ligne de base (capital initial)
            initial = history[0]["equity"]
            fig.add_hline(y=initial, line_dash="dot", line_color=_YELLOW, opacity=0.5)

        fig.update_layout(
            title=dict(text="📈 Equity Curve", font=dict(color=_WHITE, size=16)),
            paper_bgcolor=_CARD_BG,
            plot_bgcolor=_CARD_BG,
            font=dict(color=_WHITE, family=_FONT),
            xaxis=dict(title="Cycle", gridcolor=_ACCENT, showgrid=True),
            yaxis=dict(title="Equity ($)", gridcolor=_ACCENT, showgrid=True, tickformat="$,.0f"),
            margin=dict(l=60, r=20, t=50, b=40),
            showlegend=False,
        )
        return fig

    def _build_dd_figure(self, history: list[dict[str, Any]]) -> go.Figure:
        cycles = [p["cycle"] for p in history]
        dds = [p["drawdown_pct"] for p in history]

        fig = go.Figure()
        if cycles:
            fig.add_trace(go.Scatter(
                x=cycles, y=dds,
                mode="lines",
                fill="tozeroy",
                line=dict(color=_RED, width=1.5),
                fillcolor="rgba(233,69,96,0.2)",
                name="Drawdown",
                hovertemplate="Cycle %{x}<br>DD: %{y:.2f}%<extra></extra>",
            ))
            fig.add_hline(y=5, line_dash="dot", line_color=_YELLOW, opacity=0.6,
                          annotation_text="⚠ 5%", annotation_position="right")
            fig.add_hline(y=10, line_dash="dot", line_color=_RED, opacity=0.6,
                          annotation_text="🛑 10%", annotation_position="right")

        fig.update_layout(
            title=dict(text="📉 Drawdown (%)", font=dict(color=_WHITE, size=14)),
            paper_bgcolor=_CARD_BG,
            plot_bgcolor=_CARD_BG,
            font=dict(color=_WHITE, family=_FONT),
            xaxis=dict(title="Cycle", gridcolor=_ACCENT, showgrid=True),
            yaxis=dict(title="DD (%)", gridcolor=_ACCENT, showgrid=True),
            margin=dict(l=60, r=60, t=40, b=40),
            showlegend=False,
        )
        return fig

    # ── Rafraîchissement ───────────────────────────────────────────────────────

    def _refresh(self) -> None:
        """Appelé périodiquement par Panel — lit l'état et met à jour les widgets."""
        snap = self._state.snapshot()
        history = self._state.get_equity_history()

        # Indicateurs numériques
        self._equity_ind.value = snap.get("equity", 0.0)
        self._pnl_ind.value = snap.get("pnl", 0.0)
        self._dd_ind.value = snap.get("drawdown_pct", 0.0)
        self._winrate_ind.value = snap.get("win_rate", 0.0)

        # Statut texte
        status_icon = "⏸" if snap.get("paused") else "🟢"
        cb_icon = "🔴" if not snap.get("circuit_breaker_ok", True) else "✅"
        self._status_md.object = (
            f"**{status_icon} Cycle {snap.get('cycle', 0)}/{snap.get('max_cycles', 0)}** | "
            f"Régime: `{snap.get('regime', 'unknown')}` | "
            f"Symbole: `{snap.get('symbol', '—')}` | "
            f"Source: `{snap.get('data_source', '—')}` | "
            f"CB: {cb_icon} | "
            f"Stratégie: `{snap.get('best_strategy_type', '—')}` "
            f"Sharpe={snap.get('best_sharpe', 0.0):.2f} | "
            f"Mis à jour: `{snap.get('last_updated', '—')}`"
        )

        # Mise à jour des graphiques
        self._equity_fig.object = self._build_equity_figure(history)
        self._dd_fig.object = self._build_dd_figure(history)

        # Scoreboard
        with self._state._lock:
            top = list(self._state.scoreboard_top)
        if top:
            rows = "\n".join(
                f"| {i+1} | {s.get('type', s.get('strategy_type', '?'))} | {s.get('sharpe', 0.0):.3f} |"
                for i, s in enumerate(top)
            )
            self._scoreboard_md.object = (
                "### 🏆 Top Stratégies\n"
                "| # | Type | Sharpe |\n|---|------|--------|\n" + rows
            )
        else:
            self._scoreboard_md.object = "*Scoreboard vide (en attente de cycles...)*"

    # ── Layout Panel ───────────────────────────────────────────────────────────

    def servable(self) -> pn.template.FastDarkTemplate:
        """Retourne le template Panel prêt à être servi."""
        metrics_row = pn.Row(
            self._equity_ind, self._pnl_ind, self._dd_ind, self._winrate_ind,
            sizing_mode="stretch_width",
        )
        layout = pn.Column(
            pn.pane.Markdown("# 🤖 Quant Hedge AI — Live Dashboard V9.1",
                             styles={"color": _WHITE, "font-family": _FONT}),
            self._status_md,
            pn.layout.Divider(),
            metrics_row,
            self._equity_fig,
            self._dd_fig,
            pn.layout.Divider(),
            self._scoreboard_md,
            sizing_mode="stretch_width",
        )
        template = pn.template.FastDarkTemplate(
            title="Quant Hedge AI V9.1",
            main=[layout],
        )
        return template


# ── Lancement en thread daemon ─────────────────────────────────────────────────

def start_live_dashboard(
    host: str = "0.0.0.0",
    port: int = 5012,
    refresh_ms: int = 2000,
    state: SystemState | None = None,
) -> threading.Thread:
    """
    Lance le serveur Panel dans un thread daemon.
    Retourne le thread (non-bloquant).
    """
    if not _PANEL_AVAILABLE:
        raise ImportError("panel et plotly sont requis : pip install panel plotly")

    def _run() -> None:
        dashboard = LiveDashboard(state=state, refresh_ms=refresh_ms)
        tmpl = dashboard.servable()
        pn.serve(
            tmpl,
            address=host,
            port=port,
            show=False,
            allow_websocket_origin=["*"],
        )

    t = threading.Thread(target=_run, daemon=True, name="v91-live-dashboard")
    t.start()
    return t


# ── Point d'entrée standalone ──────────────────────────────────────────────────

if __name__ == "__main__" or pn.state.curdoc is not None:
    # Lancé via `panel serve dashboard/live_dashboard.py`
    if _PANEL_AVAILABLE:
        import sys
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
        _dashboard = LiveDashboard()
        _dashboard.servable().servable()
