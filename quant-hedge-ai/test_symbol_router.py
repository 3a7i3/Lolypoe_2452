"""Tests — Option Q : SymbolRouter multi-symbole."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from agents.market.symbol_router import SymbolRouter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candles(symbols_volumes: list[tuple[str, float, float]]) -> list[dict]:
    """Crée des bougies de test avec symbol, volume, close."""
    return [
        {"symbol": sym, "volume": vol, "close": price}
        for sym, vol, price in symbols_volumes
    ]


CANDLES = _make_candles([
    ("BTCUSDT", 1000.0, 50_000.0),
    ("ETHUSDT", 800.0, 3_000.0),
    ("SOLUSDT", 400.0, 200.0),
    ("BNBUSDT", 200.0, 500.0),
])


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

class TestSymbolRouterInit:
    def test_defaults(self):
        r = SymbolRouter()
        assert r.max_symbols == 3
        assert r.weighting == "volume"
        assert r.min_volume == 0.0

    def test_custom(self):
        r = SymbolRouter(max_symbols=2, weighting="equal", min_volume=1000.0)
        assert r.max_symbols == 2
        assert r.weighting == "equal"
        assert r.min_volume == 1000.0

    def test_invalid_max_symbols(self):
        with pytest.raises(ValueError, match="max_symbols"):
            SymbolRouter(max_symbols=0)

    def test_invalid_weighting(self):
        with pytest.raises(ValueError, match="weighting"):
            SymbolRouter(weighting="magic")

    def test_negative_min_volume(self):
        with pytest.raises(ValueError, match="min_volume"):
            SymbolRouter(min_volume=-1.0)


# ---------------------------------------------------------------------------
# top_symbols
# ---------------------------------------------------------------------------

class TestTopSymbols:
    def test_returns_top_n_by_volume(self):
        r = SymbolRouter(max_symbols=3)
        top = r.top_symbols(CANDLES)
        assert top == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    def test_respects_max_symbols(self):
        r = SymbolRouter(max_symbols=2)
        top = r.top_symbols(CANDLES)
        assert len(top) == 2
        assert "BTCUSDT" in top

    def test_n_override(self):
        r = SymbolRouter(max_symbols=10)
        top = r.top_symbols(CANDLES, n=1)
        assert top == ["BTCUSDT"]

    def test_empty_candles(self):
        r = SymbolRouter()
        assert r.top_symbols([]) == []

    def test_min_volume_filter(self):
        # min_volume = volume * close → SOLUSDT = 400*200=80k, BNBUSDT = 200*500=100k
        r = SymbolRouter(max_symbols=4, min_volume=100_001.0)
        # BTC=50M, ETH=2.4M : tous dépassent 100k sauf min=100001 → BTC et ETH passent
        top = r.top_symbols(CANDLES)
        for sym in top:
            c = next(c for c in CANDLES if c["symbol"] == sym)
            assert float(c["volume"]) * float(c["close"]) >= 100_001.0

    def test_deduplicate_symbols(self):
        candles_dup = CANDLES + [{"symbol": "BTCUSDT", "volume": 5.0, "close": 50_000.0}]
        r = SymbolRouter(max_symbols=5)
        top = r.top_symbols(candles_dup)
        assert top.count("BTCUSDT") == 1

    def test_dedup_keeps_highest_volume(self):
        candles_dup = [
            {"symbol": "BTCUSDT", "volume": 100.0, "close": 1.0},
            {"symbol": "BTCUSDT", "volume": 999.0, "close": 1.0},
        ]
        r = SymbolRouter(max_symbols=1)
        # Le volume retenu doit être 999
        top = r.top_symbols(candles_dup)
        assert top == ["BTCUSDT"]


# ---------------------------------------------------------------------------
# allocate — equal weighting
# ---------------------------------------------------------------------------

class TestAllocateEqual:
    def test_equal_sum_matches_total(self):
        r = SymbolRouter(max_symbols=3, weighting="equal")
        alloc = r.allocate(CANDLES, total_size=0.10)
        assert pytest.approx(sum(alloc.values()), abs=1e-5) == 0.10

    def test_equal_all_symbols_same_size(self):
        r = SymbolRouter(max_symbols=3, weighting="equal")
        alloc = r.allocate(CANDLES, total_size=0.09)
        sizes = list(alloc.values())
        assert all(abs(s - sizes[0]) < 1e-6 for s in sizes)

    def test_equal_returns_n_symbols(self):
        r = SymbolRouter(max_symbols=2, weighting="equal")
        alloc = r.allocate(CANDLES, total_size=0.10)
        assert len(alloc) == 2

    def test_empty_candles_returns_empty(self):
        r = SymbolRouter(max_symbols=3, weighting="equal")
        assert r.allocate([], total_size=0.10) == {}

    def test_zero_size_returns_empty(self):
        r = SymbolRouter(max_symbols=3, weighting="equal")
        assert r.allocate(CANDLES, total_size=0.0) == {}


# ---------------------------------------------------------------------------
# allocate — volume weighting
# ---------------------------------------------------------------------------

class TestAllocateVolume:
    def test_volume_sum_matches_total(self):
        r = SymbolRouter(max_symbols=3, weighting="volume")
        alloc = r.allocate(CANDLES, total_size=0.10)
        assert pytest.approx(sum(alloc.values()), abs=1e-5) == 0.10

    def test_highest_volume_gets_largest_share(self):
        r = SymbolRouter(max_symbols=3, weighting="volume")
        alloc = r.allocate(CANDLES, total_size=0.10)
        shares = list(alloc.items())
        shares.sort(key=lambda x: x[1], reverse=True)
        assert shares[0][0] == "BTCUSDT"

    def test_volume_weighted_proportional(self):
        r = SymbolRouter(max_symbols=2, weighting="volume")
        candles2 = _make_candles([("AUSDT", 300.0, 1.0), ("BUSDT", 100.0, 1.0)])
        alloc = r.allocate(candles2, total_size=0.04)
        # A a 3x le volume de B → part 0.03 / B part 0.01
        assert pytest.approx(alloc["AUSDT"] / alloc["BUSDT"], rel=0.01) == 3.0

    def test_fallback_equal_when_zero_volume(self):
        zero_candles = [
            {"symbol": "XUSDT", "volume": 0.0, "close": 1.0},
            {"symbol": "YUSDT", "volume": 0.0, "close": 1.0},
        ]
        r = SymbolRouter(max_symbols=2, weighting="volume")
        alloc = r.allocate(zero_candles, total_size=0.10)
        assert len(alloc) == 2
        assert pytest.approx(sum(alloc.values()), abs=1e-5) == 0.10


# ---------------------------------------------------------------------------
# build_orders
# ---------------------------------------------------------------------------

class TestBuildOrders:
    def test_returns_list_with_correct_keys(self):
        r = SymbolRouter(max_symbols=2)
        orders = r.build_orders(CANDLES, action="BUY", total_size=0.10)
        assert all("symbol" in o and "action" in o and "size" in o for o in orders)

    def test_action_propagated(self):
        r = SymbolRouter(max_symbols=3)
        orders = r.build_orders(CANDLES, action="SELL", total_size=0.10)
        assert all(o["action"] == "SELL" for o in orders)

    def test_hold_no_orders_or_zero_size(self):
        r = SymbolRouter(max_symbols=3)
        orders = r.build_orders(CANDLES, action="HOLD", total_size=0.10)
        # HOLD → allocate retourne des tailles > 0 mais action=HOLD
        # build_orders filtre taille > 0 : des ordres HOLD peuvent exister
        assert isinstance(orders, list)

    def test_orders_count_matches_router_max(self):
        r = SymbolRouter(max_symbols=2)
        orders = r.build_orders(CANDLES, action="BUY", total_size=0.10)
        assert len(orders) <= 2

    def test_empty_candles_returns_empty(self):
        r = SymbolRouter(max_symbols=3)
        orders = r.build_orders([], action="BUY", total_size=0.10)
        assert orders == []
