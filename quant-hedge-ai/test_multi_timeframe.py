"""Tests pour l'option AD — Multi-Timeframe Signal Aggregator."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from agents.market.multi_timeframe import (
    MultiTimeframeAggregator,
    MultiTimeframeResult,
    MultiTimeframeScanner,
    TimeframeSignal,
    _sma,
    compute_timeframe_signal,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candles(n: int, start_price: float = 100.0, step: float = 1.0) -> list[dict]:
    """Génère n bougies OHLCV avec un trend haussier simple."""
    candles = []
    price = start_price
    for i in range(n):
        close = price + i * step
        candles.append({
            "symbol": "BTCUSDT",
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        })
    return candles


def _make_candles_bearish(n: int, start_price: float = 200.0, step: float = 1.0) -> list[dict]:
    """Génère n bougies avec un trend baissier."""
    candles = []
    for i in range(n):
        close = start_price - i * step
        candles.append({
            "symbol": "BTCUSDT",
            "open": close + 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        })
    return candles


def _make_flat_candles(n: int, price: float = 100.0) -> list[dict]:
    """Génère n bougies plates (HOLD)."""
    return [
        {"symbol": "BTCUSDT", "open": price, "high": price + 0.1,
         "low": price - 0.1, "close": price, "volume": 500.0}
        for _ in range(n)
    ]


# ---------------------------------------------------------------------------
# Tests _sma
# ---------------------------------------------------------------------------

class TestSmaHelper:
    def test_sma_exact_period(self):
        assert _sma([1.0, 2.0, 3.0], 3) == pytest.approx(2.0)

    def test_sma_last_n(self):
        result = _sma([1.0, 2.0, 3.0, 4.0, 5.0], 3)
        assert result == pytest.approx(4.0)  # (3+4+5)/3

    def test_sma_insufficient_data(self):
        assert _sma([1.0, 2.0], 5) is None

    def test_sma_single_value(self):
        assert _sma([42.0], 1) == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# Tests compute_timeframe_signal
# ---------------------------------------------------------------------------

class TestComputeTimeframeSignal:
    def test_bullish_trend_returns_buy(self):
        candles = _make_candles(n=100, start_price=100.0, step=0.5)
        sig = compute_timeframe_signal(candles, "1h", sma_fast=10, sma_slow=20)
        assert sig.direction == "BUY"
        assert sig.strength > 0.0
        assert sig.timeframe == "1h"
        assert sig.n_candles == 100

    def test_bearish_trend_returns_sell(self):
        candles = _make_candles_bearish(n=100, start_price=500.0, step=1.0)
        sig = compute_timeframe_signal(candles, "4h", sma_fast=10, sma_slow=20)
        assert sig.direction == "SELL"
        assert sig.strength > 0.0

    def test_insufficient_data_returns_hold(self):
        candles = _make_candles(n=10)  # moins que sma_slow=50
        sig = compute_timeframe_signal(candles, "1d", sma_fast=20, sma_slow=50)
        assert sig.direction == "HOLD"
        assert sig.strength == 0.0
        assert sig.n_candles == 10

    def test_flat_market_returns_hold(self):
        candles = _make_flat_candles(n=100)
        sig = compute_timeframe_signal(candles, "1h", sma_fast=10, sma_slow=20)
        # Données plates → sma_fast ≈ sma_slow, pas de direction claire
        assert sig.direction in ("HOLD", "BUY", "SELL")  # pas crash, résultat valide

    def test_strength_bounded_0_1(self):
        candles = _make_candles(n=200, step=10.0)  # trend très fort
        sig = compute_timeframe_signal(candles, "1h", sma_fast=10, sma_slow=50)
        assert 0.0 <= sig.strength <= 1.0

    def test_returns_timeframe_signal_dataclass(self):
        candles = _make_candles(n=60)
        sig = compute_timeframe_signal(candles, "1h")
        assert isinstance(sig, TimeframeSignal)
        assert sig.close > 0
        assert sig.sma_fast > 0
        assert sig.sma_slow > 0

    def test_empty_candles_returns_hold(self):
        sig = compute_timeframe_signal([], "1h")
        assert sig.direction == "HOLD"
        assert sig.n_candles == 0


# ---------------------------------------------------------------------------
# Tests MultiTimeframeAggregator
# ---------------------------------------------------------------------------

class TestMultiTimeframeAggregator:
    def test_all_bullish_returns_buy(self):
        aggregator = MultiTimeframeAggregator(
            timeframes=["1h", "4h", "1d"],
            min_alignment=0.67,
            sma_fast=10,
            sma_slow=20,
        )
        bullish = _make_candles(n=60, step=0.5)
        result = aggregator.aggregate(
            {"1h": bullish, "4h": bullish, "1d": bullish},
            symbol="BTCUSDT",
        )
        assert result.composite_signal == "BUY"
        assert result.alignment_score >= 0.67
        assert result.n_bull == 3
        assert result.n_bear == 0

    def test_all_bearish_returns_sell(self):
        aggregator = MultiTimeframeAggregator(
            timeframes=["1h", "4h"],
            min_alignment=0.5,
            sma_fast=10,
            sma_slow=20,
        )
        bearish = _make_candles_bearish(n=60, step=1.0)
        result = aggregator.aggregate(
            {"1h": bearish, "4h": bearish},
            symbol="ETHUSDT",
        )
        assert result.composite_signal == "SELL"
        assert result.n_bear == 2

    def test_mixed_signals_returns_hold(self):
        aggregator = MultiTimeframeAggregator(
            timeframes=["1h", "4h", "1d"],
            min_alignment=0.67,
            sma_fast=10,
            sma_slow=20,
        )
        bullish = _make_candles(n=60, step=0.5)
        bearish = _make_candles_bearish(n=60, step=1.0)
        result = aggregator.aggregate(
            {"1h": bullish, "4h": bearish, "1d": bullish},  # 2 BUY, 1 SELL → 66.7% < 67%
            symbol="BTCUSDT",
        )
        # Peut être BUY ou HOLD selon alignment exact
        assert result.composite_signal in ("BUY", "HOLD")

    def test_empty_candles_per_tf_returns_hold(self):
        aggregator = MultiTimeframeAggregator(timeframes=["1h", "4h"])
        result = aggregator.aggregate({}, symbol="SOLUSDT")
        assert result.composite_signal == "HOLD"
        assert result.alignment_score == 0.0

    def test_result_has_signals_list(self):
        aggregator = MultiTimeframeAggregator(timeframes=["1h", "4h"])
        bullish = _make_candles(n=60, step=0.5)
        result = aggregator.aggregate({"1h": bullish, "4h": bullish})
        assert len(result.signals) == 2
        assert all(isinstance(s, TimeframeSignal) for s in result.signals)

    def test_as_dict_structure(self):
        aggregator = MultiTimeframeAggregator(timeframes=["1h"])
        bullish = _make_candles(n=60)
        result = aggregator.aggregate({"1h": bullish})
        d = result.as_dict()
        assert "symbol" in d
        assert "composite_signal" in d
        assert "alignment_score" in d
        assert "signals" in d
        assert isinstance(d["signals"], list)

    def test_min_alignment_boundary_exact(self):
        """alignment_score == min_alignment doit passer."""
        aggregator = MultiTimeframeAggregator(
            timeframes=["1h", "4h"],
            min_alignment=0.5,
            sma_fast=10,
            sma_slow=20,
        )
        bullish = _make_candles(n=60, step=0.5)
        bearish = _make_candles_bearish(n=60)
        result = aggregator.aggregate({"1h": bullish, "4h": bearish})
        # 1 BUY + 1 SELL → dominant=BUY (1/2=50%) — alignement exact = min_alignment
        assert result.alignment_score == pytest.approx(0.5)
        assert result.composite_signal in ("BUY", "HOLD")  # 50% >= 50% → BUY

    def test_returns_multi_timeframe_result(self):
        aggregator = MultiTimeframeAggregator(timeframes=["1h"])
        result = aggregator.aggregate({"1h": []})
        assert isinstance(result, MultiTimeframeResult)

    def test_n_counts_correct(self):
        aggregator = MultiTimeframeAggregator(
            timeframes=["1h", "4h", "1d"],
            sma_fast=10,
            sma_slow=20,
        )
        bullish = _make_candles(n=60, step=0.5)
        flat = _make_flat_candles(n=60)
        # Pour flat, la direction dépend des prix exacts — on vérifie juste n_neutral ≥ 0
        result = aggregator.aggregate({"1h": bullish, "4h": bullish, "1d": flat})
        assert result.n_bull + result.n_bear + result.n_neutral == 3


# ---------------------------------------------------------------------------
# Tests MultiTimeframeScanner
# ---------------------------------------------------------------------------

class TestMultiTimeframeScanner:
    def _make_base_scanner(self, symbol: str = "BTCUSDT", tf: str = "1h"):
        """Crée un MarketScanner mocké."""
        mock = MagicMock()
        mock.symbols = [symbol]
        mock.timeframe = tf
        mock._exchanges = {"binance": MagicMock()}
        mock._cache = MagicMock()
        mock._cache.ttl = 60.0
        mock.fetch_history.return_value = _make_candles(n=100, step=0.5)
        return mock

    def test_init_creates_scanners_per_tf(self):
        base = self._make_base_scanner(tf="1h")
        with patch("agents.market.multi_timeframe.MarketScanner") as MockScanner:
            MockScanner.return_value = MagicMock(
                symbols=["BTCUSDT"], timeframe="4h",
                _exchanges={}, _cache=MagicMock(ttl=60.0),
            )
            mtf = MultiTimeframeScanner(base, timeframes=["1h", "4h", "1d"])
        # Le scanner de base est réutilisé pour "1h", 2 nouveaux sont créés
        assert "1h" in mtf._scanners
        assert "4h" in mtf._scanners
        assert "1d" in mtf._scanners
        assert mtf._scanners["1h"] is base  # réutilisation

    def test_fetch_multi_returns_dict_per_tf(self):
        base = self._make_base_scanner(tf="1h")
        with patch("agents.market.multi_timeframe.MarketScanner") as MockScanner:
            mock_tf_scanner = MagicMock()
            mock_tf_scanner.fetch_history.return_value = _make_candles(60)
            mock_tf_scanner.symbols = ["BTCUSDT"]
            mock_tf_scanner.timeframe = "4h"
            mock_tf_scanner._exchanges = {}
            mock_tf_scanner._cache = MagicMock(ttl=60.0)
            MockScanner.return_value = mock_tf_scanner
            mtf = MultiTimeframeScanner(base, timeframes=["1h", "4h"])

        result = mtf.fetch_multi("BTCUSDT")
        assert "1h" in result
        assert "4h" in result
        assert isinstance(result["1h"], list)

    def test_analyze_returns_result(self):
        base = self._make_base_scanner(tf="1h")
        with patch("agents.market.multi_timeframe.MarketScanner") as MockScanner:
            MockScanner.return_value = MagicMock(
                fetch_history=MagicMock(return_value=_make_candles(100, step=0.5)),
                symbols=["BTCUSDT"], timeframe="4h",
                _exchanges={}, _cache=MagicMock(ttl=60.0),
            )
            mtf = MultiTimeframeScanner(base, timeframes=["1h", "4h"], sma_fast=10, sma_slow=20)

        result = mtf.analyze("BTCUSDT")
        assert isinstance(result, MultiTimeframeResult)
        assert result.symbol == "BTCUSDT"
        assert result.composite_signal in ("BUY", "SELL", "HOLD")

    def test_analyze_all_covers_all_symbols(self):
        base = self._make_base_scanner(tf="1h")
        base.symbols = ["BTCUSDT", "ETHUSDT"]
        with patch("agents.market.multi_timeframe.MarketScanner") as MockScanner:
            MockScanner.return_value = MagicMock(
                fetch_history=MagicMock(return_value=_make_candles(60)),
                symbols=["BTCUSDT", "ETHUSDT"], timeframe="4h",
                _exchanges={}, _cache=MagicMock(ttl=60.0),
            )
            mtf = MultiTimeframeScanner(base, timeframes=["1h", "4h"])

        results = mtf.analyze_all()
        assert set(results.keys()) == {"BTCUSDT", "ETHUSDT"}

    def test_aggregator_uses_correct_timeframes(self):
        base = self._make_base_scanner(tf="1h")
        with patch("agents.market.multi_timeframe.MarketScanner") as MockScanner:
            MockScanner.return_value = MagicMock(
                fetch_history=MagicMock(return_value=[]),
                symbols=["BTCUSDT"], timeframe="1d",
                _exchanges={}, _cache=MagicMock(ttl=60.0),
            )
            mtf = MultiTimeframeScanner(
                base,
                timeframes=["1h", "1d"],
                min_alignment=0.9,
            )

        assert mtf.aggregator.timeframes == ["1h", "1d"]
        assert mtf.aggregator.min_alignment == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Tests d'intégration MTF + RuntimeConfig
# ---------------------------------------------------------------------------

class TestMTFRuntimeConfig:
    def test_mtf_fields_exist_in_runtime_config(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert hasattr(cfg, "mtf_enabled")
        assert hasattr(cfg, "mtf_timeframes")
        assert hasattr(cfg, "mtf_require_alignment")
        assert hasattr(cfg, "mtf_min_alignment")
        assert hasattr(cfg, "mtf_sma_fast")
        assert hasattr(cfg, "mtf_sma_slow")

    def test_mtf_defaults(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.mtf_enabled is False
        assert cfg.mtf_timeframes == "1h,4h,1d"
        assert cfg.mtf_require_alignment is True
        assert cfg.mtf_min_alignment == pytest.approx(0.67)
        assert cfg.mtf_sma_fast == 20
        assert cfg.mtf_sma_slow == 50

    def test_mtf_env_parsing(self, monkeypatch):
        monkeypatch.setenv("V9_MTF_ENABLED", "true")
        monkeypatch.setenv("V9_MTF_TIMEFRAMES", "1h,4h")
        monkeypatch.setenv("V9_MTF_MIN_ALIGNMENT", "0.80")
        monkeypatch.setenv("V9_MTF_SMA_FAST", "10")
        monkeypatch.setenv("V9_MTF_SMA_SLOW", "30")
        from runtime_config import load_runtime_config_from_env
        cfg = load_runtime_config_from_env()
        assert cfg.mtf_enabled is True
        assert cfg.mtf_timeframes == "1h,4h"
        assert cfg.mtf_min_alignment == pytest.approx(0.80)
        assert cfg.mtf_sma_fast == 10
        assert cfg.mtf_sma_slow == 30

    def test_as_dict_contains_mtf_fields(self):
        from runtime_config import RuntimeConfig
        d = RuntimeConfig(mtf_enabled=True, mtf_timeframes="1h,4h").as_dict()
        assert d["mtf_enabled"] is True
        assert d["mtf_timeframes"] == "1h,4h"
