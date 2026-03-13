"""
Quant Dashboard V16 – Main Panel application
Real-time crypto trading monitoring and control center
"""

import logging
from dataclasses import dataclass
from datetime import datetime

import panel as pn
import pandas as pd

from ui.components import (
    create_candlestick_chart,
    create_equity_curve,
    create_kpi_indicators,
    create_market_table,
    create_portfolio_pie,
)

pn.extension("plotly", sizing_mode="stretch_width")

LOGGER = logging.getLogger(__name__)

COIN_OPTIONS = ("BTC", "ETH", "SOL", "AVAX", "LINK")
TIMEFRAME_OPTIONS = ("5m", "15m", "1h", "4h", "1d")


@dataclass(frozen=True)
class DashboardMetrics:
    """Static KPI values shown in the header."""

    best_sharpe: float = 2.45
    max_dd: float = 0.12
    active_signals: int = 18

    def as_dict(self) -> dict[str, float | int]:
        return {
            "best_sharpe": self.best_sharpe,
            "max_dd": self.max_dd,
            "active_signals": self.active_signals,
        }


class QuantDashboard:
    """Main Quant V16 Dashboard"""

    def __init__(self):
        """Initialize dashboard"""
        self.refresh_count = 0
        self.market_data = pd.DataFrame()
        self.portfolio_value = 10000
        self.equity_curve = [10000]

        self._setup_layout()

    def _setup_layout(self):
        """Setup dashboard layout"""
        header = self._build_header()
        controls = self._build_controls()
        tabs = self._build_tabs()
        sidebar = self._build_sidebar()

        self.layout = pn.template.FastListTemplate(
            title="🚀 AI QUANT CONTROL CENTER V16",
            header_background="#00ff9f",
            main=[header, controls, tabs],
            theme="dark",
            sidebar=[sidebar],
        )

    def _build_header(self):
        """Create dashboard KPI area."""
        return create_kpi_indicators(DashboardMetrics().as_dict())

    def _build_controls(self):
        """Create top-level control widgets."""
        self.coin_select = pn.widgets.Select(
            name="Select Coin",
            value="BTC",
            options=COIN_OPTIONS,
        )
        self.timeframe_select = pn.widgets.Select(
            name="Timeframe",
            value="1h",
            options=TIMEFRAME_OPTIONS,
        )
        self.refresh_btn = pn.widgets.Button(
            name="🔄 Refresh Now",
            button_type="success",
        )
        self.refresh_btn.on_click(self._on_refresh)

        return pn.Column(
            pn.Row(self.coin_select, self.timeframe_select, self.refresh_btn),
            width=1200,
        )

    def _build_tabs(self):
        """Create dashboard tab set."""
        market_table = create_market_table(self.market_data)
        candlestick = pn.pane.Plotly(create_candlestick_chart({}), height=600)
        portfolio_pie = pn.pane.Plotly(create_portfolio_pie({}), height=400)
        equity_chart = pn.pane.Plotly(create_equity_curve(self.equity_curve), height=500)

        return pn.Tabs(
            ("🌐 Market", market_table),
            ("📈 Charts", candlestick),
            ("💼 Portfolio", pn.Column(portfolio_pie, equity_chart)),
            ("⚠️ Risk", pn.pane.Markdown("## Risk Monitor\nRisk limits OK")),
            ("🐋 Whales", pn.pane.Markdown("## Whale Radar\nNo anomalies")),
            ("🤖 Agents", pn.pane.Markdown("## AI Agents Status\nAll active")),
            (
                "📊 Strategy Lab",
                pn.pane.Markdown("## Strategy Lab\nTesting strategies..."),
            ),
            width=1200,
            height=700,
        )

    def _build_sidebar(self):
        """Create status sidebar with static operational context."""
        return pn.pane.Markdown(
            """
### V16 Status

- Connected to Binance
- 300+ cryptos scanned
- 4 agents running
- Port: 5011
            """.strip()
        )

    def _on_refresh(self, *events):
        """Refresh callback"""
        self.refresh_count += 1
        LOGGER.info(
            "Refresh %s at %s",
            self.refresh_count,
            datetime.now().isoformat(timespec="seconds"),
        )

    def show(self):
        """Display dashboard"""
        return self.layout

    def get_layout(self):
        """Return layout for serving"""
        return self.layout


# Initialize and serve dashboard
dashboard = QuantDashboard()
dashboard.get_layout().servable()
