import panel as pn
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any, Mapping, Sequence, cast

from core.orchestrator import run_cycle, CLUSTER_METRICS

pn.extension("plotly", sizing_mode="stretch_width")


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(cast(Any, value))
    except (TypeError, ValueError):
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return default


def _to_dict(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _to_list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _candles_from_prices(prices: list[float]) -> go.Figure:
    if not prices:
        prices = [100 + i * 0.1 for i in range(120)]

    opens = prices[:-1]
    closes = prices[1:]
    highs = [max(o, c) * 1.002 for o, c in zip(opens, closes)]
    lows = [min(o, c) * 0.998 for o, c in zip(opens, closes)]

    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(
        go.Candlestick(
            x=list(range(len(opens))),
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name="Price",
        )
    )
    fig.update_layout(height=420, template="plotly_dark", margin=dict(l=20, r=20, t=30, b=20))
    return fig


class QuantDashboardV13:
    def __init__(self):
        self.market_table = pn.widgets.Tabulator(pd.DataFrame(), height=280)
        self.best_table = pn.widgets.Tabulator(pd.DataFrame(), height=280)
        self.portfolio_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)
        self.orders_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)

        self.risk_indicator = pn.indicators.String(name="Risk", value="OK")
        self.regime_indicator = pn.indicators.String(name="Regime", value="NORMAL")
        self.metrics_indicator = pn.indicators.String(name="System", value="Idle")

        self.chart = pn.pane.Plotly(_candles_from_prices([]), height=430)

        # Cluster Status panel
        self.cluster_pane = pn.pane.Markdown(self._cluster_md(), width=700)
        self.cluster_tasks_table = pn.widgets.Tabulator(
            pd.DataFrame(columns=["metric", "value"]), height=240
        )

        self.refresh_btn = pn.widgets.Button(name="Run V13 Cycle", button_type="primary")
        self.refresh_btn.on_click(self.refresh)

        self.layout = pn.template.FastListTemplate(
            title="AI Quant Control Center V13",
            main=[
                pn.Row(self.refresh_btn, self.risk_indicator, self.regime_indicator, self.metrics_indicator),
                pn.Tabs(
                    ("Market Scanner", self.market_table),
                    ("Live Candlestick Charts", self.chart),
                    ("Strategy Lab", self.best_table),
                    ("Portfolio", self.portfolio_table),
                    ("Risk Engine", pn.Column(self.risk_indicator)),
                    ("Agents Monitor", self.orders_table),
                    ("Cluster Status", pn.Column(self.cluster_pane, self.cluster_tasks_table)),
                ),
            ],
            theme="dark",
        )

        self.refresh()

    # ------------------------------------------------------------------
    def _cluster_md(self) -> str:
        m = CLUSTER_METRICS
        workers = _to_int(m.get("workers_active", 0))
        tasks = _to_int(m.get("tasks_completed", 0))
        avg_ms = _to_float(m.get("avg_backtest_ms", 0.0))
        cycles = _to_int(m.get("cycles", 0))
        sharpe = _to_float(m.get("last_best_sharpe", 0.0))
        regime = str(m.get("last_regime", "N/A"))
        risk = str(m.get("last_risk", "N/A"))
        return (
            "## Cluster Status\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Workers Active | **{workers}** |\n"
            f"| Tasks Completed | **{tasks}** |\n"
            f"| Avg Backtest Time | **{avg_ms:.1f} ms** |\n"
            f"| Cycles Run | **{cycles}** |\n"
            f"| Last Best Sharpe | **{sharpe:.4f}** |\n"
            f"| Last Regime | **{regime}** |\n"
            f"| Last Risk | **{risk}** |\n"
        )

    def _cluster_df(self) -> pd.DataFrame:
        m = CLUSTER_METRICS
        rows = [
            {"metric": "workers_active", "value": _to_int(m.get("workers_active", 0))},
            {"metric": "tasks_completed", "value": _to_int(m.get("tasks_completed", 0))},
            {"metric": "avg_backtest_ms", "value": round(_to_float(m.get("avg_backtest_ms", 0.0)), 1)},
            {"metric": "cycles_run", "value": _to_int(m.get("cycles", 0))},
            {"metric": "last_best_sharpe", "value": round(_to_float(m.get("last_best_sharpe", 0.0)), 4)},
            {"metric": "last_regime", "value": str(m.get("last_regime", "N/A"))},
            {"metric": "last_risk", "value": str(m.get("last_risk", "N/A"))},
        ]
        return pd.DataFrame(rows)

    def refresh(self, *_) -> None:
        result_raw = run_cycle(strategy_count=120, top_k=10)
        result = _to_dict(result_raw)
        market_size = _to_int(result.get("market_size", 0))

        market_df = pd.DataFrame(
            [
                {"metric": "market_size", "value": market_size},
                {"metric": "regime", "value": str(result.get("regime", "UNKNOWN"))},
            ]
        )
        self.market_table.value = market_df

        best_rows = []
        for item in _to_list(result.get("best_strategies", [])):
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            strategy, score = item
            strategy_dict = _to_dict(strategy)
            best_rows.append(
                {
                    "indicator": str(strategy_dict.get("indicator", "unknown")),
                    "period": _to_int(strategy_dict.get("period", 0)),
                    "sharpe": round(_to_float(score, 0.0), 4),
                }
            )
        self.best_table.value = pd.DataFrame(best_rows)

        allocation = _to_dict(result.get("allocation", {}))
        orders = _to_list(result.get("orders", []))
        risk = _to_dict(result.get("risk", {}))

        self.portfolio_table.value = pd.DataFrame(
            [{"asset": str(k), "weight": round(_to_float(v, 0.0), 4)} for k, v in allocation.items()]
        )
        self.orders_table.value = pd.DataFrame(orders)

        synthetic_prices = [100 + i * 0.05 for i in range(150)]
        self.chart.object = _candles_from_prices(synthetic_prices)

        risk_status = str(risk.get("status", "UNKNOWN"))
        self.risk_indicator.value = risk_status
        self.regime_indicator.value = str(result.get("regime", "UNKNOWN"))
        self.metrics_indicator.value = f"Scanned: {market_size} | Strategies: 120 | Top: 10"

        # Refresh cluster status pane
        self.cluster_pane.object = self._cluster_md()
        self.cluster_tasks_table.value = self._cluster_df()


def main():
    app = QuantDashboardV13()
    app.layout.servable()


if __name__.startswith("bokeh"):
    main()

if __name__ == "__main__":
    main()
