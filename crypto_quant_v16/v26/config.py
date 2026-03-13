"""Configuration for V26 Smart Chart + AI behavior analytics."""

V26_CONFIG = {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "history_limit": 220,
    "lookback_bos": 20,
    "lookback_choch": 12,
    "risk": {
        "sl_pct": 0.02,
        "tp_pct": 0.04,
        "min_confidence": 0.55,
        "capital": 10000.0,
    },
    "features": {
        "ema50": True,
        "ema200": True,
        "rsi": True,
        "macd": True,
        "bollinger": True,
        "volume": True,
        "structure": True,
        "bos": True,
        "choch": True,
        "depth": True,
        "volatility": True,
    },
    "assets": ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "LINK"],
    "exchanges": ["binance", "bybit", "kucoin", "mexc", "kraken", "okx", "coinbase", "uniswap", "hyperliquid"],
    "trend_sources": ["amazon", "temu", "facebook_marketplace", "tiktok", "instagram", "x", "youtube"],
    # Optional DEX routing map for pair/pool-specific live anchors.
    # Fill pair_address/coin values to avoid generic symbol search where possible.
    "dex_routing": {
        "uniswap": {
            "BTC/USDT": {
                "chain": "ethereum",
                "pair_address": "",
                "base_symbol": "WBTC",
                "quote_symbol": "USDT",
            },
            "ETH/USDT": {
                "chain": "ethereum",
                "pair_address": "",
                "base_symbol": "WETH",
                "quote_symbol": "USDT",
            },
            "SOL/USDT": {
                "chain": "solana",
                "pair_address": "",
                "base_symbol": "SOL",
                "quote_symbol": "USDT",
            },
        },
        "hyperliquid": {
            "BTC/USDT": {"coin": "BTC"},
            "ETH/USDT": {"coin": "ETH"},
            "SOL/USDT": {"coin": "SOL"},
        },
    },
    # V27.4 Telegram alerts — override via env vars TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
    # Leave empty strings to disable; or set here for dev convenience.
    "telegram": {
        "bot_token": "",   # e.g. "7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        "chat_ids": "",    # e.g. "123456789" or "123456789,-100987654321"
    },
}
