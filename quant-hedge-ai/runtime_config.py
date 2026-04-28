from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass
class RuntimeConfig:
    max_cycles: int = 3
    population_size: int = 300
    sleep_seconds: int = 2
    seed: int = 42

    generations: int = 3
    max_drawdown: float = 0.25
    min_sharpe_for_trade: float = 2.0
    trade_max_drawdown: float = 0.10
    whale_block_threshold: int = 2
    max_risk_per_trade: float = 0.02
    whale_threshold_usd: float = 500_000.0
    max_strategy_weight: float = 0.3

    monte_carlo_paths: int = 200
    monte_carlo_steps: int = 120
    display_frequency: int = 1
    doctor_telegram_enabled: bool = False
    doctor_telegram_user_id: str = "local-user"
    doctor_v26_report_enabled: bool = False
    doctor_report_export_enabled: bool = False
    doctor_report_export_dir: str = "databases/doctor_reports"

    director_dashboard_enabled: bool = False

    dry_run: bool = False

    # Paramètres CCXT / multi-exchange
    ccxt_symbols: str = "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT"
    ccxt_timeframe: str = "1h"
    ccxt_history_limit: int = 200  # nombre de bougies pour le backtest
    ccxt_cache_ttl: float = 60.0  # secondes — 0 pour désactiver le cache
    ccxt_exchanges: str = "binance,kraken,okx"  # ordre de priorité des exchanges
    ccxt_cache_db: str = ""  # chemin SQLite pour cache persistant (vide = désactivé)
    ccxt_ws_enabled: bool = False  # active le live ticker feed (option G)
    ccxt_ws_interval: float = 5.0  # intervalle de rafraîchissement en secondes (option G)
    ccxt_ws_pro: bool = False  # utilise ccxt.pro WebSocket au lieu du polling REST (option L)

    # Alertes Telegram (option H)
    telegram_bot_token: str = ""   # token du bot (V9_TELEGRAM_BOT_TOKEN)
    telegram_chat_id: str = ""     # ID du canal ou chat (V9_TELEGRAM_CHAT_ID)
    telegram_cooldown: float = 60.0  # secondes entre 2 alertes du même type

    # Kelly Criterion (option K)
    kelly_max_fraction: float = 0.25  # fraction max du capital par trade (V9_KELLY_MAX_FRACTION)
    kelly_half: bool = True           # utilise half-Kelly pour réduire la variance (V9_KELLY_HALF)

    # CVaR / Expected Shortfall (option M)
    cvar_confidence: float = 0.95     # niveau de confiance (V9_CVAR_CONFIDENCE)
    cvar_max_loss: float = 0.05       # perte max tolérée dans le tail (V9_CVAR_MAX_LOSS)

    # Strategy Scoreboard SQL (option N)
    scoreboard_sql_path: str = "databases/strategy_scoreboard.db"  # V9_SCOREBOARD_SQL_PATH

    # Paper Trading live (option O)
    initial_balance: float = 100_000.0  # capital initial en USD (V9_INITIAL_BALANCE)

    # Circuit Breakers (option P)
    cb_daily_loss_limit: float = 0.05     # perte journalière max en fraction du capital (V9_CB_DAILY_LOSS)
    cb_drawdown_limit: float = 0.15       # drawdown max global (V9_CB_DRAWDOWN_LIMIT)
    cb_consecutive_losses: int = 3        # pertes consécutives avant blocage (V9_CB_CONSECUTIVE)

    # Multi-symbole (option Q)
    symbol_router_max: int = 3            # nombre de symboles tradés en parallèle (V9_SYMBOL_ROUTER_MAX)
    symbol_router_weighting: str = "volume"  # "volume" ou "equal" (V9_SYMBOL_ROUTER_WEIGHTING)
    symbol_router_min_volume: float = 0.0    # volume minimum USD pour être éligible (V9_SYMBOL_ROUTER_MIN_VOLUME)

    # Sentiment / Fear & Greed (option R)
    sentiment_enabled: bool = True        # active le feed Fear & Greed (V9_SENTIMENT_ENABLED)
    sentiment_cache_ttl: float = 300.0    # TTL du cache en secondes (V9_SENTIMENT_CACHE_TTL)
    sentiment_fallback_score: int = 50    # score si API inaccessible (V9_SENTIMENT_FALLBACK)
    sentiment_bearish_threshold: int = 30  # score en dessous duquel on réduit la taille (V9_SENTIMENT_BEARISH_THRESHOLD)

    # Stop Loss / Take Profit (option S)
    sl_pct: float = 0.05           # stop loss fixe en fraction de l'entrée (V9_SL_PCT)
    tp_pct: float = 0.10           # take profit fixe en fraction de l'entrée (V9_TP_PCT)
    sl_atr_enabled: bool = False   # SL/TP basé sur ATR au lieu du % fixe (V9_SL_ATR_ENABLED)
    sl_atr_multiplier: float = 2.0  # distance SL = ATR × multiplicateur (V9_SL_ATR_MULT)
    sl_tp_multiplier: float = 4.0   # distance TP = ATR × multiplicateur (V9_SL_TP_MULT)

    # Trailing Stop (option T)
    sl_trailing_enabled: bool = False  # active le trailing stop (V9_SL_TRAILING_ENABLED)
    sl_trailing_pct: float = 0.03      # % trailing en dessous du pic (V9_SL_TRAILING_PCT)

    # Walk-Forward Optimization (option U)
    wfo_enabled: bool = False      # active la validation WFO (V9_WFO_ENABLED)
    wfo_n_splits: int = 5          # nombre de splits train/test (V9_WFO_N_SPLITS)
    wfo_train_ratio: float = 0.7   # fraction de train par split (V9_WFO_TRAIN_RATIO)

    def as_dict(self) -> dict[str, int | float | bool | str]:
        return asdict(self)


def get_env_int(name: str, default: int, min_value: int | None = None, max_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        value = int(raw)
    except (TypeError, ValueError):
        print(f"[WARN] Invalid value for {name}={raw!r}. Using default={default}.")
        return default

    if min_value is not None and value < min_value:
        print(f"[WARN] {name}={value} is below min_value={min_value}. Using min_value.")
        value = min_value

    if max_value is not None and value > max_value:
        print(f"[WARN] {name}={value} is above max_value={max_value}. Using max_value.")
        value = max_value

    return value


def get_env_float(name: str, default: float, min_value: float | None = None, max_value: float | None = None) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        value = float(raw)
    except (TypeError, ValueError):
        print(f"[WARN] Invalid value for {name}={raw!r}. Using default={default}.")
        return default

    if min_value is not None and value < min_value:
        print(f"[WARN] {name}={value} is below min_value={min_value}. Using min_value.")
        value = min_value

    if max_value is not None and value > max_value:
        print(f"[WARN] {name}={value} is above max_value={max_value}. Using max_value.")
        value = max_value

    return value


def get_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False

    print(f"[WARN] Invalid boolean value for {name}={raw!r}. Using default={default}.")
    return default


def get_env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    return value or default


def load_runtime_config_from_env() -> RuntimeConfig:
    return RuntimeConfig(
        max_cycles=get_env_int("V9_MAX_CYCLES", 3, min_value=0),
        population_size=get_env_int("V9_POPULATION", 300, min_value=1, max_value=10_000),
        sleep_seconds=get_env_int("V9_SLEEP_SECONDS", 2, min_value=0, max_value=3_600),
        seed=get_env_int("V9_SEED", 42, min_value=0),
        generations=get_env_int("V9_GENERATIONS", 3, min_value=1, max_value=100),
        max_drawdown=get_env_float("V9_MAX_DRAWDOWN", 0.25, min_value=0.01, max_value=1.0),
        min_sharpe_for_trade=get_env_float("V9_MIN_SHARPE", 2.0, min_value=0.0, max_value=100.0),
        trade_max_drawdown=get_env_float("V9_TRADE_MAX_DRAWDOWN", 0.10, min_value=0.001, max_value=1.0),
        whale_block_threshold=get_env_int("V9_WHALE_BLOCK_THRESHOLD", 2, min_value=0, max_value=100),
        max_risk_per_trade=get_env_float("V9_MAX_RISK_PER_TRADE", 0.02, min_value=0.001, max_value=1.0),
        whale_threshold_usd=get_env_float("V9_WHALE_THRESHOLD", 500_000.0, min_value=1_000.0),
        max_strategy_weight=get_env_float("V9_MAX_POSITION_WEIGHT", 0.3, min_value=0.01, max_value=1.0),
        monte_carlo_paths=get_env_int("V9_MONTECARLO_SIMULATIONS", 200, min_value=10, max_value=100_000),
        monte_carlo_steps=get_env_int("V9_MONTECARLO_STEPS", 120, min_value=10, max_value=10_000),
        display_frequency=get_env_int("V9_DISPLAY_FREQUENCY", 1, min_value=1, max_value=1_000),
        doctor_telegram_enabled=get_env_bool("V9_DOCTOR_TELEGRAM_ENABLED", False),
        doctor_telegram_user_id=get_env_str("V9_DOCTOR_TELEGRAM_USER_ID", "local-user"),
        doctor_v26_report_enabled=get_env_bool("V9_DOCTOR_V26_REPORT_ENABLED", False),
        doctor_report_export_enabled=get_env_bool("V9_DOCTOR_REPORT_EXPORT_ENABLED", False),
        doctor_report_export_dir=get_env_str("V9_DOCTOR_REPORT_EXPORT_DIR", "databases/doctor_reports"),
        dry_run=get_env_bool("V9_DRY_RUN", False),
        ccxt_symbols=get_env_str("V9_CCXT_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT"),
        ccxt_timeframe=get_env_str("V9_CCXT_TIMEFRAME", "1h"),
        ccxt_history_limit=get_env_int("V9_CCXT_HISTORY_LIMIT", 200, min_value=10, max_value=1000),
        ccxt_cache_ttl=get_env_float("V9_CCXT_CACHE_TTL", 60.0, min_value=0.0, max_value=3600.0),
        ccxt_exchanges=get_env_str("V9_CCXT_EXCHANGES", "binance,kraken,okx"),
        ccxt_cache_db=get_env_str("V9_CCXT_CACHE_DB", ""),
        ccxt_ws_enabled=get_env_bool("V9_CCXT_WS_ENABLED", False),
        ccxt_ws_interval=get_env_float("V9_CCXT_WS_INTERVAL", 5.0, min_value=1.0, max_value=60.0),
        ccxt_ws_pro=get_env_bool("V9_CCXT_WS_PRO", False),
        telegram_bot_token=get_env_str("V9_TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=get_env_str("V9_TELEGRAM_CHAT_ID", ""),
        telegram_cooldown=get_env_float("V9_TELEGRAM_COOLDOWN", 60.0, min_value=5.0, max_value=3600.0),
        kelly_max_fraction=get_env_float("V9_KELLY_MAX_FRACTION", 0.25, min_value=0.01, max_value=1.0),
        kelly_half=get_env_bool("V9_KELLY_HALF", True),
        cvar_confidence=get_env_float("V9_CVAR_CONFIDENCE", 0.95, min_value=0.50, max_value=0.999),
        cvar_max_loss=get_env_float("V9_CVAR_MAX_LOSS", 0.05, min_value=0.001, max_value=1.0),
        scoreboard_sql_path=get_env_str("V9_SCOREBOARD_SQL_PATH", "databases/strategy_scoreboard.db"),
        initial_balance=get_env_float("V9_INITIAL_BALANCE", 100_000.0, min_value=1.0),
        cb_daily_loss_limit=get_env_float("V9_CB_DAILY_LOSS", 0.05, min_value=0.0, max_value=1.0),
        cb_drawdown_limit=get_env_float("V9_CB_DRAWDOWN_LIMIT", 0.15, min_value=0.0, max_value=1.0),
        cb_consecutive_losses=get_env_int("V9_CB_CONSECUTIVE", 3, min_value=0, max_value=100),
        symbol_router_max=get_env_int("V9_SYMBOL_ROUTER_MAX", 3, min_value=1, max_value=50),
        symbol_router_weighting=get_env_str("V9_SYMBOL_ROUTER_WEIGHTING", "volume"),
        symbol_router_min_volume=get_env_float("V9_SYMBOL_ROUTER_MIN_VOLUME", 0.0, min_value=0.0),
        sentiment_enabled=get_env_bool("V9_SENTIMENT_ENABLED", True),
        sentiment_cache_ttl=get_env_float("V9_SENTIMENT_CACHE_TTL", 300.0, min_value=0.0, max_value=3600.0),
        sentiment_fallback_score=get_env_int("V9_SENTIMENT_FALLBACK", 50, min_value=0, max_value=100),
        sentiment_bearish_threshold=get_env_int("V9_SENTIMENT_BEARISH_THRESHOLD", 30, min_value=0, max_value=100),
        sl_pct=get_env_float("V9_SL_PCT", 0.05, min_value=0.001, max_value=1.0),
        tp_pct=get_env_float("V9_TP_PCT", 0.10, min_value=0.0, max_value=10.0),
        sl_atr_enabled=get_env_bool("V9_SL_ATR_ENABLED", False),
        sl_atr_multiplier=get_env_float("V9_SL_ATR_MULT", 2.0, min_value=0.1, max_value=20.0),
        sl_tp_multiplier=get_env_float("V9_SL_TP_MULT", 4.0, min_value=0.0, max_value=40.0),
        sl_trailing_enabled=get_env_bool("V9_SL_TRAILING_ENABLED", False),
        sl_trailing_pct=get_env_float("V9_SL_TRAILING_PCT", 0.03, min_value=0.001, max_value=1.0),
        wfo_enabled=get_env_bool("V9_WFO_ENABLED", False),
        wfo_n_splits=get_env_int("V9_WFO_N_SPLITS", 5, min_value=2, max_value=50),
        wfo_train_ratio=get_env_float("V9_WFO_TRAIN_RATIO", 0.7, min_value=0.1, max_value=0.95),
    )
