from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Callable, Optional, cast

import panel as pn
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from v26.config import V26_CONFIG
from v26.data_simulator import (
    generate_human_trend_data,
    generate_ohlcv,
    generate_orderbook,
    get_data_source,
    get_data_meta,
    get_orderbook_meta,
)

_WS_UI_AVAILABLE = False
_ws_status: Optional[Callable[[str, str], str]] = None
_ws_candles_ready: Optional[Callable[[str, str], int]] = None
_ws_subscribe: Optional[Callable[[str, str], object]] = None
try:
    from v26.ws_feed import ws_status as _ws_status, ws_candles_ready as _ws_candles_ready, subscribe as _ws_subscribe
    _WS_UI_AVAILABLE = True
except Exception:
    pass

# V27.4 Telegram alerts + command loop (optional).
try:
    from v26.telegram_alerts import (
        send_alert as _tg_send,
        status_summary as _tg_status,
        start_command_loop as _tg_start_loop,
    )
    _TG_AVAILABLE = True
except Exception:
    _tg_send = None  # type: ignore[assignment]
    _tg_status = None  # type: ignore[assignment]
    _tg_start_loop = None  # type: ignore[assignment]
    _TG_AVAILABLE = False
from v26.paper_trading import PaperTrader
from v26.smart_chart import (
    detect_bos,
    detect_choch,
    detect_fvg_zones,
    detect_order_blocks_zones,
    detect_smart_money,
    detect_structure,
    enrich_indicators,
    orderbook_depth,
)
from v26.ai_assistant import detect_trend, generate_trade, momentum_signal, breakout_signal, volatility_state
from v26.debate_engine import DebateEngine, final_decision
from v26.strategy_evolution import evolve_population
from v26.market_brain import trend_ai, sentiment_ai, liquidity_ai, volatility_ai, fuse_market_state
from v26.regime_engine import detect_regime, choose_strategy
from v26.portfolio_brain import score_asset, allocate_portfolio, apply_risk_limits
from v26.multi_exchange import scan_prices, detect_arbitrage
from v26.human_trend_engine import aggregate_by_source, find_common_trends, predict_next_products, source_sentiment_snapshot
from v26.human_trend_engine import build_trend_score_history
from v26.bot_doctor import run_bot_doctor
from v26.runtime_profile import (
    PROFILE_RANGES,
    CUSTOM_PROFILE_NAME,
    load_saved_custom_profile,
    load_saved_custom_updated_at,
    load_saved_profile_name,
    load_saved_snapshot_schema_only,
    load_saved_snapshot_tag_filter,
    profile_for_dashboard,
    resolve_custom_profile,
    resolve_profile,
    save_custom_profile,
    save_profile_name,
    save_snapshot_schema_only,
    save_snapshot_tag_filter,
)

_CLUSTER_AVAILABLE = False
_CLUSTER_METRICS: dict[str, object] = {}
try:
    from core.orchestrator import CLUSTER_METRICS as _ORCH_CLUSTER_METRICS

    _CLUSTER_METRICS = _ORCH_CLUSTER_METRICS
    _CLUSTER_AVAILABLE = True
except Exception:
    pass

pn.extension("plotly", "tabulator", sizing_mode="stretch_width")


class SmartChartV26Dashboard:
    SNAPSHOT_SCHEMA_VERSION = 1
    SNAPSHOT_NOTES_MAX_LEN = 280
    SNAPSHOT_TAG_MAX_LEN = 32
    SNAPSHOT_TAG_FILTER_ALL = "all"
    SNAPSHOT_TAG_FILTER_UNTAGGED = "untagged"
    DRYRUN_CONFIRM_THRESHOLD = 4
    FEED_WARN_AGE_MULTIPLIER = 2.0
    FEED_CRITICAL_AGE_MULTIPLIER = 4.0
    FEED_WARN_LATENCY_MS = 1500.0
    FEED_CRITICAL_LATENCY_MS = 3000.0
    DRYRUN_FILTER_ALL = "all"
    DRYRUN_FILTER_INCREASE = "increase"
    DRYRUN_FILTER_DECREASE = "decrease"
    DOCTOR_HEALTH_WARN = 70.0
    DOCTOR_HEALTH_CRITICAL = 50.0
    DOCTOR_BURST_WINDOW = 5
    DOCTOR_BURST_ERROR_SPIKE = 3
    DOCTOR_BURST_WARNING_SPIKE = 6

    @staticmethod
    def _profile_change_tolerance(key: str) -> float:
        if key == "poll_seconds":
            return 0.5
        return 1e-6

    def _is_material_profile_change(self, key: str, current: float, incoming: float) -> bool:
        if key == "poll_seconds":
            return int(round(current)) != int(round(incoming))
        return abs(current - incoming) > self._profile_change_tolerance(key)

    def __init__(self) -> None:
        self.runtime_profile = profile_for_dashboard()
        self.symbol = pn.widgets.Select(name="Symbol", value=V26_CONFIG["symbol"], options=["BTC/USDT", "ETH/USDT", "SOL/USDT"]) 
        self.timeframe = pn.widgets.Select(name="Timeframe", value=V26_CONFIG["timeframe"], options=["5m", "15m", "1h", "4h", "1d"])
        self.exchange_feed = pn.widgets.Select(
            name="Exchange",
            value="binance",
            options=["binance", "bybit", "kucoin", "mexc", "kraken", "okx", "coinbase", "uniswap", "hyperliquid"],
        )
        self.exchange_data_mode = pn.widgets.Select(name="Data Mode", value="auto", options=["auto", "live", "mock"], width=110)
        self.profile_select = pn.widgets.Select(
            name="Profile",
            value=str(self.runtime_profile["name"]),
            options=["conservative", "balanced", "aggressive", CUSTOM_PROFILE_NAME],
            width=140,
        )
        self.profile_apply_btn = pn.widgets.Button(name="Apply Profile", button_type="primary", width=120)
        self.profile_save_btn = pn.widgets.Button(name="Save Default Profile", button_type="warning", width=160)
        self.profile_save_apply_custom_btn = pn.widgets.Button(name="Save + Apply Custom", button_type="success", width=160)
        self.profile_reset_custom_btn = pn.widgets.Button(name="Reset Custom to Balanced", button_type="light", width=180)
        self.profile_clone_source = pn.widgets.Select(
            name="Clone From",
            value="balanced",
            options=["conservative", "balanced", "aggressive"],
            width=130,
        )
        self.profile_clone_btn = pn.widgets.Button(name="Clone Preset to Custom", button_type="light", width=180)
        self.profile_status = pn.pane.Markdown("")
        self.custom_profile_help = pn.pane.Markdown("")
        self.custom_profile_status = pn.pane.Markdown("")
        self.custom_dirty_status = pn.pane.Markdown("")
        self.custom_saved_text = pn.widgets.TextInput(name="Saved Timestamps", value="", disabled=True, width=460)
        self.custom_copy_btn = pn.widgets.Button(name="Copy Timestamps", button_type="light", width=140)
        self.custom_export_btn = pn.widgets.Button(name="Export Profile Snapshot", button_type="primary", width=170)
        self.snapshot_import_path = pn.widgets.TextInput(name="Snapshot File", value="", placeholder="profile_snapshot_v30_YYYYMMDD_HHMMSS.json", width=420)
        self.snapshot_import_btn = pn.widgets.Button(name="Import Snapshot", button_type="primary", width=140)
        self.snapshot_use_last_source_btn = pn.widgets.Button(name="Use Last Dry-run Source", button_type="light", width=170, disabled=True)
        self.snapshot_recent_select = pn.widgets.Select(name="Recent Snapshots (0/0)", options=[], width=560)
        self.snapshot_recent_tag_filter = pn.widgets.Select(name="Filter Tag", options=["all"], value="all", width=180)
        self.snapshot_recent_schema_only = pn.widgets.Checkbox(name="Valid schema only", value=False, width=140)
        self.snapshot_recent_clear_filter_btn = pn.widgets.Button(name="Clear", button_type="light", width=70)
        self.snapshot_recent_refresh_btn = pn.widgets.Button(name="Refresh List", button_type="light", width=110)
        self.snapshot_recent_import_btn = pn.widgets.Button(name="Import Selected", button_type="primary", width=130)
        self.snapshot_recent_validate_btn = pn.widgets.Button(name="Validate Selected", button_type="warning", width=130)
        self.snapshot_recent_dryrun_btn = pn.widgets.Button(name="Dry-run Import", button_type="warning", width=130)
        self.snapshot_rerun_last_dryrun_btn = pn.widgets.Button(name="Re-run Last Dry-run", button_type="light", width=150, disabled=True)
        self.snapshot_fix_apply_block_btn = pn.widgets.Button(name="Fix Apply Block", button_type="warning", width=130, disabled=True)
        self.snapshot_apply_dryrun_btn = pn.widgets.Button(name="Apply Dry-run Result", button_type="success", width=150, disabled=True)
        self.snapshot_export_dryrun_btn = pn.widgets.Button(name="Export Dry-run CSV", button_type="light", width=140)
        self.snapshot_reset_block_audit_btn = pn.widgets.Button(name="Reset Block Audit", button_type="light", width=130)
        self.snapshot_export_block_audit_btn = pn.widgets.Button(name="Export Block Audit", button_type="light", width=130)
        self.snapshot_dryrun_block_filter = pn.widgets.Select(name="Block Code", options={"All codes": "all"}, value="all", width=180)
        self.snapshot_dryrun_block_order = pn.widgets.Select(name="Block Order", options={"Newest first": "newest", "Oldest first": "oldest"}, value="newest", width=140)
        self.snapshot_recent_show_excluded_btn = pn.widgets.Button(name="Show Excluded Files (0)", button_type="light", width=170)
        self.snapshot_recent_export_excluded_btn = pn.widgets.Button(name="Export Excluded CSV", button_type="light", width=150, disabled=True)
        self.snapshot_recent_filter_info = pn.pane.Markdown("### Snapshot Filter Info\nSchema filter: OFF")
        self.snapshot_recent_excluded_table = pn.widgets.Tabulator(
            pd.DataFrame(columns=["file", "reason"]),
            height=180,
            sizing_mode="stretch_width",
            visible=False,
        )
        self.snapshot_recent_excluded_section = pn.Column(self.snapshot_recent_excluded_table, visible=False)
        self.snapshot_recent_preview = pn.pane.Markdown("### Snapshot Preview\nSelect a snapshot to preview metadata.")
        self.snapshot_dryrun_preview = pn.pane.Markdown("### Snapshot Dry-run\nRun dry-run to preview value changes before import.")
        self.snapshot_dryrun_meta = pn.pane.Markdown(
            "### Dry-run Meta\n"
            "- Status: <span style='color:#9ca3af'><b>IDLE</b></span>\n"
            "- Action lock: <span style='color:#22c55e'><b>IDLE</b></span>\n"
            "- Baseline match: <span style='color:#9ca3af'><b>n/a</b></span>\n"
            "- Apply readiness: <span style='color:#ef4444'><b>BLOCKED</b></span>\n"
            "- Apply block code: NO_DRYRUN\n"
            "- Apply reason: No dry-run available\n"
            "- Source: n/a\n"
            "- Last run UTC: n/a\n"
            "- Last run Local: n/a"
        )
        self.snapshot_dryrun_block_audit = pn.pane.Markdown(
            "### Dry-run Block Audit\n"
            "- Filter: all\n"
            "- Order: newest\n"
            "- Showing: 0/0\n"
            "- Last transition: n/a\n"
            "- Top block codes: n/a\n"
            "- Recent transitions:\n"
            "- none"
        )
        self.snapshot_dryrun_filter = pn.widgets.Select(
            name="Dry-run Delta",
            value=self.DRYRUN_FILTER_ALL,
            options={"All changes": self.DRYRUN_FILTER_ALL, "Increase only": self.DRYRUN_FILTER_INCREASE, "Decrease only": self.DRYRUN_FILTER_DECREASE},
            width=160,
        )
        self.snapshot_dryrun_set_all_btn = pn.widgets.Button(name="Set Filter: All", button_type="light", width=120, disabled=True)
        self.snapshot_dryrun_filter_info = pn.pane.Markdown("### Dry-run Filter\nMode: all | Showing: 0/0")
        self.snapshot_dryrun_stats = pn.pane.Markdown(
            "### Dry-run Stats\n"
            "- Net delta sum: 0.000000\n"
            "- Increases: 0 | Decreases: 0\n"
            "- Abs delta sum: 0.000000\n"
            "- Impact: <span style='color:#22c55e'><b>LOW</b></span>\n"
            "- Top increase: n/a\n"
            "- Top decrease: n/a"
        )
        self.snapshot_dryrun_table = pn.widgets.Tabulator(
            pd.DataFrame(),
            height=220,
            sizing_mode="stretch_width",
            formatters={"delta_view": "html"},
        )
        self.snapshot_tag = pn.widgets.TextInput(name="Snapshot Tag", value="", placeholder="e.g. scalping-asia", width=220, max_length=self.SNAPSHOT_TAG_MAX_LEN)
        self.snapshot_notes = pn.widgets.TextAreaInput(
            name="Snapshot Notes",
            value="",
            placeholder="Optional operator notes for this snapshot",
            height=80,
            width=560,
            max_length=self.SNAPSHOT_NOTES_MAX_LEN,
        )

        self.custom_sl_pct = pn.widgets.FloatInput(
            name="SL %",
            value=float(self.runtime_profile.get("sl_pct", 0.02)),
            start=float(PROFILE_RANGES["sl_pct"][0]),
            end=float(PROFILE_RANGES["sl_pct"][1]),
            step=0.001,
            width=110,
        )
        self.custom_tp_pct = pn.widgets.FloatInput(
            name="TP %",
            value=float(self.runtime_profile.get("tp_pct", 0.04)),
            start=float(PROFILE_RANGES["tp_pct"][0]),
            end=float(PROFILE_RANGES["tp_pct"][1]),
            step=0.001,
            width=110,
        )
        self.custom_alert_conf = pn.widgets.FloatInput(
            name="Alert Conf",
            value=float(self.runtime_profile.get("alert_min_conf", 0.70)),
            start=float(PROFILE_RANGES["alert_min_conf"][0]),
            end=float(PROFILE_RANGES["alert_min_conf"][1]),
            step=0.01,
            width=110,
        )
        self.custom_alert_imb = pn.widgets.FloatInput(
            name="Alert Imb",
            value=float(self.runtime_profile.get("alert_min_imbalance", 0.25)),
            start=float(PROFILE_RANGES["alert_min_imbalance"][0]),
            end=float(PROFILE_RANGES["alert_min_imbalance"][1]),
            step=0.01,
            width=110,
        )
        self.custom_ticket_rr = pn.widgets.FloatInput(
            name="Min RR",
            value=float(self.runtime_profile.get("ticket_min_rr", 1.5)),
            start=float(PROFILE_RANGES["ticket_min_rr"][0]),
            end=float(PROFILE_RANGES["ticket_min_rr"][1]),
            step=0.1,
            width=110,
        )
        self.custom_stop_pct = pn.widgets.FloatInput(
            name="Max Stop %",
            value=float(self.runtime_profile.get("ticket_max_stop_pct", 3.0)),
            start=float(PROFILE_RANGES["ticket_max_stop_pct"][0]),
            end=float(PROFILE_RANGES["ticket_max_stop_pct"][1]),
            step=0.1,
            width=110,
        )
        self.custom_poll_seconds = pn.widgets.IntInput(
            name="Poll Sec",
            value=int(self.runtime_profile.get("poll_seconds", 45)),
            start=int(PROFILE_RANGES["poll_seconds"][0]),
            end=int(PROFILE_RANGES["poll_seconds"][1]),
            step=1,
            width=110,
        )
        self.custom_regime_conf = pn.widgets.FloatInput(
            name="Regime Conf",
            value=float(self.runtime_profile.get("min_regime_conf", 0.65)),
            start=float(PROFILE_RANGES["min_regime_conf"][0]),
            end=float(PROFILE_RANGES["min_regime_conf"][1]),
            step=0.01,
            width=110,
        )

        self.ema_fast = pn.widgets.IntInput(name="EMA Fast", value=50, start=5, end=400, step=1, width=110)
        self.ema_slow = pn.widgets.IntInput(name="EMA Slow", value=200, start=10, end=500, step=1, width=110)
        self.rsi_period = pn.widgets.IntInput(name="RSI Period", value=14, start=5, end=50, step=1, width=110)
        self.macd_fast = pn.widgets.IntInput(name="MACD Fast", value=12, start=5, end=30, step=1, width=110)
        self.macd_slow = pn.widgets.IntInput(name="MACD Slow", value=26, start=10, end=60, step=1, width=110)
        self.macd_signal = pn.widgets.IntInput(name="MACD Signal", value=9, start=3, end=30, step=1, width=120)
        self.atr_period = pn.widgets.IntInput(name="ATR Period", value=14, start=5, end=60, step=1, width=110)
        self.bb_window = pn.widgets.IntInput(name="BB Window", value=20, start=5, end=100, step=1, width=110)
        self.bb_dev = pn.widgets.FloatInput(name="BB Dev", value=2.0, start=1.0, end=4.0, step=0.1, width=110)
        self.bos_lookback = pn.widgets.IntInput(name="BOS Lookback", value=int(V26_CONFIG["lookback_bos"]), start=5, end=100, step=1, width=130)
        self.choch_lookback = pn.widgets.IntInput(name="CHoCH Lookback", value=int(V26_CONFIG["lookback_choch"]), start=5, end=100, step=1, width=140)

        self.show_ema50 = pn.widgets.Checkbox(name="EMA 50", value=True)
        self.show_ema200 = pn.widgets.Checkbox(name="EMA 200", value=True)
        self.show_rsi = pn.widgets.Checkbox(name="RSI", value=True)
        self.show_macd = pn.widgets.Checkbox(name="MACD", value=True)
        self.show_boll = pn.widgets.Checkbox(name="Bollinger", value=False)
        self.show_volume = pn.widgets.Checkbox(name="Volume", value=True)
        self.show_volatility = pn.widgets.Checkbox(name="Volatility", value=True)
        self.show_structure = pn.widgets.Checkbox(name="HH HL LH LL", value=True)
        self.show_bos = pn.widgets.Checkbox(name="BOS", value=True)
        self.show_choch = pn.widgets.Checkbox(name="CHoCH", value=True)
        self.show_order_blocks = pn.widgets.Checkbox(name="Order Blocks", value=True)
        self.show_fvg = pn.widgets.Checkbox(name="FVG", value=True)
        self.show_trade_plan = pn.widgets.Checkbox(name="Trade Plan Overlay", value=True)

        self.show_all_btn = pn.widgets.Button(name="Show All", button_type="success", width=100)
        self.hide_all_btn = pn.widgets.Button(name="Hide All", button_type="light", width=100)
        self.preset = pn.widgets.Select(name="Preset", value="Swing", options=["Scalp", "Swing", "SMC"])
        self.apply_preset_btn = pn.widgets.Button(name="Apply Preset", button_type="primary", width=120)
        self.auto_setup_btn = pn.widgets.Button(name="Auto Setup", button_type="warning", width=110)
        self.ai_trade_plan_btn = pn.widgets.Button(name="AI Trade Plan", button_type="success", width=120)
        self.show_all_btn.on_click(self._show_all_indicators)
        self.hide_all_btn.on_click(self._hide_all_indicators)
        self.apply_preset_btn.on_click(self._apply_preset)
        self.auto_setup_btn.on_click(self._auto_setup)
        self.ai_trade_plan_btn.on_click(self._ai_trade_plan)

        self.replay_enabled = pn.widgets.Checkbox(name="Replay Mode", value=False)
        self.replay_bars = pn.widgets.IntInput(name="Replay Bars", value=120, start=30, end=3000, step=5, width=120)
        self.replay_shift = pn.widgets.IntInput(name="Replay Shift", value=0, start=0, end=3000, step=1, width=120)
        self.replay_play = pn.widgets.Toggle(name="Play", value=False, button_type="primary", width=80)
        self.replay_next_btn = pn.widgets.Button(name="Next Bar", button_type="light", width=95)
        self.replay_speed_ms = pn.widgets.IntInput(name="Replay ms", value=900, start=200, end=5000, step=100, width=110)
        self.replay_loop = pn.widgets.Checkbox(name="Loop Replay", value=False)
        self.replay_next_btn.on_click(self._replay_next)

        self.alert_enabled = pn.widgets.Checkbox(name="Live Alerts", value=True)
        self.alert_conf_min = pn.widgets.FloatInput(
            name="Min Conf",
            value=float(self.runtime_profile["alert_min_conf"]),
            start=0.5,
            end=1.0,
            step=0.05,
            width=100,
        )
        self.alert_imb_min = pn.widgets.FloatInput(
            name="Min Imbalance",
            value=float(self.runtime_profile["alert_min_imbalance"]),
            start=0.05,
            end=0.9,
            step=0.05,
            width=120,
        )
        self.strict_live_mode = pn.widgets.Checkbox(name="Strict Live Mode", value=False)
        self.live_enabled = pn.widgets.Checkbox(name="Live Mode", value=False)
        self.live_interval_ms = pn.widgets.IntInput(name="Live ms", value=8000, start=1000, end=60000, step=500, width=110)

        self.refresh_btn = pn.widgets.Button(name="Refresh V26", button_type="primary")
        self.refresh_btn.on_click(self._request_refresh)

        # ── Paper trading widgets ──────────────────────────────────────────────
        self._paper = PaperTrader(capital=float(V26_CONFIG["risk"]["capital"]))
        self._last_trade: dict | None = None
        self._last_price: float = 62000.0
        self._trade_plan_active: bool = True
        self._last_alert_key: str = ""
        self._last_alert_ts: float = 0.0
        self._alert_rows: list[dict] = []
        self._last_regime: str = ""
        self._strict_live_block_active: bool = False
        self._last_feed_health: str = "UNKNOWN"
        self._feed_health_since_ts: float = time.time()
        self._ops_health_rows: list[dict] = []
        self._ops_last_health: str = "UNKNOWN"

        self.ticket_side = pn.widgets.Select(name="Ticket Side", value="BUY", options=["BUY", "SELL"])
        self.ticket_size_usd = pn.widgets.NumberInput(name="Ticket Size USD", value=500.0, start=10.0, end=100000.0, step=50.0)
        self.ticket_entry = pn.widgets.FloatInput(name="Entry", value=0.0, step=0.1)
        self.ticket_stop = pn.widgets.FloatInput(name="Stop", value=0.0, step=0.1)
        self.ticket_take = pn.widgets.FloatInput(name="Take Profit", value=0.0, step=0.1)
        self.ticket_min_rr = pn.widgets.FloatInput(
            name="Min RR",
            value=float(self.runtime_profile["ticket_min_rr"]),
            start=0.5,
            end=10.0,
            step=0.1,
            width=100,
        )
        self.ticket_max_size = pn.widgets.FloatInput(name="Max Size USD", value=2000.0, start=50.0, end=100000.0, step=50.0, width=120)
        self.ticket_max_stop_pct = pn.widgets.FloatInput(
            name="Max Stop %",
            value=float(self.runtime_profile["ticket_max_stop_pct"]),
            start=0.2,
            end=25.0,
            step=0.1,
            width=110,
        )
        self.ticket_from_ai_btn = pn.widgets.Button(name="Use AI Plan", button_type="primary", width=110)
        self.ticket_exec_btn = pn.widgets.Button(name="Execute Paper", button_type="success", width=120)
        self.ticket_status = pn.pane.Markdown("Ticket idle.")
        self.profile_apply_btn.on_click(self._apply_runtime_profile)
        self.profile_save_btn.on_click(self._save_runtime_profile)
        self.profile_save_apply_custom_btn.on_click(self._save_apply_custom_profile)
        self.profile_reset_custom_btn.on_click(self._reset_custom_profile)
        self.profile_clone_btn.on_click(self._clone_preset_to_custom)
        self.custom_copy_btn.on_click(self._copy_timestamp_hint)
        self.custom_export_btn.on_click(self._export_profile_snapshot)
        self.snapshot_import_btn.on_click(self._import_profile_snapshot)
        self.snapshot_recent_refresh_btn.on_click(self._refresh_snapshot_list)
        self.snapshot_recent_clear_filter_btn.on_click(self._clear_snapshot_filter)
        self.snapshot_recent_import_btn.on_click(self._import_selected_snapshot)
        self.snapshot_recent_validate_btn.on_click(self._validate_selected_snapshot)
        self.snapshot_recent_dryrun_btn.on_click(self._dry_run_selected_snapshot)
        self.snapshot_rerun_last_dryrun_btn.on_click(self._rerun_last_dryrun)
        self.snapshot_fix_apply_block_btn.on_click(self._fix_apply_block)
        self.snapshot_use_last_source_btn.on_click(self._use_last_dryrun_source)
        self.snapshot_apply_dryrun_btn.on_click(self._apply_dryrun_result)
        self.snapshot_export_dryrun_btn.on_click(self._export_dryrun_csv)
        self.snapshot_reset_block_audit_btn.on_click(self._reset_dryrun_block_audit)
        self.snapshot_export_block_audit_btn.on_click(self._export_dryrun_block_audit_csv)
        self.snapshot_recent_show_excluded_btn.on_click(self._toggle_excluded_snapshot_table)
        self.snapshot_recent_export_excluded_btn.on_click(self._export_excluded_csv)
        self.snapshot_recent_tag_filter.param.watch(self._on_snapshot_filter_change, "value")
        self.snapshot_recent_schema_only.param.watch(self._on_snapshot_filter_change, "value")
        self.snapshot_recent_select.param.watch(self._on_snapshot_selected, "value")
        self.snapshot_dryrun_filter.param.watch(self._on_dryrun_filter_change, "value")
        self.snapshot_dryrun_block_filter.param.watch(self._on_dryrun_block_filter_change, "value")
        self.snapshot_dryrun_block_order.param.watch(self._on_dryrun_block_filter_change, "value")
        self.snapshot_dryrun_set_all_btn.on_click(self._set_dryrun_filter_all)
        self.custom_copy_btn.js_on_click(
            args={"savedField": self.custom_saved_text},
            code="""
            const text = savedField.value || "";
            if (!text) {
                return;
            }
            if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text);
            }
            """,
        )
        self.ticket_from_ai_btn.on_click(self._ticket_from_ai)
        self.ticket_exec_btn.on_click(self._ticket_execute)

        self.paper_size = pn.widgets.NumberInput(
            name="Size USD", value=500.0, start=10.0, end=5000.0, step=100.0, width=140
        )
        self.paper_buy_btn = pn.widgets.Button(name="▲ BUY", button_type="success", width=120)
        self.paper_sell_btn = pn.widgets.Button(name="▼ SELL SHORT", button_type="danger", width=120)
        self.paper_close_id = pn.widgets.TextInput(name="Position ID", placeholder="e.g. a3f2c1d9", width=180)
        self.paper_close_btn = pn.widgets.Button(name="Close One", button_type="warning", width=110)
        self.paper_closeall_btn = pn.widgets.Button(name="Close All", button_type="warning", width=110)
        self.paper_reset_btn = pn.widgets.Button(name="Reset Journal", button_type="light", width=120)
        self.paper_buy_btn.on_click(self._paper_buy)
        self.paper_sell_btn.on_click(self._paper_sell)
        self.paper_close_btn.on_click(self._paper_close_one)
        self.paper_closeall_btn.on_click(self._paper_close_all)
        self.paper_reset_btn.on_click(self._paper_reset)

        self.paper_pos_table = pn.widgets.Tabulator(
            pd.DataFrame(), height=200, sizing_mode="stretch_width"
        )
        self.paper_trades_table = pn.widgets.Tabulator(
            pd.DataFrame(), height=200, sizing_mode="stretch_width"
        )
        self.paper_kpi = pn.pane.Markdown("## Paper Trading\nPress **Refresh V26** to initialize.")

        self.chart = pn.pane.Plotly(height=640)
        self.agent_table = pn.widgets.Tabulator(pd.DataFrame(), height=260)
        self.trade_table = pn.widgets.Tabulator(pd.DataFrame(), height=150)
        self.market_table = pn.widgets.Tabulator(pd.DataFrame(), height=180)
        self.exchange_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)
        self.strategy_table = pn.widgets.Tabulator(pd.DataFrame(), height=240)
        self.trend_table = pn.widgets.Tabulator(pd.DataFrame(), height=260)
        self.next_trend_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)
        self.portfolio_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)
        self.depth_table = pn.widgets.Tabulator(pd.DataFrame(), height=300)
        self.depth_heatmap = pn.pane.Plotly(height=260)
        self.alert_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)
        self.alert_clear_btn = pn.widgets.Button(name="Clear Alerts", button_type="light", width=100)
        self.alert_export_btn = pn.widgets.Button(name="Export Alerts CSV", button_type="primary", width=130)
        self.alert_clear_btn.on_click(self._clear_alerts)
        self.alert_export_btn.on_click(self._export_alerts)
        self.doctor_summary = pn.pane.Markdown("### Bot Doctor\nWaiting for first audit...")
        self.doctor_table = pn.widgets.Tabulator(pd.DataFrame(), height=240)
        self.doctor_history_chart = pn.pane.Plotly(height=290)
        self.doctor_anomaly_status = pn.pane.Markdown(
            "### Doctor Burst Detector\n"
            "- Status: **IDLE**\n"
            "- Window: `5` cycles\n"
            "- Notes: Waiting for first refresh..."
        )
        self.doctor_cycle_report = pn.pane.Markdown(
            "### Doctor Cycle Report\n"
            "- Waiting for first cycle..."
        )
        self.doctor_export_btn = pn.widgets.Button(name="Export Doctor CSV", button_type="primary", width=150)
        self.doctor_export_status = pn.pane.Markdown("CSV export idle.")
        self.doctor_director_summary = pn.pane.Markdown("### Director Panel\nWaiting for first refresh...")
        self.doctor_developer_summary = pn.pane.Markdown("### Developer Dashboard\nWaiting for first refresh...")
        self.doctor_filter = pn.widgets.Select(
            name="Doctor Filter",
            options={"All": "all", "User": "user", "Strategy": "strategy"},
            value="all",
            width=140,
        )
        self.doctor_export_btn.on_click(self._export_doctor_history_csv)
        self.doctor_filter.param.watch(self._on_doctor_filter_change, "value")
        self.doctor_interactive_table = pn.widgets.Tabulator(pd.DataFrame(), height=180, sizing_mode="stretch_width")

        self.cluster_pane = pn.pane.Markdown(self._cluster_md(), sizing_mode="stretch_width")
        self.cluster_tasks_table = pn.widgets.Tabulator(
            pd.DataFrame(columns=["metric", "value"]),
            height=240,
            sizing_mode="stretch_width",
        )

        self.ops_refresh_btn = pn.widgets.Button(name="Refresh Ops", button_type="primary", width=110)
        self.ops_start_alert_btn = pn.widgets.Button(name="Start Alerts", button_type="success", width=110)
        self.ops_restart_alert_btn = pn.widgets.Button(name="Restart Alerts", button_type="warning", width=120)
        self.ops_stop_alert_btn = pn.widgets.Button(name="Stop Alerts", button_type="danger", width=110)
        self.ops_export_diag_btn = pn.widgets.Button(name="Export Diagnostic", button_type="warning", width=140)
        self.ops_export_timeline_btn = pn.widgets.Button(name="Export Timeline CSV", button_type="primary", width=150)
        self.ops_auto_refresh = pn.widgets.Checkbox(name="Auto Refresh Ops", value=False)
        self.ops_refresh_ms = pn.widgets.IntInput(name="Ops ms", value=15000, start=3000, end=120000, step=1000, width=110)
        self.ops_health_badge = pn.pane.HTML("<b>Health:</b> <span style='color:#9ca3af'>UNKNOWN</span>")
        self.ops_status = pn.pane.Markdown("### Ops Status\nWaiting for first refresh...")
        self.ops_events = pn.pane.Markdown("### Recent Ops Events\n- none")
        self.ops_table = pn.widgets.Tabulator(pd.DataFrame(), height=260)
        self.ops_health_table = pn.widgets.Tabulator(pd.DataFrame(), height=220)
        self.ops_refresh_btn.on_click(self._refresh_ops_status)
        self.ops_start_alert_btn.on_click(self._ops_start_alert)
        self.ops_restart_alert_btn.on_click(self._ops_restart_alert)
        self.ops_stop_alert_btn.on_click(self._ops_stop_alert)
        self.ops_export_diag_btn.on_click(self._ops_export_diag)
        self.ops_export_timeline_btn.on_click(self._ops_export_timeline)

        self.kpi = pn.pane.Markdown("## V26 Status\nReady", width=460)
        self.ai_suggestion = pn.pane.Markdown("### AI Trade Suggestions\nWaiting for refresh...")
        self.feed_quality = pn.pane.Markdown("### Feed Quality\nWaiting for refresh...")
        self.dex_diagnostics = pn.pane.Markdown("### DEX Diagnostics\nWaiting for refresh...")
        self.pie = pn.pane.Plotly(height=420)
        self.trend_history = pn.pane.Plotly(height=280)

        self._custom_widgets = [
            self.custom_sl_pct,
            self.custom_tp_pct,
            self.custom_alert_conf,
            self.custom_alert_imb,
            self.custom_ticket_rr,
            self.custom_stop_pct,
            self.custom_poll_seconds,
            self.custom_regime_conf,
        ]
        self._last_saved_custom: dict[str, object] | None = None
        self._last_saved_custom_utc: str | None = None
        self._saved_snapshot_tag_filter: str | None = load_saved_snapshot_tag_filter()
        self._saved_snapshot_schema_only: bool = load_saved_snapshot_schema_only()
        self._snapshot_tag_filter_restored = False
        self._snapshot_schema_only_restored = False
        self._snapshot_excluded_rows: list[dict[str, str]] = []
        self._snapshot_excluded_visible = False
        saved_profile_name = load_saved_profile_name()
        if saved_profile_name == CUSTOM_PROFILE_NAME:
            self._last_saved_custom = load_saved_custom_profile()
            self._last_saved_custom_utc = load_saved_custom_updated_at()

        self.profile_select.param.watch(self._on_profile_select_change, "value")
        for widget in self._custom_widgets:
            widget.param.watch(self._on_custom_profile_change, "value")

        self.layout = pn.template.FastListTemplate(
            title="Smart Chart V27 - Hedge Fund + Human Trend Intelligence",
            main=[
                pn.Row(
                    self.symbol,
                    self.timeframe,
                    self.exchange_feed,
                    self.exchange_data_mode,
                    self.profile_select,
                    self.profile_apply_btn,
                    self.profile_save_btn,
                    self.profile_save_apply_custom_btn,
                    self.profile_reset_custom_btn,
                    self.profile_clone_source,
                    self.profile_clone_btn,
                    self.refresh_btn,
                    self.kpi,
                ),
                self.profile_status,
                pn.Row(
                    "### Custom Profile",
                    self.custom_sl_pct,
                    self.custom_tp_pct,
                    self.custom_alert_conf,
                    self.custom_alert_imb,
                    self.custom_ticket_rr,
                    self.custom_stop_pct,
                    self.custom_poll_seconds,
                    self.custom_regime_conf,
                ),
                self.custom_profile_help,
                self.custom_profile_status,
                self.custom_dirty_status,
                pn.Row(self.custom_saved_text, self.custom_copy_btn, self.custom_export_btn),
                pn.Row(self.snapshot_import_path, self.snapshot_import_btn, self.snapshot_use_last_source_btn),
                pn.Row(self.snapshot_recent_select, self.snapshot_recent_tag_filter, self.snapshot_recent_schema_only, self.snapshot_recent_clear_filter_btn, self.snapshot_recent_refresh_btn, self.snapshot_recent_validate_btn, self.snapshot_recent_dryrun_btn, self.snapshot_rerun_last_dryrun_btn, self.snapshot_fix_apply_block_btn, self.snapshot_apply_dryrun_btn, self.snapshot_export_dryrun_btn, self.snapshot_reset_block_audit_btn, self.snapshot_export_block_audit_btn, self.snapshot_dryrun_block_filter, self.snapshot_dryrun_block_order, self.snapshot_recent_show_excluded_btn, self.snapshot_recent_export_excluded_btn, self.snapshot_recent_import_btn),
                self.snapshot_recent_filter_info,
                self.snapshot_recent_excluded_section,
                self.snapshot_recent_preview,
                self.snapshot_dryrun_preview,
                self.snapshot_dryrun_meta,
                self.snapshot_dryrun_block_audit,
                pn.Row(self.snapshot_dryrun_filter, self.snapshot_dryrun_set_all_btn, self.snapshot_dryrun_filter_info),
                self.snapshot_dryrun_stats,
                self.snapshot_dryrun_table,
                self.snapshot_tag,
                self.snapshot_notes,
                pn.Tabs(
                    (
                        "Smart Chart V27",
                        pn.Row(
                            pn.Column(
                                pn.Row(self.show_ema50, self.show_ema200, self.show_rsi, self.show_macd, self.show_boll, self.show_volume, self.show_volatility),
                                pn.Row(
                                    self.show_structure,
                                    self.show_bos,
                                    self.show_choch,
                                    self.show_order_blocks,
                                    self.show_fvg,
                                    self.show_trade_plan,
                                    self.show_all_btn,
                                    self.hide_all_btn,
                                ),
                                pn.Row(
                                    self.ema_fast,
                                    self.ema_slow,
                                    self.rsi_period,
                                    self.macd_fast,
                                    self.macd_slow,
                                    self.macd_signal,
                                ),
                                pn.Row(
                                    self.atr_period,
                                    self.bb_window,
                                    self.bb_dev,
                                    self.bos_lookback,
                                    self.choch_lookback,
                                    self.preset,
                                    self.apply_preset_btn,
                                    self.auto_setup_btn,
                                    self.ai_trade_plan_btn,
                                ),
                                pn.Row(
                                    self.replay_enabled,
                                    self.replay_bars,
                                    self.replay_shift,
                                    self.replay_play,
                                    self.replay_next_btn,
                                    self.replay_speed_ms,
                                    self.replay_loop,
                                    self.alert_enabled,
                                    self.alert_conf_min,
                                    self.alert_imb_min,
                                    self.strict_live_mode,
                                    self.live_enabled,
                                    self.live_interval_ms,
                                ),
                                pn.Row(
                                    self.ticket_side,
                                    self.ticket_size_usd,
                                    self.ticket_entry,
                                    self.ticket_stop,
                                    self.ticket_take,
                                    self.ticket_min_rr,
                                    self.ticket_max_size,
                                    self.ticket_max_stop_pct,
                                    self.ticket_from_ai_btn,
                                    self.ticket_exec_btn,
                                ),
                                self.ticket_status,
                                self.chart,
                            ),
                            pn.Column("### Orderbook Depth", self.depth_heatmap, self.depth_table, width=360),
                        ),
                    ),
                    (
                        "AI Trade V18 + Debate V19",
                        pn.Row(
                            pn.Column(
                                "### Agent Votes",
                                self.agent_table,
                                "### Final Trade",
                                self.trade_table,
                                "### AI Trade Suggestions",
                                self.ai_suggestion,
                                "### Feed Quality",
                                self.feed_quality,
                                "### DEX Diagnostics",
                                self.dex_diagnostics,
                                pn.Row(self.alert_clear_btn),
                                pn.Row(self.alert_export_btn),
                                "### Alert History",
                                self.alert_table,
                            ),
                            pn.Column("### Market Brain", self.market_table),
                        ),
                    ),
                    (
                        "Strategy V20 + Regime V22",
                        pn.Row(self.strategy_table),
                    ),
                    (
                        "Portfolio V23 + Exchange V24",
                        pn.Row(
                            pn.Column("### Portfolio Brain", self.portfolio_table),
                            pn.Column("### Multi Exchange", self.exchange_table),
                        ),
                    ),
                    (
                        "Human Trends V27",
                        pn.Row(
                            pn.Column("### Common Trends", self.trend_table, "### Predicted Next Trends", self.next_trend_table),
                            pn.Column("### Top Products Pie", self.pie, "### Trend Score History", self.trend_history),
                        ),
                    ),
                    (
                        "Paper Trading",
                        pn.Column(
                            pn.Row(
                                self.paper_size,
                                self.paper_buy_btn,
                                self.paper_sell_btn,
                                self.paper_close_id,
                                self.paper_close_btn,
                                self.paper_closeall_btn,
                                self.paper_reset_btn,
                            ),
                            self.paper_kpi,
                            "### Open Positions",
                            self.paper_pos_table,
                            "### Closed Trades History",
                            self.paper_trades_table,
                        ),
                    ),
                    (
                        "Bot Doctor",
                        pn.Column(
                            "### AI System Audit",
                            self.doctor_summary,
                            "### Doctor Evolution Timeline",
                            self.doctor_history_chart,
                            self.doctor_anomaly_status,
                            self.doctor_cycle_report,
                            pn.Row(self.doctor_export_btn, self.doctor_export_status),
                            self.doctor_table,
                            pn.Row(
                                pn.Column(self.doctor_director_summary),
                                pn.Column(self.doctor_developer_summary),
                            ),
                            pn.Row(self.doctor_filter),
                            "### Interactive Doctor Panel",
                            self.doctor_interactive_table,
                        ),
                    ),
                    (
                        "Cluster Status",
                        pn.Column(
                            self.cluster_pane,
                            self.cluster_tasks_table,
                        ),
                    ),
                    (
                        "Admin/Ops",
                        pn.Column(
                            pn.Row(
                                self.ops_refresh_btn,
                                self.ops_start_alert_btn,
                                self.ops_restart_alert_btn,
                                self.ops_stop_alert_btn,
                                self.ops_export_diag_btn,
                                self.ops_export_timeline_btn,
                                self.ops_auto_refresh,
                                self.ops_refresh_ms,
                            ),
                            self.ops_health_badge,
                            self.ops_status,
                            self.ops_events,
                            "### Health Timeline",
                            self.ops_health_table,
                            "### Managed Processes",
                            self.ops_table,
                        ),
                    ),
                ),
            ],
            theme="dark",
        )

        # Enable Telegram command handling (/subscribe, /status, /mute, /alerts).
        if _TG_AVAILABLE and _tg_start_loop is not None:
            _tg_start_loop()

        self._last_dryrun_path: str | None = None
        self._last_dryrun_changes: int = 0
        self._last_dryrun_changed_keys: list[str] = []
        self._last_dryrun_df: pd.DataFrame = pd.DataFrame()
        self._last_dryrun_status: str = "IDLE"
        self._last_dryrun_source: str = ""
        self._last_dryrun_utc: str = ""
        self._last_dryrun_signature: str = ""
        self._dryrun_apply_ready: bool = False
        self._dryrun_apply_reason: str = "No dry-run available"
        self._dryrun_apply_block_code: str = "NO_DRYRUN"
        self._dryrun_apply_in_progress: bool = False
        self._dryrun_run_in_progress: bool = False
        self._dryrun_fix_in_progress: bool = False
        self._dryrun_rerun_in_progress: bool = False
        self._pending_dryrun_confirm: bool = False
        self._dryrun_block_rows: list[str] = []
        self._dryrun_block_counts: dict[str, int] = {}
        self._ops_events_rows: list[str] = []
        self._doctor_recent_logs: list[str] = []
        self._doctor_history_rows: list[dict[str, Any]] = []
        self._doctor_history_max_points: int = 180
        self._doctor_prev_health_score: float | None = None
        self._refresh_in_progress: bool = False
        self._refresh_queued: bool = False
        self.doctor_history_chart.object = self._build_doctor_history_figure()
        self._refresh_dryrun_meta()
        self._refresh_dryrun_block_audit()
        self._apply_dryrun_filter()
        self._refresh_snapshot_list()
        self._refresh_custom_profile_state()
        self._apply_runtime_profile(notify=False)
        self._request_refresh()
        # Periodic replay tick; only active when Replay + Play are enabled.
        self._replay_cb = pn.state.add_periodic_callback(self._replay_tick, period=self._ival(self.replay_speed_ms, 900), start=True)
        # Periodic live tick; refreshes dashboard when Live Mode is enabled.
        self._live_cb = pn.state.add_periodic_callback(self._live_tick, period=self._ival(self.live_interval_ms, 8000), start=True)
        # Periodic ops tick; refreshes Admin/Ops status when enabled.
        self._ops_cb = pn.state.add_periodic_callback(self._ops_tick, period=self._ival(self.ops_refresh_ms, 15000), start=True)

    @staticmethod
    def _ival(widget: object, default: int) -> int:
        try:
            value = getattr(widget, "value", default)
            return int(value if value is not None else default)
        except Exception:
            return default

    @staticmethod
    def _fval(widget: object, default: float) -> float:
        try:
            value = getattr(widget, "value", default)
            return float(value if value is not None else default)
        except Exception:
            return default

    @staticmethod
    def _to_float(value: object, default: object) -> float:
        try:
            return float(cast(Any, value))
        except Exception:
            try:
                return float(cast(Any, default))
            except Exception:
                return 0.0

    @staticmethod
    def _to_int(value: object, default: object) -> int:
        try:
            return int(cast(Any, value))
        except Exception:
            try:
                return int(cast(Any, default))
            except Exception:
                return 0

    def _log_ops_event(self, message: str) -> None:
        ts = datetime.utcnow().strftime("%H:%M:%S UTC")
        self._ops_events_rows.append(f"- [{ts}] {message}")
        self._ops_events_rows = self._ops_events_rows[-12:]
        body = "\n".join(reversed(self._ops_events_rows)) if self._ops_events_rows else "- none"
        self.ops_events.object = f"### Recent Ops Events\n{body}"

    def _record_dryrun_block_transition(self, previous_code: str, previous_reason: str) -> None:
        current_code = str(self._dryrun_apply_block_code or "")
        current_reason = str(self._dryrun_apply_reason or "")
        if current_code == str(previous_code or "") and current_reason == str(previous_reason or ""):
            return

        ts = datetime.utcnow().strftime("%H:%M:%S UTC")
        label = current_code or "UNKNOWN"
        self._dryrun_block_counts[label] = int(self._dryrun_block_counts.get(label, 0)) + 1
        self._dryrun_block_rows.append(f"- [{ts}] {label}: {current_reason}")
        self._dryrun_block_rows = self._dryrun_block_rows[-10:]
        self._refresh_dryrun_block_filter_options()
        self._refresh_dryrun_block_audit()

    def _refresh_dryrun_block_filter_options(self) -> None:
        options: dict[str, str] = {"All codes": "all"}
        for code in sorted(self._dryrun_block_counts.keys()):
            options[str(code)] = str(code)
        self.snapshot_dryrun_block_filter.options = options
        current = str(self.snapshot_dryrun_block_filter.value or "all")
        if current not in options.values():
            self.snapshot_dryrun_block_filter.value = "all"

    @staticmethod
    def _parse_dryrun_block_row(row: str) -> tuple[str, str, str]:
        line = str(row or "").strip()
        if line.startswith("- "):
            line = line[2:]
        timestamp = ""
        rest = line
        if line.startswith("[") and "]" in line:
            end = line.find("]")
            if end > 1:
                timestamp = line[1:end]
                rest = line[end + 1 :].strip()
        code = "UNKNOWN"
        reason = rest
        if ": " in rest:
            code, reason = rest.split(": ", 1)
        return timestamp, str(code or "UNKNOWN"), str(reason or "")

    def _on_dryrun_block_filter_change(self, *_: object) -> None:
        self._refresh_dryrun_block_audit()

    def _refresh_dryrun_block_audit(self) -> None:
        filter_code = str(self.snapshot_dryrun_block_filter.value or "all")
        order_mode = str(self.snapshot_dryrun_block_order.value or "newest")
        total_rows = len(self._dryrun_block_rows)
        filtered_rows: list[str] = []
        if filter_code == "all":
            filtered_rows = list(self._dryrun_block_rows)
        else:
            for row in self._dryrun_block_rows:
                _, code, _ = self._parse_dryrun_block_row(row)
                if code == filter_code:
                    filtered_rows.append(row)

        shown_rows = len(filtered_rows)
        last_transition = filtered_rows[-1] if filtered_rows else "- n/a"
        sorted_counts = sorted(self._dryrun_block_counts.items(), key=lambda item: (-int(item[1]), str(item[0])))
        top = sorted_counts[:3]
        if top:
            top_text = ", ".join(f"{code}: {count}" for code, count in top)
        else:
            top_text = "n/a"
        ordered_rows = list(reversed(filtered_rows)) if order_mode != "oldest" else list(filtered_rows)
        rows = "\n".join(ordered_rows) if ordered_rows else "- none"
        mode = "all" if filter_code == "all" else filter_code
        self.snapshot_dryrun_block_audit.object = (
            "### Dry-run Block Audit\n"
            f"- Filter: {mode}\n"
            f"- Order: {order_mode}\n"
            f"- Showing: {shown_rows}/{total_rows}\n"
            f"- Last transition: {last_transition}\n"
            f"- Top block codes: {top_text}\n"
            "- Recent transitions:\n"
            f"{rows}"
        )

    def _request_refresh(self, *_: object) -> None:
        if self._refresh_in_progress:
            self._refresh_queued = True
            return
        self._refresh_in_progress = True
        try:
            self.refresh()
        finally:
            self._refresh_in_progress = False
        if self._refresh_queued:
            self._refresh_queued = False
            self._request_refresh()

    def _on_doctor_filter_change(self, *_: object) -> None:
        self._refresh_doctor_interactive_table()

    def _build_doctor_panels(self, report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        findings = list(report.get("findings") or [])
        errors_count = sum(1 for item in findings if str(item.get("severity", "")).lower() == "error")
        warnings_count = sum(1 for item in findings if str(item.get("severity", "")).lower() == "warning")

        director_panel = {
            "bot_status": "Attention required" if errors_count > 0 else "Bots running normally",
            "doctor_summary": self._doctor_recent_logs[-5:],
            "performance_metrics": {
                "findings_count": len(findings),
                "errors_detected": errors_count,
                "warnings_detected": warnings_count,
                "health_score": float(report.get("health_score", 0.0)),
            },
        }

        developer_dashboard = {
            "active_agents": ["BotDoctor", "DebateEngine", "RiskEngine", "DataFeed"],
            "recent_corrections": self._doctor_recent_logs[-10:],
            "pending_alerts": errors_count + warnings_count,
            "system_health": "Optimal" if errors_count == 0 else "Degraded",
        }
        return director_panel, developer_dashboard

    def _refresh_doctor_interactive_table(self) -> None:
        filter_value = str(self.doctor_filter.value or "all").lower()
        if filter_value == "user":
            filtered = [item for item in self._doctor_recent_logs if "user" in item.lower() or "utilisateur" in item.lower()]
        elif filter_value == "strategy":
            filtered = [item for item in self._doctor_recent_logs if "strategy" in item.lower()]
        else:
            filtered = list(self._doctor_recent_logs)

        rows = [{"log": entry} for entry in filtered[-10:]]
        self.doctor_interactive_table.value = pd.DataFrame(rows)

    def _append_doctor_history(self, report: dict[str, Any]) -> None:
        findings = list(report.get("findings") or [])
        errors_count = sum(1 for item in findings if str(item.get("severity", "")).lower() == "error")
        warnings_count = sum(1 for item in findings if str(item.get("severity", "")).lower() == "warning")
        infos_count = sum(1 for item in findings if str(item.get("severity", "")).lower() == "info")
        self._doctor_history_rows.append(
            {
                "timestamp": datetime.utcnow(),
                "health_score": self._to_float(report.get("health_score"), 0.0),
                "findings_count": len(findings),
                "errors_count": errors_count,
                "warnings_count": warnings_count,
                "infos_count": infos_count,
            }
        )
        if len(self._doctor_history_rows) > self._doctor_history_max_points:
            self._doctor_history_rows = self._doctor_history_rows[-self._doctor_history_max_points :]

    def _export_doctor_history_csv(self, *_: object) -> None:
        if not self._doctor_history_rows:
            self.doctor_export_status.object = "No doctor history to export yet."
            return

        out_dir = os.path.join("logs", "doctor")
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_file = os.path.join(out_dir, f"doctor_history_{ts}.csv")
        dfh = pd.DataFrame(self._doctor_history_rows)
        if "timestamp" in dfh.columns:
            dfh["timestamp"] = dfh["timestamp"].astype(str)
        dfh.to_csv(out_file, index=False)
        self.doctor_export_status.object = f"Exported: `{out_file}`"

    def _build_doctor_cycle_report(self, report: dict[str, Any], burst: dict[str, Any]) -> str:
        findings = list(report.get("findings") or [])
        top_issue = str(findings[0].get("issue", "n/a")) if findings else "n/a"
        current_score = self._to_float(report.get("health_score"), 0.0)
        previous_score = self._doctor_prev_health_score
        delta_text = "n/a"
        delta_arrow = ""
        if previous_score is not None:
            delta = current_score - previous_score
            if delta > 0.01:
                delta_arrow = "up"
            elif delta < -0.01:
                delta_arrow = "down"
            else:
                delta_arrow = "flat"
            delta_text = f"{delta:+.1f} ({delta_arrow})"

        self._doctor_prev_health_score = current_score

        return (
            "### Doctor Cycle Report\n"
            f"- Health score: **{current_score:.1f}** (delta: `{delta_text}`)\n"
            f"- Findings this cycle: `{len(findings)}`\n"
            f"- Burst status: **{burst.get('status', 'IDLE')}**\n"
            f"- Top issue: `{top_issue}`"
        )

    def _build_doctor_history_figure(self) -> go.Figure:
        if not self._doctor_history_rows:
            fig = go.Figure()
            fig.add_annotation(
                text="No Bot Doctor history yet. Click Refresh V26 to start.",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=13),
            )
            fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=28, b=20), height=290)
            return fig

        dfh = pd.DataFrame(self._doctor_history_rows)
        dfh["health_sma5"] = dfh["health_score"].rolling(5, min_periods=1).mean()
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.62, 0.38],
            specs=[[{"secondary_y": True}], [{}]],
        )

        fig.add_trace(
            go.Scatter(
                x=dfh["timestamp"],
                y=dfh["health_score"],
                mode="lines+markers",
                name="Health Score",
                line=dict(color="#22c55e", width=2.2),
                marker=dict(size=5),
            ),
            row=1,
            col=1,
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=dfh["timestamp"],
                y=dfh["health_sma5"],
                mode="lines",
                name="Health SMA(5)",
                line=dict(color="#86efac", width=1.5, dash="dash"),
            ),
            row=1,
            col=1,
            secondary_y=False,
        )
        fig.add_trace(
            go.Bar(
                x=dfh["timestamp"],
                y=dfh["findings_count"],
                name="Findings",
                marker_color="#60a5fa",
                opacity=0.35,
            ),
            row=1,
            col=1,
            secondary_y=True,
        )

        fig.add_shape(
            type="rect",
            x0=0,
            x1=1,
            y0=self.DOCTOR_HEALTH_WARN,
            y1=100,
            xref="paper",
            yref="y",
            fillcolor="rgba(34,197,94,0.10)",
            line_width=0,
            layer="below",
        )
        fig.add_shape(
            type="rect",
            x0=0,
            x1=1,
            y0=self.DOCTOR_HEALTH_CRITICAL,
            y1=self.DOCTOR_HEALTH_WARN,
            xref="paper",
            yref="y",
            fillcolor="rgba(245,158,11,0.10)",
            line_width=0,
            layer="below",
        )
        fig.add_shape(
            type="rect",
            x0=0,
            x1=1,
            y0=0,
            y1=self.DOCTOR_HEALTH_CRITICAL,
            xref="paper",
            yref="y",
            fillcolor="rgba(239,68,68,0.10)",
            line_width=0,
            layer="below",
        )

        fig.add_trace(
            go.Bar(
                x=dfh["timestamp"],
                y=dfh["errors_count"],
                name="Errors",
                marker_color="#ef4444",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=dfh["timestamp"],
                y=dfh["warnings_count"],
                name="Warnings",
                marker_color="#f59e0b",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=dfh["timestamp"],
                y=dfh["infos_count"],
                name="Info",
                marker_color="#94a3b8",
            ),
            row=2,
            col=1,
        )

        burst_snapshot = self._doctor_burst_snapshot()
        if not dfh.empty and str(burst_snapshot.get("status", "")).upper() in {"BURST", "DEGRADED"}:
            last_x = dfh["timestamp"].iloc[-1]
            last_health = float(dfh["health_score"].iloc[-1])
            marker_color = "#ef4444" if str(burst_snapshot.get("status", "")).upper() == "BURST" else "#f59e0b"
            fig.add_trace(
                go.Scatter(
                    x=[last_x],
                    y=[last_health],
                    mode="markers+text",
                    text=[str(burst_snapshot.get("status", "")).upper()],
                    textposition="top center",
                    marker=dict(size=11, color=marker_color, symbol="diamond"),
                    name="Doctor Event",
                ),
                row=1,
                col=1,
                secondary_y=False,
            )

        fig.update_yaxes(title_text="Health", range=[0, 100], row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Findings", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text="Severity Count", row=2, col=1)
        fig.update_xaxes(title_text="UTC Time", row=2, col=1)
        fig.update_layout(
            template="plotly_dark",
            barmode="stack",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20),
            height=290,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.0),
        )
        return fig

    def _doctor_burst_snapshot(self) -> dict[str, Any]:
        rows = self._doctor_history_rows[-self.DOCTOR_BURST_WINDOW :]
        if not rows:
            return {
                "status": "IDLE",
                "status_color": "#9ca3af",
                "errors_sum": 0,
                "warnings_sum": 0,
                "health_min": 100.0,
                "health_max": 100.0,
                "notes": "No history available yet.",
            }

        errors_sum = sum(self._to_int(item.get("errors_count"), 0) for item in rows)
        warnings_sum = sum(self._to_int(item.get("warnings_count"), 0) for item in rows)
        health_values = [self._to_float(item.get("health_score"), 0.0) for item in rows]
        health_min = min(health_values)
        health_max = max(health_values)
        health_drop = health_max - health_min

        burst_triggered = (
            errors_sum >= self.DOCTOR_BURST_ERROR_SPIKE
            or warnings_sum >= self.DOCTOR_BURST_WARNING_SPIKE
            or health_drop >= 20.0
            or health_min < self.DOCTOR_HEALTH_CRITICAL
        )
        degraded = not burst_triggered and (
            health_min < self.DOCTOR_HEALTH_WARN
            or warnings_sum >= max(1, self.DOCTOR_BURST_WARNING_SPIKE // 2)
        )

        if burst_triggered:
            return {
                "status": "BURST",
                "status_color": "#ef4444",
                "errors_sum": errors_sum,
                "warnings_sum": warnings_sum,
                "health_min": health_min,
                "health_max": health_max,
                "notes": "Rapid anomaly growth detected in recent cycles.",
            }
        if degraded:
            return {
                "status": "DEGRADED",
                "status_color": "#f59e0b",
                "errors_sum": errors_sum,
                "warnings_sum": warnings_sum,
                "health_min": health_min,
                "health_max": health_max,
                "notes": "Watch closely: warning pressure or health softness detected.",
            }

        return {
            "status": "STABLE",
            "status_color": "#22c55e",
            "errors_sum": errors_sum,
            "warnings_sum": warnings_sum,
            "health_min": health_min,
            "health_max": health_max,
            "notes": "No anomaly burst in the configured window.",
        }

    def _cluster_metrics_map(self) -> dict[str, object]:
        return _CLUSTER_METRICS if _CLUSTER_AVAILABLE else {}

    def _cluster_md(self) -> str:
        metrics = self._cluster_metrics_map()
        workers = self._to_int(metrics.get("workers_active", 0), 0)
        tasks = self._to_int(metrics.get("tasks_completed", 0), 0)
        avg_ms = self._to_float(metrics.get("avg_backtest_ms", 0.0), 0.0)
        cycles = self._to_int(metrics.get("cycles", 0), 0)
        sharpe = self._to_float(metrics.get("last_best_sharpe", 0.0), 0.0)
        regime = str(metrics.get("last_regime", "N/A"))
        risk = str(metrics.get("last_risk", "N/A"))
        source = "orchestrator" if _CLUSTER_AVAILABLE else "unavailable"
        return (
            "## Cluster Status\n\n"
            f"- Source: **{source}**\n\n"
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
        metrics = self._cluster_metrics_map()
        rows = [
            {"metric": "source", "value": "orchestrator" if _CLUSTER_AVAILABLE else "unavailable"},
            {"metric": "workers_active", "value": self._to_int(metrics.get("workers_active", 0), 0)},
            {"metric": "tasks_completed", "value": self._to_int(metrics.get("tasks_completed", 0), 0)},
            {"metric": "avg_backtest_ms", "value": round(self._to_float(metrics.get("avg_backtest_ms", 0.0), 0.0), 1)},
            {"metric": "cycles_run", "value": self._to_int(metrics.get("cycles", 0), 0)},
            {"metric": "last_best_sharpe", "value": round(self._to_float(metrics.get("last_best_sharpe", 0.0), 0.0), 4)},
            {"metric": "last_regime", "value": str(metrics.get("last_regime", "N/A"))},
            {"metric": "last_risk", "value": str(metrics.get("last_risk", "N/A"))},
        ]
        return pd.DataFrame(rows)

    def _build_chart(self, df: pd.DataFrame) -> go.Figure:
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.62, 0.2, 0.18])

        fig.add_trace(
            go.Candlestick(
                x=df["time"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Price",
            ),
            row=1,
            col=1,
        )

        if bool(self.show_ema50.value):
            fig.add_trace(go.Scatter(x=df["time"], y=df["EMA50"], mode="lines", name=f"EMA{self._ival(self.ema_fast, 50)}"), row=1, col=1)
        if bool(self.show_ema200.value):
            fig.add_trace(go.Scatter(x=df["time"], y=df["EMA200"], mode="lines", name=f"EMA{self._ival(self.ema_slow, 200)}"), row=1, col=1)
        if bool(self.show_boll.value):
            fig.add_trace(go.Scatter(x=df["time"], y=df["BBH"], mode="lines", name="BB High", line=dict(width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df["time"], y=df["BBL"], mode="lines", name="BB Low", line=dict(width=1)), row=1, col=1)

        if bool(self.show_bos.value):
            bos_up = df[df["BOS"] == "BOS_UP"]
            bos_down = df[df["BOS"] == "BOS_DOWN"]
            fig.add_trace(
                go.Scatter(
                    x=bos_up["time"],
                    y=bos_up["close"],
                    mode="markers+text",
                    name="BOS_UP",
                    text=["BOS"] * len(bos_up),
                    textposition="top center",
                    marker=dict(symbol="triangle-up", size=10, color="#22c55e"),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=bos_down["time"],
                    y=bos_down["close"],
                    mode="markers+text",
                    name="BOS_DOWN",
                    text=["BOS"] * len(bos_down),
                    textposition="bottom center",
                    marker=dict(symbol="triangle-down", size=10, color="#ef4444"),
                ),
                row=1,
                col=1,
            )

        if bool(self.show_choch.value):
            choch_bull = df[df["CHOCH"] == "CHOCH_BULL"]
            choch_bear = df[df["CHOCH"] == "CHOCH_BEAR"]
            fig.add_trace(
                go.Scatter(
                    x=choch_bull["time"],
                    y=choch_bull["close"],
                    mode="markers+text",
                    name="CHOCH_BULL",
                    text=["CHoCH"] * len(choch_bull),
                    textposition="top right",
                    marker=dict(symbol="star", size=9, color="#60a5fa"),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=choch_bear["time"],
                    y=choch_bear["close"],
                    mode="markers+text",
                    name="CHOCH_BEAR",
                    text=["CHoCH"] * len(choch_bear),
                    textposition="bottom left",
                    marker=dict(symbol="x", size=9, color="#f59e0b"),
                ),
                row=1,
                col=1,
            )

        if bool(self.show_order_blocks.value):
            for zone in detect_order_blocks_zones(df):
                fig.add_shape(
                    type="rect",
                    x0=zone["x0"],
                    x1=zone["x1"],
                    y0=zone["y0"],
                    y1=zone["y1"],
                    line=dict(color="#00d084", width=1),
                    fillcolor="rgba(0,208,132,0.18)",
                    row=1,
                    col=1,
                )

        if bool(self.show_fvg.value):
            for zone in detect_fvg_zones(df):
                fig.add_shape(
                    type="rect",
                    x0=zone["x0"],
                    x1=zone["x1"],
                    y0=zone["y0"],
                    y1=zone["y1"],
                    line=dict(color="#ffb020", width=1),
                    fillcolor="rgba(255,176,32,0.16)",
                    row=1,
                    col=1,
                )

        if bool(self.show_rsi.value):
            fig.add_trace(go.Scatter(x=df["time"], y=df["RSI"], mode="lines", name="RSI"), row=2, col=1)
        if bool(self.show_volatility.value):
            fig.add_trace(go.Scatter(x=df["time"], y=df["ATR"], mode="lines", name="Volatility (ATR)", line=dict(width=1)), row=2, col=1)
        if bool(self.show_macd.value):
            fig.add_trace(go.Scatter(x=df["time"], y=df["MACD"], mode="lines", name="MACD"), row=3, col=1)
            fig.add_trace(go.Scatter(x=df["time"], y=df["MACD_SIGNAL"], mode="lines", name="MACD Signal", line=dict(width=1)), row=3, col=1)
        if bool(self.show_volume.value):
            fig.add_trace(go.Bar(x=df["time"], y=df["volume"], name="Volume", opacity=0.25), row=3, col=1)

        if bool(self.show_trade_plan.value) and self._trade_plan_active and self._last_trade:
            entry = float(self._last_trade.get("entry", 0.0))
            stop = float(self._last_trade.get("stop", 0.0))
            take = float(self._last_trade.get("take_profit", 0.0))
            rr = self._last_trade.get("rr", None)
            if entry > 0 and stop > 0 and take > 0:
                x0 = df["time"].iloc[0]
                x1 = df["time"].iloc[-1]
                fig.add_shape(type="line", x0=x0, x1=x1, y0=entry, y1=entry, line=dict(color="#22c55e", width=1.2), row=1, col=1)
                fig.add_shape(type="line", x0=x0, x1=x1, y0=stop, y1=stop, line=dict(color="#ef4444", width=1.1, dash="dash"), row=1, col=1)
                fig.add_shape(type="line", x0=x0, x1=x1, y0=take, y1=take, line=dict(color="#38bdf8", width=1.1, dash="dot"), row=1, col=1)
                fig.add_annotation(
                    x=df["time"].iloc[-1],
                    y=take,
                    text=f"AI Plan RR={rr}",
                    showarrow=False,
                    font=dict(color="#38bdf8"),
                    xanchor="right",
                    yanchor="bottom",
                    row=1,
                    col=1,
                )

        if self._strict_live_block_active:
            fig.add_annotation(
                x=0.01,
                y=0.98,
                xref="paper",
                yref="paper",
                text="STRICT LIVE BLOCK ACTIVE",
                showarrow=False,
                align="left",
                font=dict(color="#fecaca", size=12),
                bgcolor="rgba(127,29,29,0.85)",
                bordercolor="#ef4444",
                borderwidth=1,
            )

        fig.update_layout(template="plotly_dark", height=640, margin=dict(l=20, r=20, t=30, b=20), xaxis_rangeslider_visible=False)
        return fig

    def _show_all_indicators(self, *_) -> None:
        self.show_ema50.value = True
        self.show_ema200.value = True
        self.show_rsi.value = True
        self.show_macd.value = True
        self.show_boll.value = True
        self.show_volume.value = True
        self.show_volatility.value = True
        self.show_structure.value = True
        self.show_bos.value = True
        self.show_choch.value = True
        self.show_order_blocks.value = True
        self.show_fvg.value = True
        self.show_trade_plan.value = True

    def _hide_all_indicators(self, *_) -> None:
        self.show_ema50.value = False
        self.show_ema200.value = False
        self.show_rsi.value = False
        self.show_macd.value = False
        self.show_boll.value = False
        self.show_volume.value = False
        self.show_volatility.value = False
        self.show_structure.value = False
        self.show_bos.value = False
        self.show_choch.value = False
        self.show_order_blocks.value = False
        self.show_fvg.value = False
        self.show_trade_plan.value = False

    def _ai_trade_plan(self, *_) -> None:
        self._trade_plan_active = True
        self.show_trade_plan.value = True
        self._ticket_from_ai()
        self._request_refresh()

    def _ticket_from_ai(self, *_) -> None:
        if not self._last_trade:
            self.ticket_status.object = "No AI plan available yet. Click Refresh V26 first."
            return
        entry = float(self._last_trade.get("entry") or self._last_price)
        stop = float(self._last_trade.get("stop") or (entry * 0.98))
        take = float(self._last_trade.get("take_profit") or (entry * 1.04))
        self.ticket_entry.value = entry
        self.ticket_stop.value = stop
        self.ticket_take.value = take
        self.ticket_side.value = "BUY" if take >= entry else "SELL"
        self.ticket_status.object = f"AI ticket loaded: {self.ticket_side.value} @ {entry:.2f}"

    def _ticket_execute(self, *_) -> None:
        if self._strict_live_block_active:
            self.ticket_status.object = "Ticket blocked: strict live mode is active (fallback/mock source detected)."
            self._alert_once("ticket_blocked_strict_live", "error", "Ticket blocked by strict live mode.", cooldown=4)
            return

        side = str(self.ticket_side.value)
        entry = self._fval(self.ticket_entry, self._last_price)
        stop = self._fval(self.ticket_stop, entry * (0.98 if side == "BUY" else 1.02))
        take = self._fval(self.ticket_take, entry * (1.04 if side == "BUY" else 0.96))
        size = self._fval(self.ticket_size_usd, 500.0)
        max_size = self._fval(self.ticket_max_size, 2000.0)

        if size > max_size:
            self.ticket_status.object = f"Ticket rejected: size ${size:.2f} > max ${max_size:.2f}"
            self._alert_once("ticket_size", "warning", "Ticket blocked by Max Size", cooldown=3)
            return

        ok, reason, rr = self._validate_ticket(side, entry, stop, take)
        if not ok:
            self.ticket_status.object = f"Ticket rejected: {reason}"
            self._alert_once("ticket_invalid", "error", f"Ticket invalid: {reason}", cooldown=3)
            return
        min_rr = self._fval(self.ticket_min_rr, 1.5)
        if rr < min_rr:
            self.ticket_status.object = f"Ticket rejected: RR {rr:.2f} < min {min_rr:.2f}"
            self._alert_once("ticket_rr", "warning", "Ticket blocked by Min RR", cooldown=3)
            return

        self._paper.open_position(str(self.symbol.value), side, entry, size, stop, take)
        self.ticket_status.object = f"Paper order executed: {side} size ${size:.2f} | RR {rr:.2f}"
        self._refresh_paper_widgets()

    def _validate_ticket(self, side: str, entry: float, stop: float, take: float) -> tuple[bool, str, float]:
        if entry <= 0 or stop <= 0 or take <= 0:
            return False, "entry/stop/take must be positive", 0.0
        if side == "BUY":
            if not (stop < entry < take):
                return False, "BUY requires stop < entry < take", 0.0
        elif side == "SELL":
            if not (take < entry < stop):
                return False, "SELL requires take < entry < stop", 0.0
        else:
            return False, "invalid side", 0.0

        risk = abs(entry - stop)
        reward = abs(take - entry)
        if risk <= 1e-9:
            return False, "risk must be > 0", 0.0
        stop_pct = (risk / entry) * 100.0 if entry > 0 else 0.0
        max_stop_pct = self._fval(self.ticket_max_stop_pct, 3.0)
        if stop_pct > max_stop_pct:
            return False, f"stop distance {stop_pct:.2f}% > max {max_stop_pct:.2f}%", 0.0
        return True, "ok", (reward / risk)

    def _clear_alerts(self, *_) -> None:
        self._alert_rows = []
        self.alert_table.value = pd.DataFrame()

    def _export_alerts(self, *_) -> None:
        if not self._alert_rows:
            self._alert_once("alerts_export_empty", "warning", "No alerts to export.", cooldown=2)
            return

        export_df = pd.DataFrame(self._alert_rows)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"alerts_v26_{stamp}.csv"
        out_path = os.path.join(self._project_root(), file_name)
        export_df.to_csv(out_path, index=False)
        self._alert_once("alerts_export", "success", f"Alerts exported to {file_name}", cooldown=2)

    def _replay_next(self, *_) -> None:
        if not bool(self.replay_enabled.value):
            return
        self.replay_shift.value = self._ival(self.replay_shift, 0) + 1
        self._request_refresh()

    def _replay_tick(self) -> None:
        # Keep callback period in sync with UI.
        try:
            target = self._ival(self.replay_speed_ms, 900)
            if self._replay_cb.period != target:
                self._replay_cb.period = target
        except Exception:
            pass

        if bool(self.replay_enabled.value) and bool(self.replay_play.value):
            current_shift = self._ival(self.replay_shift, 0)
            next_shift = current_shift + 1
            if bool(self.replay_loop.value):
                raw_df = generate_ohlcv(
                    symbol=str(self.symbol.value),
                    timeframe=str(self.timeframe.value),
                    limit=int(V26_CONFIG["history_limit"]),
                    exchange_name=str(self.exchange_feed.value),
                    data_mode=str(self.exchange_data_mode.value),
                )
                max_shift = max(0, len(raw_df) - 30)
                if next_shift > max_shift:
                    next_shift = 0
            self.replay_shift.value = next_shift
            self._request_refresh()

    def _live_tick(self) -> None:
        # Keep callback period synced with UI setting.
        try:
            target = self._ival(self.live_interval_ms, 8000)
            if self._live_cb.period != target:
                self._live_cb.period = target
        except Exception:
            pass

        # Live mode is disabled while replay is actively playing.
        if bool(self.live_enabled.value) and not (bool(self.replay_enabled.value) and bool(self.replay_play.value)):
            self._request_refresh()

    def _ops_tick(self) -> None:
        try:
            target = self._ival(self.ops_refresh_ms, 15000)
            if self._ops_cb.period != target:
                self._ops_cb.period = target
        except Exception:
            pass

        if bool(self.ops_auto_refresh.value):
            self._refresh_ops_status()

    def _on_profile_select_change(self, *_: object) -> None:
        self._refresh_custom_profile_state()

    def _on_custom_profile_change(self, *_: object) -> None:
        had_dryrun = bool(self._last_dryrun_path)
        self._refresh_custom_profile_state()
        if had_dryrun:
            self._set_dryrun_state(None, changed_fields=0)
            self.snapshot_dryrun_preview.object = (
                "### Snapshot Dry-run\n"
                "Status: <span style='color:#f59e0b'><b>STALE</b></span>\n"
                "Custom profile values changed. Re-run dry-run before apply."
            )
            self._alert_once(
                "profile_snapshot_dryrun_stale",
                "warning",
                "Dry-run invalidated: custom values changed. Re-run dry-run.",
                cooldown=2,
            )
            self._last_dryrun_status = "STALE"
            self._last_dryrun_signature = ""
            self._refresh_dryrun_meta()
            self._log_ops_event("Dry-run invalidated: custom profile values changed")

    def _refresh_dryrun_meta(self) -> None:
        status = str(self._last_dryrun_status or "IDLE").upper()
        if status == "READY":
            color = "#22c55e"
        elif status == "NO_CHANGES":
            color = "#22c55e"
        elif status == "STALE":
            color = "#f59e0b"
        elif status == "FAILED":
            color = "#ef4444"
        else:
            color = "#9ca3af"

        source = os.path.basename(self._last_dryrun_source) if self._last_dryrun_source else "n/a"
        utc_run = str(self._last_dryrun_utc or "").strip() or "n/a"
        local_run = self._format_saved_local(utc_run) if utc_run != "n/a" else "n/a"

        if not self._last_dryrun_path or not self._last_dryrun_signature:
            baseline_label = "n/a"
            baseline_color = "#9ca3af"
        elif self._is_dryrun_signature_current():
            baseline_label = "MATCH"
            baseline_color = "#22c55e"
        else:
            baseline_label = "MISMATCH"
            baseline_color = "#f59e0b"

        fix_hint = self._dryrun_suggested_fix_text(self._dryrun_apply_block_code)
        action_busy = bool(
            self._dryrun_apply_in_progress
            or self._dryrun_run_in_progress
            or self._dryrun_fix_in_progress
            or self._dryrun_rerun_in_progress
        )
        lock_label = "BUSY" if action_busy else "IDLE"
        lock_color = "#f59e0b" if action_busy else "#22c55e"

        self.snapshot_dryrun_meta.object = (
            "### Dry-run Meta\n"
            f"- Status: <span style='color:{color}'><b>{status}</b></span>\n"
            f"- Action lock: <span style='color:{lock_color}'><b>{lock_label}</b></span>\n"
            f"- Baseline match: <span style='color:{baseline_color}'><b>{baseline_label}</b></span>\n"
            f"- Apply readiness: <span style='color:{'#22c55e' if self._dryrun_apply_ready else '#ef4444'}'><b>{'READY' if self._dryrun_apply_ready else 'BLOCKED'}</b></span>\n"
            f"- Apply block code: {self._dryrun_apply_block_code}\n"
            f"- Apply reason: {self._dryrun_apply_reason}\n"
            f"- Suggested fix: {fix_hint}\n"
            f"- Source: {source}\n"
            f"- Last run UTC: {utc_run}\n"
            f"- Last run Local: {local_run}"
        )
        self.snapshot_recent_dryrun_btn.disabled = action_busy
        self.snapshot_use_last_source_btn.disabled = action_busy or (not bool(self._last_dryrun_source))
        self.snapshot_rerun_last_dryrun_btn.disabled = action_busy or (not bool(self._last_dryrun_source))
        if action_busy:
            self.snapshot_fix_apply_block_btn.disabled = True
            self.snapshot_apply_dryrun_btn.disabled = True

    @staticmethod
    def _dryrun_suggested_fix_text(block_code: str) -> str:
        code = str(block_code or "")
        if code == "ACTION_BUSY":
            return "Wait until current action completes"
        if code == "FILTER_HIDDEN":
            return "Set Dry-run Delta to all"
        if code in {"SIGNATURE_MISMATCH", "NO_DRYRUN"}:
            return "Re-run dry-run from last source"
        if code == "CONFIRM_REQUIRED":
            return "Press Apply to confirm"
        if code == "READY":
            return "No action required"
        return "Inspect apply reason"

    def _custom_profile_errors(self) -> list[str]:
        errors: list[str] = []
        checks = self._custom_profile_field_specs()

        for key, label, value in checks:
            if value is None:
                errors.append(f"{label}: value is required")
                continue
            low, high = PROFILE_RANGES[key]
            as_float = self._to_float(value, low)
            if as_float < low or as_float > high:
                errors.append(f"{label}: must be between {low} and {high}")

        sl = self._to_float(self.custom_sl_pct.value, 0.02)
        tp = self._to_float(self.custom_tp_pct.value, 0.04)
        if tp <= sl:
            errors.append("TP % must be greater than SL %")
        return errors

    def _custom_profile_field_specs(self) -> list[tuple[str, str, object]]:
        return [
            ("sl_pct", "SL %", self.custom_sl_pct.value),
            ("tp_pct", "TP %", self.custom_tp_pct.value),
            ("alert_min_conf", "Alert Conf", self.custom_alert_conf.value),
            ("alert_min_imbalance", "Alert Imb", self.custom_alert_imb.value),
            ("ticket_min_rr", "Min RR", self.custom_ticket_rr.value),
            ("ticket_max_stop_pct", "Max Stop %", self.custom_stop_pct.value),
            ("poll_seconds", "Poll Sec", self.custom_poll_seconds.value),
            ("min_regime_conf", "Regime Conf", self.custom_regime_conf.value),
        ]

    def _render_custom_profile_guidance(self, is_custom: bool) -> None:
        lines: list[str] = ["### Custom Profile Ranges"]
        if not is_custom:
            lines.append("Preset mode: custom inputs are read-only.")
        for key, label, value in self._custom_profile_field_specs():
            low, high = PROFILE_RANGES[key]
            numeric = self._to_float(value, low)
            status = "OK" if (low <= numeric <= high) else "OUT"
            lines.append(f"- {label}: {numeric:.3f} (allowed {low}..{high}) [{status}]")
        lines.append("- Rule: TP % must be greater than SL %.")
        self.custom_profile_help.object = "\n".join(lines)

    def _refresh_custom_profile_state(self) -> bool:
        is_custom = str(self.profile_select.value) == CUSTOM_PROFILE_NAME
        for widget in self._custom_widgets:
            widget.disabled = not is_custom

        self._render_custom_profile_guidance(is_custom)
        self._refresh_custom_dirty_state(is_custom)

        if not is_custom:
            self.custom_profile_status.object = (
                "### Custom Profile Validation\n"
                "Status: <span style='color:#9ca3af'><b>PRESET MODE</b></span>\n"
                "Switch profile to **custom** to edit and validate custom values."
            )
            self.profile_apply_btn.disabled = False
            self.profile_save_btn.disabled = False
            self.profile_save_apply_custom_btn.disabled = True
            return True

        errors = self._custom_profile_errors()
        if errors:
            error_text = "\n".join(f"- {err}" for err in errors)
            self.custom_profile_status.object = (
                "### Custom Profile Validation\n"
                "Status: <span style='color:#ef4444'><b>INVALID</b></span>\n"
                f"{error_text}"
            )
            self.profile_apply_btn.disabled = True
            self.profile_save_btn.disabled = True
            self.profile_save_apply_custom_btn.disabled = True
            return False

        self.custom_profile_status.object = (
            "### Custom Profile Validation\n"
            "Status: <span style='color:#22c55e'><b>VALID</b></span>"
        )
        self.profile_apply_btn.disabled = False
        self.profile_save_btn.disabled = False
        self.profile_save_apply_custom_btn.disabled = False
        return True

    def _custom_profile_dirty(self) -> bool:
        if self._last_saved_custom is None:
            return True
        current = resolve_custom_profile(self._read_custom_profile_values())
        saved = resolve_custom_profile(self._last_saved_custom)
        for key in PROFILE_RANGES:
            left = self._to_float(current.get(key), 0.0)
            right = self._to_float(saved.get(key), 0.0)
            if self._is_material_profile_change(key, left, right):
                return True
        return False

    def _refresh_custom_dirty_state(self, is_custom: bool) -> None:
        if not is_custom:
            self.custom_dirty_status.object = (
                "### Custom Save State\n"
                "Status: <span style='color:#9ca3af'><b>PRESET MODE</b></span>"
            )
            self.custom_saved_text.value = ""
            return

        saved_at_line = ""
        saved_utc = ""
        saved_local = ""
        if isinstance(self._last_saved_custom_utc, str) and self._last_saved_custom_utc.strip():
            saved_utc = self._last_saved_custom_utc.strip()
            saved_local = self._format_saved_local(self._last_saved_custom_utc)
            saved_at_line = (
                f"\nLast saved (UTC): {saved_utc}"
                f"\nLast saved (Local): {saved_local}"
            )
        self.custom_saved_text.value = f"UTC={saved_utc} | LOCAL={saved_local}" if saved_utc else ""

        if self._custom_profile_dirty():
            self.custom_dirty_status.object = (
                "### Custom Save State\n"
                "Status: <span style='color:#f59e0b'><b>UNSAVED CHANGES</b></span>"
                f"{saved_at_line}"
            )
        else:
            self.custom_dirty_status.object = (
                "### Custom Save State\n"
                "Status: <span style='color:#22c55e'><b>SAVED</b></span>"
                f"{saved_at_line}"
            )

    def _copy_timestamp_hint(self, *_) -> None:
        if not self.custom_saved_text.value.strip():
            self._alert_once("copy_timestamps_empty", "warning", "No saved timestamp available yet.", cooldown=2)
            return
        self._alert_once(
            "copy_timestamps",
            "success",
            "Timestamp text copied (or ready in field if browser blocks clipboard).",
            cooldown=1,
        )

    def _export_profile_snapshot(self, *_) -> None:
        selected = str(self.profile_select.value)
        custom_values = resolve_custom_profile(self._read_custom_profile_values())
        current_profile = resolve_custom_profile(self._read_custom_profile_values()) if selected == CUSTOM_PROFILE_NAME else resolve_profile(selected)
        errors = self._custom_profile_errors() if selected == CUSTOM_PROFILE_NAME else []
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"profile_snapshot_v30_{timestamp}.json"
        clean_notes = self._sanitize_snapshot_notes(self.snapshot_notes.value)
        clean_tag = self._sanitize_snapshot_tag(self.snapshot_tag.value)
        self.snapshot_notes.value = clean_notes
        self.snapshot_tag.value = clean_tag

        payload = {
            "schema_version": self.SNAPSHOT_SCHEMA_VERSION,
            "exported_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "symbol": str(self.symbol.value),
            "timeframe": str(self.timeframe.value),
            "exchange": str(self.exchange_feed.value),
            "snapshot_tag": clean_tag,
            "snapshot_notes": clean_notes,
            "selected_profile": selected,
            "runtime_profile_preview": current_profile,
            "custom_profile_values": custom_values,
            "custom_validation": {
                "is_valid": len(errors) == 0,
                "errors": errors,
            },
            "custom_save_state": {
                "is_dirty": self._custom_profile_dirty() if selected == CUSTOM_PROFILE_NAME else False,
                "last_saved_utc": self._last_saved_custom_utc,
                "last_saved_local": self._format_saved_local(self._last_saved_custom_utc or ""),
            },
        }
        out_path = os.path.join(self._project_root(), file_name)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True, indent=2)

        self._alert_once(
            "profile_snapshot_export",
            "success",
            f"Profile snapshot exported: {file_name}",
            cooldown=1,
        )
        self._log_ops_event(f"Snapshot exported: {file_name}")
        self._refresh_snapshot_list()

    def _refresh_snapshot_list(self, *_) -> None:
        if not self._snapshot_schema_only_restored:
            self.snapshot_recent_schema_only.value = bool(self._saved_snapshot_schema_only)
            self._snapshot_schema_only_restored = True
        current_selected_path = self._resolve_project_path(str(self.snapshot_recent_select.value or "").strip())
        active_filter = self._sanitize_snapshot_tag(str(self.snapshot_recent_tag_filter.value or ""))
        filter_enabled = bool(active_filter and active_filter != self.SNAPSHOT_TAG_FILTER_ALL)
        schema_only = bool(self.snapshot_recent_schema_only.value)
        detected_tag_counts: dict[str, int] = {}
        untagged_count = 0
        total_snapshot_count = 0
        excluded_invalid_schema = 0
        excluded_unreadable = 0
        excluded_rows: list[dict[str, str]] = []
        entries: list[tuple[float, str, str]] = []
        for path in self._list_snapshot_files():
            name = os.path.basename(path)
            total_snapshot_count += 1
            try:
                ts = float(os.path.getmtime(path))
            except Exception:
                ts = 0.0

            label = name
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                if isinstance(payload, dict):
                    validation_errors = self._validate_snapshot_payload(payload) if schema_only else []
                    if schema_only and validation_errors:
                        excluded_invalid_schema += 1
                        reason = validation_errors[0] if validation_errors else "Invalid schema"
                        excluded_rows.append({"file": name, "reason": reason})
                        continue
                    tag = self._sanitize_snapshot_tag(payload.get("snapshot_tag", ""))
                    if tag:
                        detected_tag_counts[tag] = detected_tag_counts.get(tag, 0) + 1
                    else:
                        untagged_count += 1
                    if filter_enabled and active_filter == self.SNAPSHOT_TAG_FILTER_UNTAGGED and tag:
                        continue
                    if filter_enabled and active_filter != self.SNAPSHOT_TAG_FILTER_UNTAGGED and tag != active_filter:
                        continue
                    exported = str(payload.get("exported_at_utc", "")).strip()
                    if exported:
                        ts_exported = self._utc_to_epoch(exported)
                        if ts_exported is not None:
                            ts = ts_exported
                    if tag:
                        label = f"{name} | tag={tag}"
                    else:
                        label = f"{name} | [untagged]"
                    if exported:
                        exported_local = self._format_saved_local(exported)
                        label = f"{label} | local={exported_local} | utc={exported}"
                elif schema_only:
                    excluded_invalid_schema += 1
                    excluded_rows.append({"file": name, "reason": "payload must be a JSON object"})
                    continue
            except Exception:
                if schema_only:
                    excluded_unreadable += 1
                    excluded_rows.append({"file": name, "reason": "Unreadable JSON"})
                    continue
                if filter_enabled and active_filter != self.SNAPSHOT_TAG_FILTER_UNTAGGED:
                    continue
                untagged_count += 1
                pass
            entries.append((ts, label, path))

        tag_values = [self.SNAPSHOT_TAG_FILTER_ALL]
        option_labels: dict[str, str] = {
            f"{self.SNAPSHOT_TAG_FILTER_ALL} ({total_snapshot_count})": self.SNAPSHOT_TAG_FILTER_ALL,
        }
        if untagged_count > 0:
            tag_values.append(self.SNAPSHOT_TAG_FILTER_UNTAGGED)
            option_labels[f"{self.SNAPSHOT_TAG_FILTER_UNTAGGED} ({untagged_count})"] = self.SNAPSHOT_TAG_FILTER_UNTAGGED
        sorted_tags = sorted(detected_tag_counts.items(), key=lambda it: (-it[1], it[0]))
        for tag, count in sorted_tags:
            tag_values.append(tag)
            option_labels[f"{tag} ({count})"] = tag
        current_options = self.snapshot_recent_tag_filter.options
        current_values: list[str] = []
        if isinstance(current_options, dict):
            current_values = [str(v) for v in current_options.values()]
        elif isinstance(current_options, (list, tuple)):
            current_values = [str(v) for v in current_options]
        if current_values != tag_values:
            self.snapshot_recent_tag_filter.options = option_labels
        if not self._snapshot_tag_filter_restored:
            desired = self._sanitize_snapshot_tag(self._saved_snapshot_tag_filter or self.SNAPSHOT_TAG_FILTER_ALL)
            desired = desired or self.SNAPSHOT_TAG_FILTER_ALL
            if desired not in tag_values:
                desired = self.SNAPSHOT_TAG_FILTER_ALL
            self._snapshot_tag_filter_restored = True
            if str(self.snapshot_recent_tag_filter.value or "") != desired:
                self.snapshot_recent_tag_filter.value = desired
                return
        else:
            current_value = str(self.snapshot_recent_tag_filter.value or self.SNAPSHOT_TAG_FILTER_ALL)
            if current_value not in tag_values:
                self.snapshot_recent_tag_filter.value = self.SNAPSHOT_TAG_FILTER_ALL
                return

        entries.sort(key=lambda it: it[0], reverse=True)
        total_matches = len(entries)
        entries = entries[:20]
        options = {label: path for _, label, path in entries}
        self.snapshot_recent_select.name = f"Recent Snapshots ({len(options)}/{total_matches})"
        self.snapshot_recent_select.options = options
        if current_selected_path and current_selected_path in options.values():
            self.snapshot_recent_select.value = current_selected_path
        else:
            self.snapshot_recent_select.value = next(iter(options.values()), "")
        self._snapshot_excluded_rows = excluded_rows
        excluded_df = pd.DataFrame(self._snapshot_excluded_rows, columns=["file", "reason"])
        if schema_only and self._snapshot_excluded_visible and excluded_df.empty:
            excluded_df = pd.DataFrame([
                {"file": "(none)", "reason": "No excluded files for current filters."}
            ])
        self.snapshot_recent_excluded_table.value = excluded_df
        show_label = "Hide" if self._snapshot_excluded_visible else "Show"
        self.snapshot_recent_show_excluded_btn.name = f"{show_label} Excluded Files ({len(self._snapshot_excluded_rows)})"
        self.snapshot_recent_show_excluded_btn.disabled = False
        self.snapshot_recent_export_excluded_btn.name = f"Export Excluded CSV ({len(self._snapshot_excluded_rows)})"
        self.snapshot_recent_export_excluded_btn.disabled = not (schema_only and len(self._snapshot_excluded_rows) > 0)
        self.snapshot_recent_excluded_table.visible = bool(schema_only and self._snapshot_excluded_visible)
        self.snapshot_recent_excluded_section.visible = bool(schema_only and self._snapshot_excluded_visible)
        if schema_only:
            self.snapshot_recent_filter_info.object = (
                "### Snapshot Filter Info\n"
                "Schema filter: ON\n"
                f"- Excluded invalid schema/required fields: {excluded_invalid_schema}\n"
                f"- Excluded unreadable JSON: {excluded_unreadable}"
            )
        else:
            self.snapshot_recent_filter_info.object = "### Snapshot Filter Info\nSchema filter: OFF"
            self.snapshot_recent_excluded_table.visible = False
            self.snapshot_recent_excluded_section.visible = False
            self._snapshot_excluded_visible = False
            self.snapshot_recent_show_excluded_btn.name = f"Show Excluded Files ({len(self._snapshot_excluded_rows)})"
            self.snapshot_recent_show_excluded_btn.disabled = False
            self.snapshot_recent_export_excluded_btn.disabled = True
        self._refresh_snapshot_preview()

    def _on_snapshot_filter_change(self, *_: object) -> None:
        selected = str(self.snapshot_recent_tag_filter.value or self.SNAPSHOT_TAG_FILTER_ALL)
        save_snapshot_tag_filter(selected)
        save_snapshot_schema_only(bool(self.snapshot_recent_schema_only.value))
        self._refresh_snapshot_list()

    def _clear_snapshot_filter(self, *_: object) -> None:
        self.snapshot_recent_tag_filter.value = self.SNAPSHOT_TAG_FILTER_ALL

    def _toggle_excluded_snapshot_table(self, *_: object) -> None:
        if not bool(self.snapshot_recent_schema_only.value):
            self.snapshot_recent_schema_only.value = True
            save_snapshot_schema_only(True)
            self._snapshot_excluded_visible = True
            self._refresh_snapshot_list()
            self.snapshot_recent_excluded_table.visible = True
            self.snapshot_recent_excluded_section.visible = True
            self.snapshot_recent_show_excluded_btn.name = f"Hide Excluded Files ({len(self._snapshot_excluded_rows)})"
            return
        self._snapshot_excluded_visible = not self._snapshot_excluded_visible
        self.snapshot_recent_excluded_table.visible = self._snapshot_excluded_visible
        self.snapshot_recent_excluded_section.visible = self._snapshot_excluded_visible
        label = "Hide" if self._snapshot_excluded_visible else "Show"
        self.snapshot_recent_show_excluded_btn.name = f"{label} Excluded Files ({len(self._snapshot_excluded_rows)})"
        if self._snapshot_excluded_visible:
            self._refresh_snapshot_list()
            if not self._snapshot_excluded_rows:
                self._alert_once("snapshot_excluded_show_empty", "warning", "No excluded files for current filters.", cooldown=2)

    def _export_excluded_csv(self, *_) -> None:
        if not bool(self.snapshot_recent_schema_only.value):
            self._alert_once("snapshot_excluded_export_off", "warning", "Enable 'Valid schema only' to collect excluded files.", cooldown=2)
            return
        if not self._snapshot_excluded_rows:
            self._alert_once("snapshot_excluded_export_empty", "warning", "No excluded files to export.", cooldown=2)
            return
        export_df = pd.DataFrame(self._snapshot_excluded_rows, columns=["file", "reason"])
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"excluded_snapshots_v30_{stamp}.csv"
        out_path = os.path.join(self._project_root(), file_name)
        export_df.to_csv(out_path, index=False)
        self._alert_once("snapshot_excluded_export_ok", "success", f"Excluded CSV exported: {file_name}", cooldown=1)

    def _on_snapshot_selected(self, *_: object) -> None:
        self._set_dryrun_state(None, changed_fields=0)
        self._last_dryrun_status = "IDLE"
        self._last_dryrun_source = ""
        self._last_dryrun_utc = ""
        self._refresh_dryrun_meta()
        self._refresh_snapshot_preview()

    def _use_last_dryrun_source(self, *_) -> None:
        selected = self._resolve_project_path(str(self._last_dryrun_source or "").strip())
        if not selected:
            self._alert_once("dryrun_source_use_empty", "warning", "No previous dry-run source available.", cooldown=2)
            return
        if not os.path.exists(selected):
            self._alert_once("dryrun_source_use_missing", "warning", f"Last dry-run source missing: {selected}", cooldown=2)
            return

        self.snapshot_import_path.value = selected
        options = self.snapshot_recent_select.options
        if isinstance(options, dict):
            for path in options.values():
                if str(path) == selected:
                    self.snapshot_recent_select.value = selected
                    break
        self._alert_once("dryrun_source_use_ok", "success", "Loaded last dry-run source into snapshot field.", cooldown=1)
        self._log_ops_event("Dry-run source restored in snapshot field")

    def _rerun_last_dryrun(self, *_) -> None:
        if self._dryrun_rerun_in_progress:
            self._alert_once("dryrun_rerun_busy", "warning", "Re-run is already in progress.", cooldown=1)
            return
        self._dryrun_rerun_in_progress = True
        self._refresh_dryrun_meta()
        selected = self._resolve_project_path(str(self._last_dryrun_source or "").strip())
        try:
            if not selected:
                self._alert_once("dryrun_rerun_empty", "warning", "No previous dry-run source available.", cooldown=2)
                return
            if not os.path.exists(selected):
                self._alert_once("dryrun_rerun_missing", "warning", f"Last dry-run source missing: {selected}", cooldown=2)
                return

            self.snapshot_import_path.value = selected
            options = self.snapshot_recent_select.options
            if isinstance(options, dict):
                for path in options.values():
                    if str(path) == selected:
                        self.snapshot_recent_select.value = selected
                        break
            self._log_ops_event("Re-run last dry-run requested")
            self._dry_run_selected_snapshot()
        finally:
            self._dryrun_rerun_in_progress = False
            self._refresh_dryrun_meta()

    def _fix_apply_block(self, *_) -> None:
        if self._dryrun_fix_in_progress:
            self._alert_once("dryrun_fix_block_busy", "warning", "Fix action already in progress.", cooldown=1)
            return
        self._dryrun_fix_in_progress = True
        self._refresh_dryrun_meta()
        try:
            if self._dryrun_apply_ready:
                self._alert_once("dryrun_fix_block_ready", "success", "Apply is already ready.", cooldown=1)
                return

            block_code = str(self._dryrun_apply_block_code or "")
            if block_code == "FILTER_HIDDEN":
                self._set_dryrun_filter_all()
                self._alert_once("dryrun_fix_block_filter", "success", "Applied fix: switched filter to all.", cooldown=1)
                self._log_ops_event("Fix apply block: set filter to all")
                return

            if block_code in {"SIGNATURE_MISMATCH", "NO_DRYRUN"}:
                self._rerun_last_dryrun()
                return

            if block_code == "CONFIRM_REQUIRED":
                self._pending_dryrun_confirm = True
                self._update_apply_dryrun_button()
                self._log_ops_event("Fix apply block: auto-confirm apply helper")
                self._apply_dryrun_result()
                return

            self._alert_once("dryrun_fix_block_unknown", "warning", f"Manual action required: {self._dryrun_apply_reason}", cooldown=2)
        finally:
            self._dryrun_fix_in_progress = False
            self._refresh_dryrun_meta()

    def _on_dryrun_filter_change(self, *_: object) -> None:
        self._apply_dryrun_filter()

    def _set_dryrun_filter_all(self, *_: object) -> None:
        if str(self.snapshot_dryrun_filter.value or self.DRYRUN_FILTER_ALL) == self.DRYRUN_FILTER_ALL:
            return
        self.snapshot_dryrun_filter.value = self.DRYRUN_FILTER_ALL
        self._log_ops_event("Dry-run filter reset to all")

    def _dryrun_filter_mode_label(self, mode: str) -> str:
        if mode == self.DRYRUN_FILTER_INCREASE:
            return "increase"
        if mode == self.DRYRUN_FILTER_DECREASE:
            return "decrease"
        return "all"

    def _dryrun_filter_mode_color(self, mode: str) -> str:
        if mode == self.DRYRUN_FILTER_INCREASE:
            return "#22c55e"
        if mode == self.DRYRUN_FILTER_DECREASE:
            return "#ef4444"
        return "#9ca3af"

    @staticmethod
    def _dryrun_impact_level(abs_sum: float) -> tuple[str, str]:
        if abs_sum >= 2.0:
            return "HIGH", "#ef4444"
        if abs_sum >= 0.75:
            return "MEDIUM", "#f59e0b"
        return "LOW", "#22c55e"

    def _get_filtered_dryrun_df(self) -> pd.DataFrame:
        if not isinstance(self._last_dryrun_df, pd.DataFrame) or self._last_dryrun_df.empty:
            return pd.DataFrame()

        mode = str(self.snapshot_dryrun_filter.value or self.DRYRUN_FILTER_ALL)
        filtered = self._last_dryrun_df.copy()
        if mode == self.DRYRUN_FILTER_INCREASE and "delta" in filtered.columns:
            filtered = filtered[filtered["delta"] > 0]
        elif mode == self.DRYRUN_FILTER_DECREASE and "delta" in filtered.columns:
            filtered = filtered[filtered["delta"] < 0]
        return filtered.reset_index(drop=True)

    def _has_hidden_dryrun_changes(self) -> bool:
        if not isinstance(self._last_dryrun_df, pd.DataFrame) or self._last_dryrun_df.empty:
            return False
        mode = str(self.snapshot_dryrun_filter.value or self.DRYRUN_FILTER_ALL)
        if mode == self.DRYRUN_FILTER_ALL:
            return False
        total = int(len(self._last_dryrun_df.index))
        shown = int(len(self._get_filtered_dryrun_df().index))
        return shown < total

    def _current_custom_signature(self) -> str:
        resolved = resolve_custom_profile(self._read_custom_profile_values())
        return json.dumps(resolved, sort_keys=True, separators=(",", ":"))

    def _is_dryrun_signature_current(self) -> bool:
        if not self._last_dryrun_path:
            return False
        if not self._last_dryrun_signature:
            return False
        return self._last_dryrun_signature == self._current_custom_signature()

    def _apply_dryrun_filter(self) -> None:
        mode = str(self.snapshot_dryrun_filter.value or self.DRYRUN_FILTER_ALL)
        mode_label = self._dryrun_filter_mode_label(mode)
        mode_color = self._dryrun_filter_mode_color(mode)
        self.snapshot_dryrun_set_all_btn.disabled = mode == self.DRYRUN_FILTER_ALL
        total = 0
        shown = 0
        if not isinstance(self._last_dryrun_df, pd.DataFrame) or self._last_dryrun_df.empty:
            self.snapshot_dryrun_table.value = pd.DataFrame()
            self.snapshot_dryrun_filter_info.object = (
                "### Dry-run Filter\n"
                f"Mode: <span style='color:{mode_color}'><b>{mode_label}</b></span> | Showing: 0/0"
            )
            self.snapshot_dryrun_stats.object = (
                "### Dry-run Stats\n"
                "- Net delta sum: 0.000000\n"
                "- Increases: 0 | Decreases: 0\n"
                "- Abs delta sum: 0.000000\n"
                "- Impact: <span style='color:#22c55e'><b>LOW</b></span>\n"
                "- Top increase: n/a\n"
                "- Top decrease: n/a"
            )
            return

        total = int(len(self._last_dryrun_df.index))
        filtered = self._get_filtered_dryrun_df()
        shown = int(len(filtered.index))
        hidden = max(0, total - shown)
        self.snapshot_dryrun_table.value = filtered
        hidden_text = f" | Hidden: {hidden}" if hidden > 0 else ""
        self.snapshot_dryrun_filter_info.object = (
            "### Dry-run Filter\n"
            f"Mode: <span style='color:{mode_color}'><b>{mode_label}</b></span> | Showing: {shown}/{total}{hidden_text}"
        )

        if filtered.empty or "delta" not in filtered.columns or "field" not in filtered.columns:
            self.snapshot_dryrun_stats.object = (
                "### Dry-run Stats\n"
                "- Net delta sum: 0.000000\n"
                "- Increases: 0 | Decreases: 0\n"
                "- Abs delta sum: 0.000000\n"
                "- Impact: <span style='color:#22c55e'><b>LOW</b></span>\n"
                "- Top increase: n/a\n"
                "- Top decrease: n/a"
            )
            return

        delta_series = pd.to_numeric(filtered["delta"], errors="coerce").fillna(0.0)
        net_delta = float(delta_series.sum())
        abs_delta = float(delta_series.abs().sum())
        increases = int((delta_series > 0).sum())
        decreases = int((delta_series < 0).sum())
        impact_label, impact_color = self._dryrun_impact_level(abs_delta)

        inc_df = filtered[delta_series > 0]
        dec_df = filtered[delta_series < 0]

        top_inc = "n/a"
        if not inc_df.empty:
            top_inc_row = inc_df.sort_values(by="delta", ascending=False).iloc[0]
            top_inc = f"{top_inc_row['field']} (+{float(top_inc_row['delta']):.6f})"

        top_dec = "n/a"
        if not dec_df.empty:
            top_dec_row = dec_df.sort_values(by="delta", ascending=True).iloc[0]
            top_dec = f"{top_dec_row['field']} ({float(top_dec_row['delta']):.6f})"

        self.snapshot_dryrun_stats.object = (
            "### Dry-run Stats\n"
            f"- Net delta sum: {net_delta:.6f}\n"
            f"- Increases: {increases} | Decreases: {decreases}\n"
            f"- Abs delta sum: {abs_delta:.6f}\n"
            f"- Impact: <span style='color:{impact_color}'><b>{impact_label}</b></span>\n"
            f"- Top increase: {top_inc}\n"
            f"- Top decrease: {top_dec}"
        )
        self._update_apply_dryrun_button()

    def _refresh_snapshot_preview(self) -> None:
        selected = self._resolve_project_path(str(self.snapshot_recent_select.value or "").strip())
        if not selected:
            self.snapshot_recent_preview.object = "### Snapshot Preview\nNo snapshot selected."
            return

        if not os.path.exists(selected):
            self.snapshot_recent_preview.object = (
                "### Snapshot Preview\n"
                f"File missing: {selected}"
            )
            return

        try:
            with open(selected, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if not isinstance(payload, dict):
                self.snapshot_recent_preview.object = "### Snapshot Preview\nInvalid JSON object."
                return

            exported_utc = str(payload.get("exported_at_utc", "")).strip() or "n/a"
            exported_local = self._format_saved_local(exported_utc) if exported_utc != "n/a" else "n/a"
            tag = self._sanitize_snapshot_tag(payload.get("snapshot_tag", "")) or "n/a"
            selected_profile = str(payload.get("selected_profile", "")).strip() or "n/a"

            validation = payload.get("custom_validation")
            is_valid = "n/a"
            error_count = "n/a"
            if isinstance(validation, dict):
                is_valid = str(bool(validation.get("is_valid", False)))
                errors = validation.get("errors", [])
                if isinstance(errors, list):
                    error_count = str(len(errors))

            self.snapshot_recent_preview.object = (
                "### Snapshot Preview\n"
                f"- File: {os.path.basename(selected)}\n"
                f"- Tag: {tag}\n"
                f"- Exported UTC: {exported_utc}\n"
                f"- Exported Local: {exported_local}\n"
                f"- Selected profile: {selected_profile}\n"
                f"- Custom valid: {is_valid} (errors: {error_count})"
            )
        except Exception as exc:
            self.snapshot_recent_preview.object = f"### Snapshot Preview\nCould not read snapshot: {exc}"

    def _import_selected_snapshot(self, *_) -> None:
        selected = self._resolve_project_path(str(self.snapshot_recent_select.value or "").strip())
        if not selected:
            self._alert_once("profile_snapshot_recent_empty", "warning", "No snapshot selected to import.", cooldown=2)
            self._log_ops_event("Snapshot import skipped: no selection")
            return
        self.snapshot_import_path.value = selected
        self._import_profile_snapshot()

    def _dry_run_selected_snapshot(self, *_) -> None:
        if self._dryrun_run_in_progress:
            self._alert_once("profile_snapshot_dryrun_busy", "warning", "Dry-run already in progress.", cooldown=1)
            return

        self._dryrun_run_in_progress = True
        self._refresh_dryrun_meta()
        selected = ""
        try:
            selected = self._resolve_project_path(str(self.snapshot_recent_select.value or "").strip())
            if not selected:
                selected = self._resolve_project_path(str(self.snapshot_import_path.value or "").strip())
            if not selected:
                self._alert_once("profile_snapshot_dryrun_empty", "warning", "No snapshot selected for dry-run.", cooldown=2)
                self._log_ops_event("Snapshot dry-run skipped: no selection")
                self._last_dryrun_df = pd.DataFrame()
                self._apply_dryrun_filter()
                self._set_dryrun_state(None, changed_fields=0)
                return
            if not os.path.exists(selected):
                self._alert_once("profile_snapshot_dryrun_missing", "error", f"Snapshot not found: {selected}", cooldown=2)
                self._log_ops_event(f"Snapshot dry-run failed: missing file {os.path.basename(selected)}")
                self._last_dryrun_df = pd.DataFrame()
                self._apply_dryrun_filter()
                self._set_dryrun_state(None, changed_fields=0)
                return

            with open(selected, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            errors = self._validate_snapshot_payload(payload)
            if errors:
                err_lines = "\n".join(f"- {e}" for e in errors)
                self.snapshot_dryrun_preview.object = (
                    "### Snapshot Dry-run\n"
                    "Status: <span style='color:#ef4444'><b>FAILED</b></span>\n"
                    f"- File: {os.path.basename(selected)}\n"
                    f"{err_lines}"
                )
                self._last_dryrun_df = pd.DataFrame()
                self._apply_dryrun_filter()
                self._alert_once("profile_snapshot_dryrun_invalid", "warning", f"Dry-run failed: {len(errors)} issue(s).", cooldown=2)
                self._last_dryrun_status = "FAILED"
                self._last_dryrun_source = selected
                self._last_dryrun_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                self._last_dryrun_signature = ""
                self._refresh_dryrun_meta()
                self._log_ops_event(f"Snapshot dry-run failed: {len(errors)} schema issues")
                self._set_dryrun_state(None, changed_fields=0)
                return

            source = payload.get("custom_profile_values")
            if not isinstance(source, dict):
                fallback = payload.get("runtime_profile_preview")
                if isinstance(fallback, dict):
                    source = fallback
            imported_custom = resolve_custom_profile(source if isinstance(source, dict) else {})
            current_custom = resolve_custom_profile(self._read_custom_profile_values())

            diffs: list[str] = []
            changed_keys: list[str] = []
            rows: list[dict[str, object]] = []
            for key in PROFILE_RANGES:
                cur = self._to_float(current_custom.get(key), 0.0)
                new = self._to_float(imported_custom.get(key), 0.0)
                if self._is_material_profile_change(key, cur, new):
                    changed_keys.append(key)
                    if key == "poll_seconds":
                        cur_view = int(round(cur))
                        new_view = int(round(new))
                        delta = float(new_view - cur_view)
                        diffs.append(f"- {key}: {cur_view} -> {new_view}")
                    else:
                        cur_view = round(cur, 6)
                        new_view = round(new, 6)
                        delta = new - cur
                        diffs.append(f"- {key}: {cur:.6f} -> {new:.6f}")
                    delta_color = "#22c55e" if delta > 0 else "#ef4444"
                    delta_prefix = "+" if delta > 0 else ""
                    if key == "poll_seconds":
                        delta_text = f"{delta_prefix}{int(delta):d}"
                    else:
                        delta_text = f"{delta_prefix}{delta:.6f}"
                    rows.append(
                        {
                            "field": key,
                            "current": cur_view,
                            "incoming": new_view,
                            "delta": round(delta, 6),
                            "abs_delta": round(abs(delta), 6),
                            "delta_view": f"<span style='color:{delta_color}'><b>{delta_text}</b></span>",
                        }
                    )

            if not diffs:
                self.snapshot_dryrun_preview.object = (
                    "### Snapshot Dry-run\n"
                    "Status: <span style='color:#22c55e'><b>NO CHANGES</b></span>\n"
                    f"- File: {os.path.basename(selected)}"
                )
                self._last_dryrun_df = pd.DataFrame()
                self._apply_dryrun_filter()
                self._alert_once("profile_snapshot_dryrun_nochange", "success", "Dry-run complete: no value changes.", cooldown=1)
                self._last_dryrun_status = "NO_CHANGES"
                self._last_dryrun_source = selected
                self._last_dryrun_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                self._last_dryrun_signature = self._current_custom_signature()
                self._refresh_dryrun_meta()
                self._log_ops_event(f"Snapshot dry-run: no changes ({os.path.basename(selected)})")
                self._set_dryrun_state(selected, changed_fields=0, changed_keys=[])
                return

            diff_lines = "\n".join(diffs)
            self.snapshot_dryrun_preview.object = (
                "### Snapshot Dry-run\n"
                "Status: <span style='color:#f59e0b'><b>CHANGES DETECTED</b></span>\n"
                f"- File: {os.path.basename(selected)}\n"
                f"- Changed fields: {len(diffs)}\n"
                f"{diff_lines}"
            )
            dryrun_df = pd.DataFrame(rows)
            if not dryrun_df.empty and "abs_delta" in dryrun_df.columns:
                dryrun_df = dryrun_df.sort_values(by="abs_delta", ascending=False).reset_index(drop=True)
            self._last_dryrun_df = dryrun_df
            self._apply_dryrun_filter()
            self._alert_once("profile_snapshot_dryrun_ok", "success", f"Dry-run complete: {len(diffs)} field change(s).", cooldown=1)
            self._last_dryrun_status = "READY"
            self._last_dryrun_source = selected
            self._last_dryrun_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            self._last_dryrun_signature = self._current_custom_signature()
            self._refresh_dryrun_meta()
            self._log_ops_event(f"Snapshot dry-run: {len(diffs)} changes ({os.path.basename(selected)})")
            self._set_dryrun_state(selected, changed_fields=len(diffs), changed_keys=changed_keys)
        except Exception as exc:
            self._alert_once("profile_snapshot_dryrun_error", "error", f"Could not run dry-run: {exc}", cooldown=2)
            self._log_ops_event("Snapshot dry-run failed: runtime error")
            self._last_dryrun_df = pd.DataFrame()
            self._apply_dryrun_filter()
            self._last_dryrun_status = "FAILED"
            self._last_dryrun_source = selected
            self._last_dryrun_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            self._last_dryrun_signature = ""
            self._refresh_dryrun_meta()
            self._set_dryrun_state(None, changed_fields=0)
        finally:
            self._dryrun_run_in_progress = False
            self._refresh_dryrun_meta()

    def _set_dryrun_state(self, snapshot_path: str | None, changed_fields: int = 0, changed_keys: list[str] | None = None) -> None:
        self._last_dryrun_path = snapshot_path
        self._last_dryrun_changes = max(0, int(changed_fields))
        self._last_dryrun_changed_keys = list(changed_keys or [])
        if not snapshot_path:
            self._last_dryrun_signature = ""
        if not snapshot_path or self._last_dryrun_changes <= 0:
            self._last_dryrun_df = pd.DataFrame()
            self._apply_dryrun_filter()
        self._pending_dryrun_confirm = False
        self._update_apply_dryrun_button()

    def _update_apply_dryrun_button(self) -> None:
        previous_code = str(self._dryrun_apply_block_code or "")
        previous_reason = str(self._dryrun_apply_reason or "")
        self.snapshot_fix_apply_block_btn.disabled = True
        self.snapshot_fix_apply_block_btn.name = "Fix Apply Block"
        if self._dryrun_run_in_progress or self._dryrun_apply_in_progress or self._dryrun_fix_in_progress or self._dryrun_rerun_in_progress:
            self._dryrun_apply_ready = False
            self._dryrun_apply_reason = "Action lock active (wait for current task)"
            self._dryrun_apply_block_code = "ACTION_BUSY"
            self.snapshot_apply_dryrun_btn.disabled = True
            self.snapshot_apply_dryrun_btn.name = "Apply locked: action running"
            self.snapshot_apply_dryrun_btn.button_type = "warning"
            self.snapshot_fix_apply_block_btn.name = "Fix: Wait"
            self.snapshot_fix_apply_block_btn.disabled = True
            self._record_dryrun_block_transition(previous_code, previous_reason)
            self._refresh_dryrun_meta()
            return

        if not self._last_dryrun_path:
            self._dryrun_apply_ready = False
            self._dryrun_apply_reason = "No successful dry-run available"
            self._dryrun_apply_block_code = "NO_DRYRUN"
            self.snapshot_apply_dryrun_btn.disabled = True
            self.snapshot_apply_dryrun_btn.name = "Apply Dry-run Result"
            self.snapshot_apply_dryrun_btn.button_type = "success"
            self.snapshot_fix_apply_block_btn.name = "Fix: Re-run Dry-run"
            self.snapshot_fix_apply_block_btn.disabled = not bool(self._last_dryrun_source)
            self._record_dryrun_block_transition(previous_code, previous_reason)
            self._refresh_dryrun_meta()
            return

        if not self._is_dryrun_signature_current():
            self._dryrun_apply_ready = False
            self._dryrun_apply_reason = "Dry-run signature mismatch (re-run required)"
            self._dryrun_apply_block_code = "SIGNATURE_MISMATCH"
            self.snapshot_apply_dryrun_btn.disabled = True
            self.snapshot_apply_dryrun_btn.name = "Apply requires fresh dry-run"
            self.snapshot_apply_dryrun_btn.button_type = "warning"
            self.snapshot_fix_apply_block_btn.name = "Fix: Re-run Dry-run"
            self.snapshot_fix_apply_block_btn.disabled = not bool(self._last_dryrun_source)
            self._record_dryrun_block_transition(previous_code, previous_reason)
            self._refresh_dryrun_meta()
            return

        if self._has_hidden_dryrun_changes():
            self._dryrun_apply_ready = False
            self._dryrun_apply_reason = "Filtered mode hides changes (set filter to all)"
            self._dryrun_apply_block_code = "FILTER_HIDDEN"
            self.snapshot_apply_dryrun_btn.disabled = True
            self.snapshot_apply_dryrun_btn.name = "Apply requires filter=all"
            self.snapshot_apply_dryrun_btn.button_type = "warning"
            self.snapshot_fix_apply_block_btn.name = "Fix: Set Filter All"
            self.snapshot_fix_apply_block_btn.disabled = False
            self._record_dryrun_block_transition(previous_code, previous_reason)
            self._refresh_dryrun_meta()
            return

        requires_confirm = self._last_dryrun_changes > self.DRYRUN_CONFIRM_THRESHOLD
        if requires_confirm and not self._pending_dryrun_confirm:
            self._dryrun_apply_ready = True
            self._dryrun_apply_reason = f"Confirmation required ({self._last_dryrun_changes} changes)"
            self._dryrun_apply_block_code = "CONFIRM_REQUIRED"
            self.snapshot_apply_dryrun_btn.disabled = False
            self.snapshot_apply_dryrun_btn.name = f"Confirm Apply ({self._last_dryrun_changes} changes)"
            self.snapshot_apply_dryrun_btn.button_type = "warning"
            self.snapshot_fix_apply_block_btn.name = "Fix: Confirm Apply"
            self.snapshot_fix_apply_block_btn.disabled = False
            self._record_dryrun_block_transition(previous_code, previous_reason)
            self._refresh_dryrun_meta()
            return

        self._dryrun_apply_ready = True
        self._dryrun_apply_reason = "All guards passed"
        self._dryrun_apply_block_code = "READY"
        self.snapshot_apply_dryrun_btn.disabled = False
        self.snapshot_apply_dryrun_btn.name = "Apply Dry-run Result"
        self.snapshot_apply_dryrun_btn.button_type = "success"
        self.snapshot_fix_apply_block_btn.disabled = True
        self._record_dryrun_block_transition(previous_code, previous_reason)
        self._refresh_dryrun_meta()

    def _apply_dryrun_result(self, *_) -> None:
        if self._dryrun_apply_in_progress:
            self._alert_once("profile_snapshot_apply_dryrun_busy", "warning", "Apply action already in progress.", cooldown=1)
            return
        self._dryrun_apply_in_progress = True
        self._refresh_dryrun_meta()
        try:
            path = str(self._last_dryrun_path or "").strip()
            if not path:
                self._alert_once("profile_snapshot_apply_dryrun_empty", "warning", "Run a successful dry-run before apply.", cooldown=2)
                self._log_ops_event("Dry-run apply skipped: no successful dry-run")
                return
            if not self._is_dryrun_signature_current():
                self._last_dryrun_status = "STALE"
                self._refresh_dryrun_meta()
                self._alert_once(
                    "profile_snapshot_apply_dryrun_signature_block",
                    "warning",
                    "Dry-run no longer matches current custom values. Re-run dry-run before apply.",
                    cooldown=2,
                )
                self._log_ops_event("Dry-run apply blocked: signature mismatch")
                return
            if self._has_hidden_dryrun_changes():
                self._alert_once(
                    "profile_snapshot_apply_dryrun_filter_block",
                    "warning",
                    "Set Dry-run Delta to 'All changes' before apply to avoid hidden updates.",
                    cooldown=2,
                )
                self._log_ops_event("Dry-run apply blocked: filtered view hides changes")
                return
            if self._last_dryrun_changes > self.DRYRUN_CONFIRM_THRESHOLD and not self._pending_dryrun_confirm:
                self._pending_dryrun_confirm = True
                self._update_apply_dryrun_button()
                preview = ", ".join(self._last_dryrun_changed_keys[:6])
                if len(self._last_dryrun_changed_keys) > 6:
                    preview = f"{preview}, ..."
                details = f" Fields: {preview}." if preview else ""
                self._alert_once(
                    "profile_snapshot_apply_dryrun_confirm",
                    "warning",
                    f"Confirm apply: {self._last_dryrun_changes} fields will change.{details}",
                    cooldown=2,
                )
                return
            if not os.path.exists(path):
                self._alert_once("profile_snapshot_apply_dryrun_missing", "error", f"Dry-run snapshot no longer exists: {path}", cooldown=2)
                self._log_ops_event(f"Dry-run apply failed: missing file {os.path.basename(path)}")
                self._set_dryrun_state(None, changed_fields=0)
                return
            self.snapshot_import_path.value = path
            self._import_profile_snapshot()
            self._set_dryrun_state(None, changed_fields=0)
            self._last_dryrun_status = "IDLE"
            self._refresh_dryrun_meta()
        finally:
            self._dryrun_apply_in_progress = False
            self._refresh_dryrun_meta()

    def _export_dryrun_csv(self, *_) -> None:
        mode = str(self.snapshot_dryrun_filter.value or self.DRYRUN_FILTER_ALL)
        df = self._get_filtered_dryrun_df()
        if not isinstance(df, pd.DataFrame) or df.empty:
            self._alert_once("dryrun_export_empty", "warning", "No dry-run changes to export.", cooldown=2)
            self._log_ops_event("Dry-run CSV export skipped: empty table")
            return

        export_df = df.copy()
        if "delta_view" in export_df.columns:
            export_df = export_df.drop(columns=["delta_view"])

        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        mode_suffix = self._dryrun_filter_mode_label(mode)
        file_name = f"dryrun_changes_v30_{mode_suffix}_{stamp}.csv"
        out_path = os.path.join(self._project_root(), file_name)
        export_df.to_csv(out_path, index=False)
        self._alert_once("dryrun_export_ok", "success", f"Dry-run CSV exported: {file_name}", cooldown=1)
        self._log_ops_event(f"Dry-run CSV exported: {file_name}")

    def _reset_dryrun_block_audit(self, *_) -> None:
        self._dryrun_block_rows = []
        self._dryrun_block_counts = {}
        self._refresh_dryrun_block_filter_options()
        self._refresh_dryrun_block_audit()
        self._alert_once("dryrun_block_audit_reset", "success", "Dry-run block audit reset.", cooldown=1)
        self._log_ops_event("Dry-run block audit reset")

    def _export_dryrun_block_audit_csv(self, *_) -> None:
        filter_code = str(self.snapshot_dryrun_block_filter.value or "all")
        order_mode = str(self.snapshot_dryrun_block_order.value or "newest")
        selected_rows = list(self._dryrun_block_rows)
        if filter_code != "all":
            selected_rows = [row for row in self._dryrun_block_rows if self._parse_dryrun_block_row(row)[1] == filter_code]
        if order_mode != "oldest":
            selected_rows = list(reversed(selected_rows))

        if not selected_rows:
            self._alert_once("dryrun_block_audit_export_empty", "warning", "No dry-run block audit rows to export.", cooldown=2)
            self._log_ops_event("Dry-run block audit export skipped: empty history")
            return

        rows: list[dict[str, object]] = []
        for item in selected_rows:
            ts, block_code, reason = self._parse_dryrun_block_row(item)
            rows.append(
                {
                    "timestamp_utc": ts,
                    "block_code": str(block_code or "UNKNOWN"),
                    "reason": str(reason or ""),
                    "count_for_code": int(self._dryrun_block_counts.get(str(block_code or "UNKNOWN"), 0)),
                }
            )

        if not rows:
            self._alert_once("dryrun_block_audit_export_empty", "warning", "No dry-run block audit rows to export.", cooldown=2)
            self._log_ops_event("Dry-run block audit export skipped: empty history")
            return

        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filter_suffix = "all" if filter_code == "all" else str(filter_code).lower()
        file_name = f"dryrun_block_audit_v30_{filter_suffix}_{order_mode}_{stamp}.csv"
        out_path = os.path.join(self._project_root(), file_name)
        pd.DataFrame(rows).to_csv(out_path, index=False)
        self._alert_once("dryrun_block_audit_export_ok", "success", f"Dry-run block audit CSV exported: {file_name}", cooldown=1)
        self._log_ops_event(f"Dry-run block audit CSV exported: {file_name}")

    def _validate_selected_snapshot(self, *_) -> None:
        selected = self._resolve_project_path(str(self.snapshot_recent_select.value or "").strip())
        if not selected:
            selected = self._resolve_project_path(str(self.snapshot_import_path.value or "").strip())
        if not selected:
            self._alert_once("profile_snapshot_validate_empty", "warning", "No snapshot selected for validation.", cooldown=2)
            self._log_ops_event("Snapshot validation skipped: no selection")
            return
        if not os.path.exists(selected):
            self._alert_once("profile_snapshot_validate_missing", "error", f"Snapshot not found: {selected}", cooldown=2)
            self._log_ops_event(f"Snapshot validation failed: missing file {os.path.basename(selected)}")
            return

        try:
            with open(selected, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            errors = self._validate_snapshot_payload(payload)
            if errors:
                err_lines = "\n".join(f"- {e}" for e in errors)
                self.snapshot_recent_preview.object = (
                    "### Snapshot Preview\n"
                    f"- File: {os.path.basename(selected)}\n"
                    "- Validation: <span style='color:#ef4444'><b>FAILED</b></span>\n"
                    f"{err_lines}"
                )
                self._alert_once("profile_snapshot_validate_failed", "warning", f"Snapshot validation failed: {len(errors)} issue(s).", cooldown=2)
                self._log_ops_event(f"Snapshot validation failed: {len(errors)} issues")
                return

            self._refresh_snapshot_preview()
            self.snapshot_recent_preview.object = (
                f"{self.snapshot_recent_preview.object}\n"
                "- Validation: <span style='color:#22c55e'><b>OK</b></span>"
            )
            self._alert_once("profile_snapshot_validate_ok", "success", "Snapshot validation passed.", cooldown=1)
            self._log_ops_event(f"Snapshot validation passed: {os.path.basename(selected)}")
        except Exception as exc:
            self._alert_once("profile_snapshot_validate_error", "error", f"Could not validate snapshot: {exc}", cooldown=2)
            self._log_ops_event("Snapshot validation failed: runtime error")

    def _import_profile_snapshot(self, *_) -> None:
        raw_path = str(self.snapshot_import_path.value or "").strip()
        file_path = self._resolve_project_path(raw_path)

        if not file_path:
            candidates = self._list_snapshot_files()
            if not candidates:
                self._alert_once("profile_snapshot_import_empty", "warning", "No snapshot file provided and none found in project folder.", cooldown=2)
                self._log_ops_event("Snapshot import skipped: no file found")
                return
            candidates.sort()
            file_path = candidates[-1]
            self.snapshot_import_path.value = os.path.basename(file_path)

        if not os.path.exists(file_path):
            self._alert_once("profile_snapshot_import_missing", "error", f"Snapshot not found: {file_path}", cooldown=2)
            self._log_ops_event(f"Snapshot import failed: missing file {os.path.basename(file_path)}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)

            validation_errors = self._validate_snapshot_payload(payload)
            if validation_errors:
                self._alert_once(
                    "profile_snapshot_import_schema",
                    "error",
                    f"Snapshot invalid: {validation_errors[0]}",
                    cooldown=2,
                )
                self._log_ops_event("Snapshot import failed: schema validation")
                return

            imported_notes = payload.get("snapshot_notes")
            if isinstance(imported_notes, str):
                self.snapshot_notes.value = self._sanitize_snapshot_notes(imported_notes)

            imported_tag = payload.get("snapshot_tag")
            if isinstance(imported_tag, str):
                self.snapshot_tag.value = self._sanitize_snapshot_tag(imported_tag)

            source = payload.get("custom_profile_values")
            if not isinstance(source, dict):
                fallback = payload.get("runtime_profile_preview")
                if isinstance(fallback, dict):
                    source = fallback

            if not isinstance(source, dict):
                self._alert_once("profile_snapshot_import_no_profile", "error", "Snapshot does not contain importable profile values.", cooldown=2)
                self._log_ops_event("Snapshot import failed: no profile values")
                return

            imported_custom = resolve_custom_profile(source)
            self.profile_select.value = CUSTOM_PROFILE_NAME
            self._write_custom_profile_values(imported_custom)
            self._refresh_custom_profile_state()

            self._alert_once(
                "profile_snapshot_import",
                "success",
                f"Snapshot imported into custom profile: {os.path.basename(file_path)}",
                cooldown=1,
            )
            self._log_ops_event(f"Snapshot imported: {os.path.basename(file_path)}")
        except Exception as exc:
            self._alert_once("profile_snapshot_import_error", "error", f"Could not import snapshot: {exc}", cooldown=2)
            self._log_ops_event("Snapshot import failed: runtime error")

    def _validate_snapshot_payload(self, payload: object) -> list[str]:
        errors: list[str] = []
        if not isinstance(payload, dict):
            return ["payload must be a JSON object"]

        schema_version_raw = payload.get("schema_version", 1)
        try:
            schema_version = int(schema_version_raw)
        except Exception:
            return ["schema_version is invalid"]

        if schema_version > self.SNAPSHOT_SCHEMA_VERSION:
            return [f"schema_version v{schema_version} is newer than supported v{self.SNAPSHOT_SCHEMA_VERSION}"]

        source = payload.get("custom_profile_values")
        fallback = payload.get("runtime_profile_preview")
        if not isinstance(source, dict) and not isinstance(fallback, dict):
            errors.append("missing importable profile values (custom_profile_values/runtime_profile_preview)")

        selected_profile = payload.get("selected_profile")
        if selected_profile is not None and not isinstance(selected_profile, str):
            errors.append("selected_profile must be a string when present")

        validation = payload.get("custom_validation")
        if validation is not None and not isinstance(validation, dict):
            errors.append("custom_validation must be an object when present")

        return errors

    def _sanitize_snapshot_notes(self, notes: object) -> str:
        raw = str(notes or "")
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        # Keep notes compact and single-line in snapshots for easier diffing.
        parts = [line.strip() for line in normalized.split("\n") if line.strip()]
        compact = " | ".join(parts)
        return compact[: self.SNAPSHOT_NOTES_MAX_LEN]

    def _sanitize_snapshot_tag(self, tag: object) -> str:
        raw = str(tag or "").strip().lower()
        allowed = []
        for ch in raw:
            if ch.isalnum() or ch in {"-", "_"}:
                allowed.append(ch)
        compact = "".join(allowed)
        return compact[: self.SNAPSHOT_TAG_MAX_LEN]

    def _format_saved_local(self, utc_timestamp: str) -> str:
        raw = (utc_timestamp or "").strip()
        if not raw:
            return "n/a"
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            local = parsed.astimezone()
            return local.isoformat(timespec="seconds")
        except Exception:
            return "n/a"

    def _utc_to_epoch(self, utc_timestamp: str) -> float | None:
        raw = (utc_timestamp or "").strip()
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return float(parsed.timestamp())
        except Exception:
            return None

    def _apply_runtime_profile(self, *_, notify: bool = True) -> None:
        selected = str(self.profile_select.value)
        if selected == CUSTOM_PROFILE_NAME:
            if not self._refresh_custom_profile_state():
                self._alert_once("profile_invalid", "warning", "Custom profile is invalid. Fix values before apply.", cooldown=2)
                return
            self.runtime_profile = resolve_custom_profile(self._read_custom_profile_values())
        else:
            self.runtime_profile = resolve_profile(selected)
            self._write_custom_profile_values(self.runtime_profile)

        self.alert_conf_min.value = float(self.runtime_profile["alert_min_conf"])
        self.alert_imb_min.value = float(self.runtime_profile["alert_min_imbalance"])
        self.ticket_min_rr.value = float(self.runtime_profile["ticket_min_rr"])
        self.ticket_max_stop_pct.value = float(self.runtime_profile["ticket_max_stop_pct"])
        self.profile_status.object = (
            "### Runtime Profile\n"
            f"- Active profile: **{self.runtime_profile['name']}**\n"
            f"- Trade risk: sl=`{self.runtime_profile['sl_pct']:.3f}` tp=`{self.runtime_profile['tp_pct']:.3f}`\n"
            f"- Alerts: conf>={self.runtime_profile['alert_min_conf']:.2f} depth>={self.runtime_profile['alert_min_imbalance']:.2f}\n"
            f"- Poll: every {int(self.runtime_profile['poll_seconds'])}s | Regime min conf: {self.runtime_profile['min_regime_conf']:.2f}"
        )
        if notify:
            self._alert_once(
                "profile_change",
                "success",
                f"Runtime profile applied: {self.runtime_profile['name']}",
                cooldown=1,
            )

    def _save_runtime_profile(self, *_) -> None:
        try:
            selected = str(self.profile_select.value)
            if selected == CUSTOM_PROFILE_NAME:
                if not self._refresh_custom_profile_state():
                    self._alert_once("profile_save_invalid", "warning", "Cannot save invalid custom profile.", cooldown=2)
                    return
                custom = save_custom_profile(self._read_custom_profile_values())
                self._last_saved_custom = custom
                self._last_saved_custom_utc = load_saved_custom_updated_at()
                self._refresh_custom_profile_state()
                saved = str(custom["name"])
            else:
                saved = save_profile_name(selected)
            self._alert_once(
                "profile_saved",
                "success",
                f"Default profile saved: {saved}",
                cooldown=1,
            )
        except Exception as exc:
            self._alert_once(
                "profile_save_error",
                "error",
                f"Could not save profile: {exc}",
                cooldown=2,
            )

    def _save_apply_custom_profile(self, *_) -> None:
        self.profile_select.value = CUSTOM_PROFILE_NAME
        if not self._refresh_custom_profile_state():
            self._alert_once("profile_save_apply_invalid", "warning", "Cannot save/apply invalid custom profile.", cooldown=2)
            return
        custom = save_custom_profile(self._read_custom_profile_values())
        self._last_saved_custom = custom
        self._last_saved_custom_utc = load_saved_custom_updated_at()
        self._apply_runtime_profile(notify=False)
        self._refresh_custom_profile_state()
        self._alert_once(
            "profile_save_apply_custom",
            "success",
            "Custom profile saved and applied.",
            cooldown=1,
        )

    def _reset_custom_profile(self, *_) -> None:
        base = resolve_profile("balanced")
        self.profile_select.value = CUSTOM_PROFILE_NAME
        self._write_custom_profile_values(base)
        self._refresh_custom_profile_state()
        self._alert_once(
            "profile_custom_reset",
            "success",
            "Custom profile reset to balanced defaults.",
            cooldown=1,
        )

    def _clone_preset_to_custom(self, *_) -> None:
        source = str(self.profile_clone_source.value)
        base = resolve_profile(source)
        self.profile_select.value = CUSTOM_PROFILE_NAME
        self._write_custom_profile_values(base)
        self._refresh_custom_profile_state()
        self._alert_once(
            "profile_custom_clone",
            "success",
            f"Custom profile cloned from {source}.",
            cooldown=1,
        )

    def _read_custom_profile_values(self) -> dict[str, float | int]:
        return {
            "sl_pct": self._fval(self.custom_sl_pct, 0.02),
            "tp_pct": self._fval(self.custom_tp_pct, 0.04),
            "alert_min_conf": self._fval(self.custom_alert_conf, 0.70),
            "alert_min_imbalance": self._fval(self.custom_alert_imb, 0.25),
            "ticket_min_rr": self._fval(self.custom_ticket_rr, 1.5),
            "ticket_max_stop_pct": self._fval(self.custom_stop_pct, 3.0),
            "poll_seconds": self._ival(self.custom_poll_seconds, 45),
            "min_regime_conf": self._fval(self.custom_regime_conf, 0.65),
        }

    def _write_custom_profile_values(self, profile: dict[str, object]) -> None:
        self.custom_sl_pct.value = self._to_float(profile.get("sl_pct"), self.custom_sl_pct.value)
        self.custom_tp_pct.value = self._to_float(profile.get("tp_pct"), self.custom_tp_pct.value)
        self.custom_alert_conf.value = self._to_float(profile.get("alert_min_conf"), self.custom_alert_conf.value)
        self.custom_alert_imb.value = self._to_float(profile.get("alert_min_imbalance"), self.custom_alert_imb.value)
        self.custom_ticket_rr.value = self._to_float(profile.get("ticket_min_rr"), self.custom_ticket_rr.value)
        self.custom_stop_pct.value = self._to_float(profile.get("ticket_max_stop_pct"), self.custom_stop_pct.value)
        self.custom_poll_seconds.value = self._to_int(profile.get("poll_seconds"), self.custom_poll_seconds.value)
        self.custom_regime_conf.value = self._to_float(profile.get("min_regime_conf"), self.custom_regime_conf.value)

    def _alert_once(self, key: str, level: str, message: str, cooldown: int = 20) -> None:
        if not bool(self.alert_enabled.value):
            return
        now = time.time()
        if key == self._last_alert_key and (now - self._last_alert_ts) < cooldown:
            return
        self._last_alert_key = key
        self._last_alert_ts = now

        self._alert_rows.append(
            {
                "ts": datetime.utcnow().strftime("%H:%M:%S"),
                "level": level,
                "key": key,
                "message": message,
            }
        )
        self._alert_rows = self._alert_rows[-200:]
        self.alert_table.value = pd.DataFrame(self._alert_rows)

        # V27.4 – forward to Telegram (fire-and-forget).
        if _TG_AVAILABLE and _tg_send is not None:
            _tg_send(level, key, message)

        try:
            notifications = getattr(pn.state, "notifications", None)
            if notifications is None:
                return
            if level == "error":
                if hasattr(notifications, "error"):
                    notifications.error(message, duration=4000)
            elif level == "warning":
                if hasattr(notifications, "warning"):
                    notifications.warning(message, duration=3500)
            else:
                if hasattr(notifications, "success"):
                    notifications.success(message, duration=3000)
        except Exception:
            # Notifications may be unavailable in some serve contexts.
            pass

    def _apply_preset(self, *_) -> None:
        preset = str(self.preset.value)
        if preset == "Scalp":
            self.timeframe.value = "5m"
            self.ema_fast.value = 20
            self.ema_slow.value = 50
            self.rsi_period.value = 10
            self.macd_fast.value = 8
            self.macd_slow.value = 21
            self.macd_signal.value = 5
            self.bos_lookback.value = 12
            self.choch_lookback.value = 8
        elif preset == "SMC":
            self.timeframe.value = "15m"
            self.ema_fast.value = 50
            self.ema_slow.value = 200
            self.rsi_period.value = 14
            self.macd_fast.value = 12
            self.macd_slow.value = 26
            self.macd_signal.value = 9
            self.bos_lookback.value = 24
            self.choch_lookback.value = 16
            self.show_order_blocks.value = True
            self.show_fvg.value = True
            self.show_structure.value = True
            self.show_bos.value = True
            self.show_choch.value = True
        else:
            self.timeframe.value = "1h"
            self.ema_fast.value = 50
            self.ema_slow.value = 200
            self.rsi_period.value = 14
            self.macd_fast.value = 12
            self.macd_slow.value = 26
            self.macd_signal.value = 9
            self.bos_lookback.value = 20
            self.choch_lookback.value = 12
        self._request_refresh()

    def _auto_setup(self, *_) -> None:
        raw_df = generate_ohlcv(
            symbol=str(self.symbol.value),
            timeframe=str(self.timeframe.value),
            limit=int(V26_CONFIG["history_limit"]),
            exchange_name=str(self.exchange_feed.value),
            data_mode=str(self.exchange_data_mode.value),
        )
        probe = enrich_indicators(raw_df)
        regime = detect_regime(probe)
        vol = float(probe["ATR"].iloc[-1]) if not probe.empty else 0.0
        vol_mean = float(probe["ATR"].mean()) if not probe.empty else 0.0

        if regime["regime"] == "VOLATILE" or vol > vol_mean:
            self.timeframe.value = "5m"
            self.ema_fast.value = 20
            self.ema_slow.value = 50
            self.bos_lookback.value = 12
            self.choch_lookback.value = 8
            self.show_boll.value = True
        else:
            self.timeframe.value = "1h"
            self.ema_fast.value = 50
            self.ema_slow.value = 200
            self.bos_lookback.value = 20
            self.choch_lookback.value = 12

        self.show_order_blocks.value = True
        self.show_fvg.value = True
        self.show_structure.value = True
        self.show_bos.value = True
        self.show_choch.value = True
        self.show_trade_plan.value = True
        self._request_refresh()

    # ── Paper trading handlers ─────────────────────────────────────────────────

    def _paper_buy(self, *_) -> None:
        if self._strict_live_block_active:
            self._alert_once("paper_buy_blocked_strict_live", "error", "Paper BUY blocked by strict live mode.", cooldown=4)
            return
        if self._last_trade is None:
            return
        entry = self._last_price
        sl = float(self._last_trade.get("stop") or entry * 0.98)
        tp = float(self._last_trade.get("take_profit") or entry * 1.04)
        size = float(self.paper_size.value) if self.paper_size.value is not None else 500.0  # type: ignore[arg-type]
        self._paper.open_position(str(self.symbol.value), "BUY", entry, size, sl, tp)
        self._refresh_paper_widgets()

    def _paper_sell(self, *_) -> None:
        if self._strict_live_block_active:
            self._alert_once("paper_sell_blocked_strict_live", "error", "Paper SELL blocked by strict live mode.", cooldown=4)
            return
        if self._last_trade is None:
            return
        entry = self._last_price
        sl = float(self._last_trade.get("take_profit") or entry * 1.02)
        tp = float(self._last_trade.get("stop") or entry * 0.96)
        size = float(self.paper_size.value) if self.paper_size.value is not None else 500.0  # type: ignore[arg-type]
        self._paper.open_position(str(self.symbol.value), "SELL", entry, size, sl, tp)
        self._refresh_paper_widgets()

    def _paper_close_one(self, *_) -> None:
        pid = str(self.paper_close_id.value or "").strip()
        if not pid:
            return
        self._paper.close_position(pid, self._last_price)
        self._refresh_paper_widgets()

    def _paper_close_all(self, *_) -> None:
        self._paper.close_all({str(self.symbol.value): self._last_price})
        self._refresh_paper_widgets()

    def _paper_reset(self, *_) -> None:
        self._paper.reset()
        self._refresh_paper_widgets()

    def _refresh_paper_widgets(self) -> None:
        self._paper.update_unrealized({str(self.symbol.value): self._last_price})
        self.paper_pos_table.value = self._paper.get_positions_df()
        self.paper_trades_table.value = self._paper.get_trades_df()
        n_open = len(self._paper.positions)
        n_closed = len(self._paper.closed_trades)
        self.paper_kpi.object = (
            f"## Paper Trading\n"
            f"- **Equity**: `${self._paper.equity:,.2f}` &nbsp;|&nbsp; "
            f"**Cash**: `${self._paper.cash:,.2f}`  \n"
            f"- **Realized PnL**: `${self._paper.total_pnl:+,.2f}` &nbsp;|&nbsp; "
            f"**Win rate**: `{self._paper.win_rate:.0%}` ({n_closed} trades)  \n"
            f"- **Open positions**: `{n_open}` &nbsp;|&nbsp; "
            f"**Current price**: `${self._last_price:,.2f}`  \n"
            f"- **Data source**: `{get_data_source(str(self.symbol.value), str(self.timeframe.value), str(self.exchange_feed.value))}`"
        )

    @staticmethod
    def _is_port_open(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.35)
                return sock.connect_ex(("127.0.0.1", int(port))) == 0
        except Exception:
            return False

    def _project_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _resolve_project_path(self, path: str) -> str:
        clean = str(path or "").strip()
        if not clean:
            return ""
        if os.path.isabs(clean):
            return clean
        return os.path.join(self._project_root(), clean)

    def _list_snapshot_files(self) -> list[str]:
        root = self._project_root()
        entries: list[str] = []
        for name in os.listdir(root):
            if name.startswith("profile_snapshot_v30_") and name.endswith(".json"):
                entries.append(os.path.join(root, name))
        return entries

    def _get_managed_processes(self) -> list[dict]:
        cmd = (
            "$procs = Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match '^python(\\.exe)?$' -and "
            "($_.CommandLine -match 'binance_alert_app.py|quant_dashboard_v26.py|launch_v30_full.py') } | "
            "Select-Object ProcessId, Name, CommandLine; "
            "$procs | ConvertTo-Json -Compress"
        )
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=8,
            )
            raw = (proc.stdout or "").strip()
            if not raw:
                return []
            data = json.loads(raw)
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]
            return []
        except Exception:
            return []

    def _ops_start_alert(self, *_: object) -> None:
        root = self._project_root()
        poll = os.getenv("ALERT_POLL_SECONDS", str(self.runtime_profile["poll_seconds"]))
        cmd = [
            sys.executable,
            "binance_alert_app.py",
            "--symbol",
            str(self.symbol.value),
            "--timeframe",
            str(self.timeframe.value),
            "--exchange",
            str(self.exchange_feed.value),
            "--poll",
            str(poll),
            "--profile",
            str(self.runtime_profile["name"]),
        ]
        try:
            subprocess.Popen(cmd, cwd=root)
            self._alert_once("ops_start_alert", "success", "Alert engine started.", cooldown=1)
            self._log_ops_event("Alert engine start requested")
        except Exception as exc:
            self._alert_once("ops_start_alert_err", "error", f"Start alert failed: {exc}", cooldown=1)
            self._log_ops_event("Alert engine start failed")
        self._refresh_ops_status()

    def _ops_stop_alert(self, *_: object) -> None:
        cmd = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match '^python(\\.exe)?$' -and $_.CommandLine -match 'binance_alert_app.py' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=8)
            self._alert_once("ops_stop_alert", "warning", "Alert engine stop command sent.", cooldown=1)
            self._log_ops_event("Alert engine stop requested")
        except Exception as exc:
            self._alert_once("ops_stop_alert_err", "error", f"Stop alert failed: {exc}", cooldown=1)
            self._log_ops_event("Alert engine stop failed")
        self._refresh_ops_status()

    def _ops_restart_alert(self, *_: object) -> None:
        self._log_ops_event("Alert engine restart requested")
        self._ops_stop_alert()
        time.sleep(1)
        self._ops_start_alert()

    def _ops_health_summary(self) -> tuple[str, str, str]:
        root = self._project_root()
        health_cmd = [
            sys.executable,
            "healthcheck_v30.py",
            "--json",
            "--profile",
            str(self.runtime_profile["name"]),
        ]
        try:
            run = subprocess.run(health_cmd, cwd=root, capture_output=True, text=True, timeout=30)
            text = (run.stdout or "").strip()
            rows = json.loads(text) if text else []
            if not isinstance(rows, list):
                rows = []

            errors = [r for r in rows if isinstance(r, dict) and r.get("level") == "error" and r.get("ok") is False]
            warnings = [r for r in rows if isinstance(r, dict) and r.get("level") == "warning" and r.get("ok") is False]

            if errors:
                return "CRITICAL", "#ef4444", f"{len(errors)} errors"
            if warnings:
                return "DEGRADED", "#f59e0b", f"{len(warnings)} warnings"
            return "HEALTHY", "#22c55e", "all checks passed"
        except Exception as exc:
            return "UNKNOWN", "#9ca3af", f"healthcheck unavailable: {exc}"

    def _ops_export_diag(self, *_: object) -> None:
        root = self._project_root()
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(root, f"diag_v30_{stamp}.json")
        health_cmd = [
            sys.executable,
            "healthcheck_v30.py",
            "--json",
            "--profile",
            str(self.runtime_profile["name"]),
        ]
        health: object = []
        try:
            run = subprocess.run(health_cmd, cwd=root, capture_output=True, text=True, timeout=30)
            text = (run.stdout or "").strip()
            health = json.loads(text) if text else []
        except Exception:
            health = []

        payload = {
            "timestamp_utc": datetime.utcnow().isoformat(),
            "symbol": str(self.symbol.value),
            "timeframe": str(self.timeframe.value),
            "exchange": str(self.exchange_feed.value),
            "ops_processes": self._get_managed_processes(),
            "healthcheck": health,
        }
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=True)
            self._alert_once("ops_export_diag", "success", f"Diagnostic exported: {os.path.basename(out_path)}", cooldown=1)
            self._log_ops_event(f"Diagnostic exported: {os.path.basename(out_path)}")
        except Exception as exc:
            self._alert_once("ops_export_diag_err", "error", f"Diagnostic export failed: {exc}", cooldown=1)
            self._log_ops_event("Diagnostic export failed")

    def _ops_export_timeline(self, *_: object) -> None:
        root = self._project_root()
        if not self._ops_health_rows:
            self._alert_once("ops_export_timeline_empty", "warning", "No health timeline rows to export.", cooldown=2)
            self._log_ops_event("Timeline export skipped: no health rows")
            return

        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(root, f"health_timeline_v30_{stamp}.csv")
        try:
            pd.DataFrame(self._ops_health_rows).to_csv(out_path, index=False)
            self._alert_once(
                "ops_export_timeline",
                "success",
                f"Timeline exported: {os.path.basename(out_path)}",
                cooldown=1,
            )
            self._log_ops_event(f"Timeline exported: {os.path.basename(out_path)}")
        except Exception as exc:
            self._alert_once("ops_export_timeline_err", "error", f"Timeline export failed: {exc}", cooldown=1)
            self._log_ops_event("Timeline export failed")

    def _refresh_ops_status(self, *_: object) -> None:
        dashboard_port = int(os.getenv("DASHBOARD_PORT", "5026"))
        port_open = self._is_port_open(dashboard_port)
        procs = self._get_managed_processes()
        alert_count = sum(1 for p in procs if "binance_alert_app.py" in str(p.get("CommandLine", "")))
        dashboard_count = sum(1 for p in procs if "quant_dashboard_v26.py" in str(p.get("CommandLine", "")))
        health_label, health_color, health_detail = self._ops_health_summary()

        self._ops_health_rows.append(
            {
                "ts": datetime.utcnow().strftime("%H:%M:%S"),
                "health": health_label,
                "detail": health_detail,
            }
        )
        self._ops_health_rows = self._ops_health_rows[-20:]
        self.ops_health_table.value = pd.DataFrame(self._ops_health_rows)

        if health_label != self._ops_last_health:
            if health_label == "CRITICAL":
                self._alert_once("ops_health_critical", "error", f"Ops health switched to CRITICAL ({health_detail})", cooldown=1)
                print("\a", end="")
            elif health_label == "DEGRADED":
                self._alert_once("ops_health_degraded", "warning", f"Ops health switched to DEGRADED ({health_detail})", cooldown=1)
                print("\a", end="")
            elif health_label == "HEALTHY":
                self._alert_once("ops_health_recovered", "success", "Ops health recovered to HEALTHY", cooldown=1)
            self._ops_last_health = health_label

        self.ops_health_badge.object = (
            "<b>Health:</b> "
            f"<span style='color:{health_color};font-weight:700'>{health_label}</span>"
            f" <span style='color:#9ca3af'>({health_detail})</span>"
        )

        self.ops_table.value = pd.DataFrame(procs)
        self.ops_status.object = (
            "### Ops Status\n"
            f"- Dashboard port `{dashboard_port}` open: **{port_open}**\n"
            f"- Dashboard processes: **{dashboard_count}**\n"
            f"- Alert engine processes: **{alert_count}**\n"
            f"- Last update: `{datetime.utcnow().strftime('%H:%M:%S UTC')}`"
        )

    # ── Main refresh ───────────────────────────────────────────────────────────

    def refresh(self, *_args) -> None:
        raw_df = generate_ohlcv(
            symbol=str(self.symbol.value),
            timeframe=str(self.timeframe.value),
            limit=int(V26_CONFIG["history_limit"]),
            exchange_name=str(self.exchange_feed.value),
            data_mode=str(self.exchange_data_mode.value),
        )
        df = enrich_indicators(
            raw_df,
            ema_fast=self._ival(self.ema_fast, 50),
            ema_slow=self._ival(self.ema_slow, 200),
            rsi_period=self._ival(self.rsi_period, 14),
            macd_fast=self._ival(self.macd_fast, 12),
            macd_slow=self._ival(self.macd_slow, 26),
            macd_signal_period=self._ival(self.macd_signal, 9),
            atr_period=self._ival(self.atr_period, 14),
            bb_window=self._ival(self.bb_window, 20),
            bb_dev=self._fval(self.bb_dev, 2.0),
        )
        df["STRUCTURE"] = detect_structure(df)
        df["BOS"] = detect_bos(df, lookback=self._ival(self.bos_lookback, int(V26_CONFIG["lookback_bos"])))
        df["CHOCH"] = detect_choch(df, lookback=self._ival(self.choch_lookback, int(V26_CONFIG["lookback_choch"])))

        # Replay mode: analyze/display a historical slice for bar-by-bar review.
        if bool(self.replay_enabled.value):
            bars = max(30, self._ival(self.replay_bars, 120))
            max_shift = max(0, len(df) - 30)
            raw_shift = self._ival(self.replay_shift, 0)
            shift = max(0, min(raw_shift, max_shift))
            if shift != raw_shift:
                self.replay_shift.value = shift
                if bool(self.replay_play.value):
                    self.replay_play.value = False
                    self._alert_once("replay_end", "warning", "Replay reached oldest bar; Play stopped.", cooldown=2)
            end = max(30, len(df) - shift)
            start = max(0, end - bars)
            df = df.iloc[start:end].copy()

        self._last_price = float(df["close"].iloc[-1])
        orderbook = generate_orderbook(
            self._last_price,
            symbol=str(self.symbol.value),
            exchange_name=str(self.exchange_feed.value),
            data_mode=str(self.exchange_data_mode.value),
        )
        depth = orderbook_depth(orderbook)
        data_src = get_data_source(str(self.symbol.value), str(self.timeframe.value), str(self.exchange_feed.value))
        feed_meta = get_data_meta(str(self.symbol.value), str(self.timeframe.value), str(self.exchange_feed.value))
        book_meta = get_orderbook_meta(str(self.symbol.value), str(self.exchange_feed.value))
        ex_name = str(self.exchange_feed.value).lower()
        is_dex = ex_name in {"uniswap", "hyperliquid"}
        book_source = str(book_meta.get("source", "unknown"))
        strict_violation = (
            bool(self.strict_live_mode.value)
            and str(self.exchange_data_mode.value).lower() == "live"
            and ("mock" in str(data_src).lower() or "mock" in book_source.lower())
        )
        self._strict_live_block_active = strict_violation
        depth_rows = []
        bids = orderbook.get("bids", [])[:10]
        asks = orderbook.get("asks", [])[:10]
        for i in range(max(len(bids), len(asks))):
            b = bids[i] if i < len(bids) else [None, None]
            a = asks[i] if i < len(asks) else [None, None]
            depth_rows.append(
                {
                    "bid_price": b[0],
                    "bid_qty": b[1],
                    "ask_price": a[0],
                    "ask_qty": a[1],
                }
            )
        self.depth_table.value = pd.DataFrame(depth_rows)
        # Mini heatmap-style depth panel (bid/ask quantity by rank)
        bid_qty = [float(x[1]) for x in bids]
        ask_qty = [float(x[1]) for x in asks]
        depth_fig = go.Figure(
            data=go.Heatmap(
                z=[bid_qty, ask_qty],
                x=[str(i + 1) for i in range(max(len(bid_qty), len(ask_qty)))],
                y=["Bids", "Asks"],
                colorscale="RdYlGn",
            )
        )
        depth_fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), height=250)
        self.depth_heatmap.object = depth_fig
        sm = detect_smart_money(df)

        trend = detect_trend(df)
        momentum = momentum_signal(df)
        breakout = breakout_signal(df)
        vol_state = volatility_state(df)
        trade = generate_trade(
            df,
            sl_pct=float(self.runtime_profile["sl_pct"]),
            tp_pct=float(self.runtime_profile["tp_pct"]),
        )
        self._last_trade = trade

        self.chart.object = self._build_chart(df)

        debate = DebateEngine()
        votes = debate.run(df, list(df["STRUCTURE"].values), depth)
        decision = final_decision(votes)
        if self._strict_live_block_active:
            decision = {"decision": "HOLD", "confidence": 0.0}
            trade = None
            self._last_trade = None
            self._alert_once(
                "strict_live_block",
                "error",
                "Strict live mode blocked signal: fallback/mock data detected in live mode.",
                cooldown=10,
            )
        self.agent_table.value = pd.DataFrame([v.__dict__ for v in votes])

        trade_row = {
            "symbol": self.symbol.value,
            "trend": trend,
            "momentum": momentum,
            "breakout": breakout,
            "volatility": vol_state,
            "decision": decision["decision"],
            "decision_conf": decision["confidence"],
            "entry": trade["entry"] if trade else None,
            "stop": trade["stop"] if trade else None,
            "take_profit": trade["take_profit"] if trade else None,
            "rr": trade["rr"] if trade else None,
        }
        self.trade_table.value = pd.DataFrame([trade_row])

        # Live alerts (confidence + imbalance + structural events)
        conf_min = self._fval(self.alert_conf_min, 0.70)
        imb_min = self._fval(self.alert_imb_min, 0.25)
        conf_val = float(decision["confidence"])
        imb_val = abs(float(depth["imbalance"]))
        if conf_val >= conf_min:
            self._alert_once(
                key=f"decision:{decision['decision']}",
                level="success",
                message=f"Decision {decision['decision']} ({conf_val:.0%})",
            )
        if imb_val >= imb_min:
            self._alert_once(
                key=f"depth:{round(imb_val,2)}",
                level="warning",
                message=f"Depth imbalance high: {depth['imbalance']:.2f}",
            )
        if (df["BOS"].iloc[-1] != "NONE") or (df["CHOCH"].iloc[-1] != "NONE"):
            self._alert_once(
                key=f"struct:{df['BOS'].iloc[-1]}:{df['CHOCH'].iloc[-1]}",
                level="warning",
                message=f"Structure event: BOS={df['BOS'].iloc[-1]} / CHoCH={df['CHOCH'].iloc[-1]}",
            )

        sentiment_proxy = 0.58
        brain_results = [
            trend_ai(df),
            sentiment_ai(sentiment_proxy),
            liquidity_ai(depth["bid_volume"], depth["ask_volume"]),
            volatility_ai(df),
        ]
        brain = fuse_market_state(brain_results)

        regime = detect_regime(df)
        active_strategy = choose_strategy(str(regime["regime"]))
        regime_name = str(regime["regime"])
        if self._last_regime and regime_name != self._last_regime:
            self._alert_once("regime_change", "warning", f"Regime changed: {self._last_regime} -> {regime_name}", cooldown=2)
        self._last_regime = regime_name

        self.market_table.value = pd.DataFrame(
            [
                {"metric": "Market state", "value": brain["state"]},
                {"metric": "Market confidence", "value": brain["confidence"]},
                {"metric": "Regime", "value": regime["regime"]},
                {"metric": "Regime confidence", "value": regime["confidence"]},
                {"metric": "Active strategy", "value": active_strategy},
                {"metric": "Depth imbalance", "value": round(depth["imbalance"], 3)},
                {"metric": "Order blocks", "value": sm["order_blocks"]},
                {"metric": "Fair value gaps", "value": sm["fvg"]},
                {"metric": "Liquidity sweeps", "value": sm["liquidity_sweeps"]},
            ]
        )

        top_strats = evolve_population(population_size=70, keep_top=10)
        self.strategy_table.value = pd.DataFrame(top_strats)

        scores = {}
        for asset in V26_CONFIG["assets"]:
            a_trend = "BULLISH" if asset in {"BTC", "ETH", "SOL", "BNB"} else "BEARISH"
            a_momentum = "STRONG" if asset in {"BTC", "ETH", "SOL"} else "WEAK"
            a_vol = "HIGH" if asset in {"SOL", "BNB", "ADA"} else "LOW"
            scores[asset] = score_asset(a_trend, a_momentum, a_vol)

        alloc = allocate_portfolio(scores, capital=float(V26_CONFIG["risk"]["capital"]))
        alloc = apply_risk_limits(alloc, capital=float(V26_CONFIG["risk"]["capital"]))
        self.portfolio_table.value = pd.DataFrame([{"asset": k, "allocation": v} for k, v in alloc.items()])

        symbol_value = str(self.symbol.value or V26_CONFIG["symbol"])
        prices = scan_prices(symbol_value, V26_CONFIG["exchanges"], anchor_price=float(df["close"].iloc[-1]))
        buy_ex, sell_ex, spread = detect_arbitrage(prices)
        ex_rows = [{"exchange": k, "price": v} for k, v in prices.items()]
        ex_rows.append({"exchange": "best_buy", "price": buy_ex})
        ex_rows.append({"exchange": "best_sell", "price": sell_ex})
        ex_rows.append({"exchange": "spread", "price": spread})
        self.exchange_table.value = pd.DataFrame(ex_rows)

        base_trends = generate_human_trend_data()
        src_df = aggregate_by_source(base_trends, V26_CONFIG["trend_sources"])
        common = find_common_trends(src_df)
        next_trends = predict_next_products(common, top_k=7)
        self.trend_table.value = common[["item", "mentions", "total_volume", "avg_growth", "avg_sentiment", "linked_asset", "trend_score"]].round(3)
        self.next_trend_table.value = next_trends[["item", "linked_asset", "next_score", "total_volume"]].round(3)

        if not next_trends.empty:
            top_item = str(next_trends.iloc[0]["item"])
            top_score = float(next_trends.iloc[0]["next_score"])
        else:
            top_item = "n/a"
            top_score = 0.0
        rr_text = f"{trade['rr']:.2f}" if trade and trade.get("rr") is not None else "n/a"
        self.ai_suggestion.object = (
            "### AI Trade Suggestions\n"
            f"- Decision: **{decision['decision']}** ({decision['confidence']:.1%})\n"
            f"- Plan RR: **{rr_text}**\n"
            f"- Market regime: **{regime_name}**\n"
            f"- Human trend leader: **{top_item}** (score `{top_score:.2f}`)"
        )

        history_df = build_trend_score_history(common.head(5), steps=18)
        hist_fig = go.Figure()
        for item in history_df["item"].unique() if not history_df.empty else []:
            dfi = history_df[history_df["item"] == item]
            hist_fig.add_trace(go.Scatter(x=dfi["time"], y=dfi["score"], mode="lines", name=item))
        hist_fig.update_layout(template="plotly_dark", title="Trend score history (simulated)", margin=dict(l=20, r=20, t=30, b=20), height=280)
        self.trend_history.object = hist_fig

        max_bid_qty = max((float(x[1]) for x in bids), default=0.0)
        max_ask_qty = max((float(x[1]) for x in asks), default=0.0)
        mean_book_qty = (sum((float(x[1]) for x in bids), 0.0) + sum((float(x[1]) for x in asks), 0.0)) / max(len(bids) + len(asks), 1)
        if max(max_bid_qty, max_ask_qty) > (mean_book_qty * 2.8):
            side = "bid" if max_bid_qty >= max_ask_qty else "ask"
            self._alert_once("whale_event", "warning", f"Whale-like {side} wall detected in orderbook", cooldown=6)

        self.pie.object = go.Figure(
            data=[go.Pie(labels=next_trends["item"], values=next_trends["next_score"], hole=0.35)]
        ).update_layout(template="plotly_dark", title="Top Products and Predicted Next Trends")

        src_sent = source_sentiment_snapshot(src_df)

        self.dex_diagnostics.object = (
            "### DEX Diagnostics\n"
            f"- Exchange: **{ex_name}**\n"
            f"- DEX mode: **{is_dex}**\n"
            f"- Data mode: **{self.exchange_data_mode.value}**\n"
            f"- OHLCV source: **{data_src}**\n"
            f"- Orderbook source: **{book_source}**\n"
            f"- OHLCV error: `{feed_meta.get('last_error', '')}`\n"
            f"- Orderbook error: `{book_meta.get('last_error', '')}`\n"
            f"- Strict live block: **{self._strict_live_block_active}**"
        )
        live_interval_s = self._ival(self.live_interval_ms, 8000) / 1000.0
        feed_ts = str(feed_meta.get("last_fetch_utc") or "")
        feed_age_s = -1.0
        if feed_ts:
            try:
                feed_age_s = max(0.0, (datetime.utcnow() - datetime.fromisoformat(feed_ts)).total_seconds())
            except Exception:
                feed_age_s = -1.0
        # V27.3 WS status
        ws_stat = ""
        ws_ready = 0
        if _WS_UI_AVAILABLE and _ws_subscribe is not None and str(self.exchange_feed.value).lower() == "binance":
            _ws_subscribe(str(self.symbol.value), str(self.timeframe.value))
            ws_stat = _ws_status(str(self.symbol.value), str(self.timeframe.value)) if _ws_status is not None else ""
            ws_ready = _ws_candles_ready(str(self.symbol.value), str(self.timeframe.value)) if _ws_candles_ready is not None else 0
        ws_icons = {"live": "🟢", "connecting": "🟡", "reconnecting": "🟠", "stale": "🔴", "disconnected": "⚫", "not_started": "⚪"}
        ws_icon = ws_icons.get(ws_stat, "⚪")
        ws_line = f"- WS stream: {ws_icon} **{ws_stat}** ({ws_ready} candles buffered)\n" if ws_stat else ""
        tg_line = (f"- {_tg_status()}\n" if _TG_AVAILABLE and _tg_status is not None else "- Telegram: not configured\n")

        feed_latency_ms = self._to_float(feed_meta.get("latency_ms"), -1.0)
        book_latency_ms = self._to_float(book_meta.get("latency_ms"), -1.0)
        feed_health = "HEALTHY"
        feed_health_color = "#22c55e"
        feed_reasons: list[str] = []

        if feed_age_s < 0:
            feed_health = "CRITICAL"
            feed_health_color = "#ef4444"
            feed_reasons.append("missing/invalid last_fetch timestamp")
        elif feed_age_s >= (live_interval_s * self.FEED_CRITICAL_AGE_MULTIPLIER):
            feed_health = "CRITICAL"
            feed_health_color = "#ef4444"
            feed_reasons.append(f"stale feed age {feed_age_s:.1f}s")
        elif feed_age_s >= (live_interval_s * self.FEED_WARN_AGE_MULTIPLIER):
            feed_health = "DEGRADED"
            feed_health_color = "#f59e0b"
            feed_reasons.append(f"delayed feed age {feed_age_s:.1f}s")

        max_latency_ms = max(feed_latency_ms, book_latency_ms)
        if max_latency_ms >= self.FEED_CRITICAL_LATENCY_MS:
            feed_health = "CRITICAL"
            feed_health_color = "#ef4444"
            feed_reasons.append(f"high latency {max_latency_ms:.0f}ms")
        elif max_latency_ms >= self.FEED_WARN_LATENCY_MS and feed_health != "CRITICAL":
            feed_health = "DEGRADED"
            feed_health_color = "#f59e0b"
            feed_reasons.append(f"elevated latency {max_latency_ms:.0f}ms")

        if ws_stat in {"stale", "disconnected"}:
            feed_health = "CRITICAL"
            feed_health_color = "#ef4444"
            feed_reasons.append(f"ws={ws_stat}")
        elif ws_stat in {"connecting", "reconnecting", "not_started"} and feed_health != "CRITICAL":
            feed_health = "DEGRADED"
            feed_health_color = "#f59e0b"
            feed_reasons.append(f"ws={ws_stat}")

        if not feed_reasons:
            feed_reasons.append("all checks within thresholds")

        now_ts = time.time()
        if feed_health != self._last_feed_health:
            reason_text = "; ".join(feed_reasons)
            if feed_health == "CRITICAL":
                self._alert_once("feed_health_critical", "error", f"Feed health switched to CRITICAL ({reason_text})", cooldown=2)
            elif feed_health == "DEGRADED":
                self._alert_once("feed_health_degraded", "warning", f"Feed health switched to DEGRADED ({reason_text})", cooldown=2)
            elif feed_health == "HEALTHY":
                self._alert_once("feed_health_recovered", "success", "Feed health recovered to HEALTHY", cooldown=2)
            self._log_ops_event(f"Feed health: {self._last_feed_health} -> {feed_health} ({reason_text})")
            self._last_feed_health = feed_health
            self._feed_health_since_ts = now_ts

        state_elapsed_s = max(0, int(now_ts - self._feed_health_since_ts))
        state_elapsed_m = state_elapsed_s // 60

        feed_health_line = (
            "- Feed health: "
            f"<span style='color:{feed_health_color}'><b>{feed_health}</b></span> "
            f"({'; '.join(feed_reasons)})\n"
        )
        self.feed_quality.object = (
            "### Feed Quality\n"
            f"{feed_health_line}"
            f"{ws_line}"
            f"- Data mode: **{self.exchange_data_mode.value}**\n"
            f"- OHLCV source: **{data_src}**\n"
            f"- OHLCV latency ms: `{feed_meta.get('latency_ms')}`\n"
            f"- OHLCV age s: `{feed_age_s:.1f}`\n"
            f"- OHLCV rows: `{feed_meta.get('rows')}`\n"
            f"- Orderbook latency ms: `{book_meta.get('latency_ms')}`\n"
            f"- Feed health duration: `{state_elapsed_s}s` (~`{state_elapsed_m}m`) in current state\n"
            f"- Thresholds: age warn/crit = `{self.FEED_WARN_AGE_MULTIPLIER:.1f}x/{self.FEED_CRITICAL_AGE_MULTIPLIER:.1f}x` live interval, latency warn/crit = `{self.FEED_WARN_LATENCY_MS:.0f}/{self.FEED_CRITICAL_LATENCY_MS:.0f} ms`\n"
            f"{tg_line}"
        )

        if bool(self.live_enabled.value) and feed_age_s > (live_interval_s * 3.0):
            self._alert_once("feed_stale", "warning", f"Data feed appears stale ({feed_age_s:.0f}s old)", cooldown=10)

        cluster_metrics = self._cluster_metrics_map()
        cluster_cycles = self._to_int(cluster_metrics.get("cycles", 0), 0)
        cluster_tasks = self._to_int(cluster_metrics.get("tasks_completed", 0), 0)
        cluster_workers = self._to_int(cluster_metrics.get("workers_active", 0), 0)
        cluster_avg_ms = self._to_float(cluster_metrics.get("avg_backtest_ms", 0.0), 0.0)
        cluster_source = "orchestrator" if _CLUSTER_AVAILABLE else "unavailable"

        self.kpi.object = (
            "## V26 Smart Chart and Behavior AI\n"
            f"- Symbol: `{self.symbol.value}` ({self.timeframe.value}) @ `{self.exchange_feed.value}` · data: **{data_src}**  \n"
            f"- Data mode: `{self.exchange_data_mode.value}`  \n"
            f"- Strict live mode: `{bool(self.strict_live_mode.value)}`  \n"
            f"- Profile: `{self.runtime_profile['name']}` (sl=`{self.runtime_profile['sl_pct']:.3f}`, tp=`{self.runtime_profile['tp_pct']:.3f}`)  \n"
            f"- Cluster: `{cluster_source}` | workers `{cluster_workers}` | cycles `{cluster_cycles}` | tasks `{cluster_tasks}` | avg `{cluster_avg_ms:.1f} ms`  \n"
            f"- Live mode: `{bool(self.live_enabled.value)}` @ `{self._ival(self.live_interval_ms, 8000)} ms`  \n"
            f"- Params: EMA({self._ival(self.ema_fast, 50)}/{self._ival(self.ema_slow, 200)}), RSI({self._ival(self.rsi_period, 14)}), "
            f"MACD({self._ival(self.macd_fast, 12)},{self._ival(self.macd_slow, 26)},{self._ival(self.macd_signal, 9)})  \n"
            f"- Final decision: `{decision['decision']}` ({decision['confidence']:.1%})  \n"
            f"- Regime: `{regime['regime']}` ({regime['confidence']:.1%})  \n"
            f"- Arbitrage: buy `{buy_ex}` / sell `{sell_ex}` spread `{spread}`  \n"
            f"- Human trend sources tracked: `{len(src_sent)}`"
        )
        self._refresh_paper_widgets()

        initial_capital = float(V26_CONFIG["risk"]["capital"])
        dd = (initial_capital - float(self._paper.equity)) / max(initial_capital, 1.0)
        if dd >= 0.08:
            self._alert_once("drawdown_high", "error", f"Drawdown alert: {dd:.1%}", cooldown=10)

        doctor_report = run_bot_doctor(
            {
                "decision": decision.get("decision"),
                "decision_conf": decision.get("confidence"),
                "regime_conf": regime.get("confidence"),
                "depth_imbalance": depth.get("imbalance"),
                "drawdown": dd,
                "feed_age_s": feed_age_s,
                "live_interval_s": live_interval_s,
                "spread": spread,
            }
        )
        self.doctor_table.value = pd.DataFrame(doctor_report["findings"])
        self.doctor_summary.object = (
            "### Bot Doctor\n"
            f"- Health score: **{doctor_report['health_score']} / 100**\n"
            f"- Top recommendation: **{doctor_report['top_recommendation']}**"
        )
        self._append_doctor_history(doctor_report)
        self.doctor_history_chart.object = self._build_doctor_history_figure()
        burst = self._doctor_burst_snapshot()
        self.doctor_anomaly_status.object = (
            "### Doctor Burst Detector\n"
            f"- Status: <span style='color:{burst['status_color']}'><b>{burst['status']}</b></span>\n"
            f"- Window: `{self.DOCTOR_BURST_WINDOW}` cycles\n"
            f"- Errors sum: `{burst['errors_sum']}` | Warnings sum: `{burst['warnings_sum']}`\n"
            f"- Health range: `{burst['health_min']:.1f}` -> `{burst['health_max']:.1f}`\n"
            f"- Notes: {burst['notes']}"
        )
        self.doctor_cycle_report.object = self._build_doctor_cycle_report(doctor_report, burst)
        self._doctor_recent_logs = [str(item.get("issue", "")) for item in doctor_report.get("findings", [])]
        director_panel, developer_dashboard = self._build_doctor_panels(doctor_report)
        self.doctor_director_summary.object = (
            "### Director Panel\n"
            f"- Bot status: **{director_panel['bot_status']}**\n"
            f"- Findings: `{director_panel['performance_metrics']['findings_count']}` | "
            f"Errors: `{director_panel['performance_metrics']['errors_detected']}` | "
            f"Warnings: `{director_panel['performance_metrics']['warnings_detected']}`\n"
            f"- Health score: **{director_panel['performance_metrics']['health_score']} / 100**"
        )
        self.doctor_developer_summary.object = (
            "### Developer Dashboard\n"
            f"- Active agents: `{', '.join(developer_dashboard['active_agents'])}`\n"
            f"- Pending alerts: `{developer_dashboard['pending_alerts']}`\n"
            f"- System health: **{developer_dashboard['system_health']}**"
        )
        self._refresh_doctor_interactive_table()

        self.cluster_pane.object = self._cluster_md()
        self.cluster_tasks_table.value = self._cluster_df()
        self._refresh_ops_status()


def main() -> None:
    app = SmartChartV26Dashboard()
    app.layout.servable()


if __name__.startswith("bokeh"):
    main()

if __name__ == "__main__":
    main()
