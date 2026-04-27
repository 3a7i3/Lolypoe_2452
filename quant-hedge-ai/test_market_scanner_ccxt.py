"""Tests unitaires pour MarketScanner avec intégration CCXT.

Tous les appels réseau sont mockés — aucun accès Binance réel.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.market.market_scanner import MarketScanner, _to_ccxt_symbol, _to_internal_symbol


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SYMBOLS = ["BTCUSDT", "ETHUSDT"]

# Bougies OHLCV factices retournées par ccxt :  [ts, open, high, low, close, volume]
_FAKE_OHLCV = {
    "BTCUSDT": [[1_714_000_000_000, 60_000.0, 61_000.0, 59_500.0, 60_500.0, 500.0],
                [1_714_003_600_000, 60_500.0, 61_500.0, 60_400.0, 61_200.0, 420.0]],
    "ETHUSDT": [[1_714_000_000_000, 3_000.0, 3_100.0, 2_980.0, 3_050.0, 12_000.0],
                [1_714_003_600_000, 3_050.0, 3_120.0, 3_040.0, 3_090.0, 11_500.0]],
}


def _make_mock_exchange(ohlcv_map: dict = _FAKE_OHLCV) -> MagicMock:
    """Construit un faux exchange ccxt qui retourne des bougies prédéfinies."""
    exchange = MagicMock()

    def fetch_ohlcv(ccxt_symbol, timeframe, limit=2):
        internal = ccxt_symbol.replace("/", "")
        return ohlcv_map.get(internal, [])

    exchange.fetch_ohlcv.side_effect = fetch_ohlcv
    return exchange


# ---------------------------------------------------------------------------
# Tests des fonctions utilitaires
# ---------------------------------------------------------------------------

def test_to_ccxt_symbol_btcusdt():
    assert _to_ccxt_symbol("BTCUSDT") == "BTC/USDT"


def test_to_ccxt_symbol_ethusdt():
    assert _to_ccxt_symbol("ETHUSDT") == "ETH/USDT"


def test_to_ccxt_symbol_solusdt():
    assert _to_ccxt_symbol("SOLUSDT") == "SOL/USDT"


def test_to_ccxt_symbol_already_formatted():
    assert _to_ccxt_symbol("BTC/USDT") == "BTC/USDT"


def test_to_internal_symbol():
    assert _to_internal_symbol("BTC/USDT") == "BTCUSDT"
    assert _to_internal_symbol("ETH/USDT") == "ETHUSDT"


# ---------------------------------------------------------------------------
# Tests avec exchange mocké
# ---------------------------------------------------------------------------

def test_scan_retourne_vraies_donnees():
    """scan() retourne les données Binance quand l'exchange est disponible."""
    scanner = MarketScanner(symbols=SYMBOLS, timeframe="1h")
    scanner._exchange = _make_mock_exchange()

    result = scanner.scan()
    candles = result["candles"]

    assert len(candles) == len(SYMBOLS)
    assert candles[0]["symbol"] == "BTCUSDT"
    assert candles[0]["close"] == 61_200.0  # dernière bougie BTC
    assert candles[1]["symbol"] == "ETHUSDT"
    assert candles[1]["close"] == 3_090.0   # dernière bougie ETH


def test_scan_structure_chaque_candle():
    """Chaque candle retournée possède tous les champs requis."""
    scanner = MarketScanner(symbols=SYMBOLS)
    scanner._exchange = _make_mock_exchange()

    candles = scanner.scan()["candles"]
    required = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
    for c in candles:
        assert required.issubset(c.keys()), f"Champs manquants dans {c}"
        assert isinstance(c["close"], float)
        assert isinstance(c["volume"], float)
        assert c["close"] > 0
        assert c["volume"] > 0


def test_scan_fallback_si_exchange_none():
    """scan() génère des données synthétiques si _exchange est None."""
    scanner = MarketScanner(symbols=SYMBOLS)
    scanner._exchange = None  # simule ccxt non installé ou non dispo

    candles = scanner.scan()["candles"]
    assert len(candles) == len(SYMBOLS)
    for c in candles:
        assert c["close"] > 0
        assert c["volume"] > 0


def test_scan_fallback_si_api_plante():
    """scan() bascule sur les données synthétiques en cas d'erreur réseau."""
    scanner = MarketScanner(symbols=SYMBOLS)
    exchange = MagicMock()
    exchange.fetch_ohlcv.side_effect = Exception("Connection timeout")
    scanner._exchange = exchange

    candles = scanner.scan()["candles"]
    assert len(candles) == len(SYMBOLS)
    for c in candles:
        assert c["close"] > 0


def test_scan_fallback_si_reponse_vide():
    """scan() bascule sur les données synthétiques si l'API retourne []."""
    scanner = MarketScanner(symbols=SYMBOLS)
    exchange = MagicMock()
    exchange.fetch_ohlcv.return_value = []
    scanner._exchange = exchange

    candles = scanner.scan()["candles"]
    assert len(candles) == len(SYMBOLS)
    for c in candles:
        assert c["close"] > 0


def test_scan_utilise_le_timeframe_configure():
    """scan() transmet bien le timeframe configuré à ccxt."""
    scanner = MarketScanner(symbols=["BTCUSDT"], timeframe="4h")
    scanner._exchange = _make_mock_exchange()

    scanner.scan()

    call_args = scanner._exchange.fetch_ohlcv.call_args
    assert call_args.args[1] == "4h"


def test_scan_un_seul_symbole():
    """Fonctionne avec un seul symbole."""
    scanner = MarketScanner(symbols=["BTCUSDT"])
    scanner._exchange = _make_mock_exchange()

    candles = scanner.scan()["candles"]
    assert len(candles) == 1
    assert candles[0]["symbol"] == "BTCUSDT"


def test_init_exchange_sans_ccxt():
    """_init_exchanges() retourne un dict vide si ccxt n'est pas installé."""
    with patch.dict("sys.modules", {"ccxt": None}):
        scanner = MarketScanner.__new__(MarketScanner)
        scanner.symbols = ["BTCUSDT"]
        scanner.timeframe = "1h"
        scanner.exchange_names = ["binance"]
        exchanges = scanner._init_exchanges()
        assert exchanges == {}


# ---------------------------------------------------------------------------
# Tests de la config env → MarketScanner
# ---------------------------------------------------------------------------

def test_runtime_config_symboles_personnalises():
    """V9_CCXT_SYMBOLS et V9_CCXT_TIMEFRAME sont bien lus depuis l'environnement."""
    import os
    from runtime_config import load_runtime_config_from_env

    os.environ["V9_CCXT_SYMBOLS"] = "BTCUSDT,SOLUSDT"
    os.environ["V9_CCXT_TIMEFRAME"] = "4h"
    try:
        cfg = load_runtime_config_from_env()
        assert cfg.ccxt_symbols == "BTCUSDT,SOLUSDT"
        assert cfg.ccxt_timeframe == "4h"
        symboles = [s.strip() for s in cfg.ccxt_symbols.split(",")]
        assert symboles == ["BTCUSDT", "SOLUSDT"]
    finally:
        os.environ.pop("V9_CCXT_SYMBOLS", None)
        os.environ.pop("V9_CCXT_TIMEFRAME", None)


def test_runtime_config_valeurs_par_defaut():
    """Les valeurs par défaut de CCXT sont correctes."""
    import os
    from runtime_config import load_runtime_config_from_env

    os.environ.pop("V9_CCXT_SYMBOLS", None)
    os.environ.pop("V9_CCXT_TIMEFRAME", None)
    cfg = load_runtime_config_from_env()
    assert "BTCUSDT" in cfg.ccxt_symbols
    assert cfg.ccxt_timeframe == "1h"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
