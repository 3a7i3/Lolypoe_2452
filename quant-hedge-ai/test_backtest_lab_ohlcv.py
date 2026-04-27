"""Tests unitaires pour BacktestLab avec données OHLCV réelles."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.quant.backtest_lab import BacktestLab, _real_returns, _apply_signal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_candles(closes: list[float]) -> list[dict]:
    """Construit des bougies minimales à partir d'une série de prix de clôture."""
    return [
        {
            "symbol": "BTCUSDT",
            "timestamp": f"2024-01-{i+1:02d}T00:00:00+00:00",
            "open": c * 0.999,
            "high": c * 1.005,
            "low": c * 0.995,
            "close": c,
            "volume": 100.0,
        }
        for i, c in enumerate(closes)
    ]


_BULL_CANDLES = _make_candles([60_000, 61_000, 62_000, 63_000, 64_000])  # tendance haussière
_BEAR_CANDLES = _make_candles([64_000, 63_000, 62_000, 61_000, 60_000])  # tendance baissière
_FLAT_CANDLES = _make_candles([60_000, 60_000, 60_000, 60_000, 60_000])  # marché plat


# ---------------------------------------------------------------------------
# Tests _real_returns
# ---------------------------------------------------------------------------

def test_real_returns_bull():
    returns = _real_returns(_BULL_CANDLES)
    assert len(returns) == 4  # N-1 retours pour N bougies
    assert all(r > 0 for r in returns)


def test_real_returns_bear():
    returns = _real_returns(_BEAR_CANDLES)
    assert all(r < 0 for r in returns)


def test_real_returns_flat():
    returns = _real_returns(_FLAT_CANDLES)
    assert all(r == 0.0 for r in returns)


def test_real_returns_valeur():
    # 60000 → 61000 = +1/60 ≈ 0.01667
    r = _real_returns(_make_candles([60_000, 61_000]))[0]
    assert abs(r - (1_000 / 60_000)) < 1e-9


# ---------------------------------------------------------------------------
# Tests _apply_signal
# ---------------------------------------------------------------------------

def test_apply_signal_trend_suit_direction():
    """Stratégie trend-following : retours conservés si au-dessus du seuil."""
    strategy = {"entry_indicator": "EMA", "threshold": 0.5}  # seuil 0.005%
    returns = [0.01, -0.01, 0.0001]  # le dernier est sous le seuil
    signals = _apply_signal(returns, strategy)
    assert signals[0] == pytest.approx(0.01)
    assert signals[1] == pytest.approx(-0.01)
    assert signals[2] == pytest.approx(0.0)  # filtré


def test_apply_signal_mean_reversion_inverse():
    """Stratégie mean-reversion : retours extrêmes inversés."""
    strategy = {"entry_indicator": "RSI", "threshold": 0.5}
    returns = [0.01, -0.01, 0.0001]
    signals = _apply_signal(returns, strategy)
    assert signals[0] == pytest.approx(-0.01)   # inversé
    assert signals[1] == pytest.approx(0.01)    # inversé
    assert signals[2] == pytest.approx(0.0001)  # sous le seuil, conservé


# ---------------------------------------------------------------------------
# Tests BacktestLab
# ---------------------------------------------------------------------------

def test_backtest_avec_vraies_donnees_retourne_metriques():
    lab = BacktestLab()
    strategy = {"entry_indicator": "EMA", "period": 20, "threshold": 0.3, "timeframe": "1h"}
    result = lab.run_backtest(strategy, _BULL_CANDLES)

    assert "pnl" in result
    assert "sharpe" in result
    assert "drawdown" in result
    assert "win_rate" in result
    assert isinstance(result["sharpe"], float)
    assert 0.0 <= result["drawdown"] <= 1.0
    assert 0.0 <= result["win_rate"] <= 1.0


def test_backtest_bull_market_pnl_positif_trend_following():
    """Sur un marché haussier, une stratégie trend-following doit avoir un PnL positif."""
    lab = BacktestLab()
    candles = _make_candles([60_000, 61_000, 62_000, 63_000, 64_000, 65_000, 66_000])
    strategy = {"entry_indicator": "EMA", "period": 20, "threshold": 0.1, "timeframe": "1h"}
    result = lab.run_backtest(strategy, candles)
    assert result["pnl"] > 0


def test_backtest_bear_market_mean_reversion_pnl_positif():
    """Sur un marché baissier, une stratégie mean-reversion doit avoir un PnL positif."""
    lab = BacktestLab()
    candles = _make_candles([66_000, 65_000, 64_000, 63_000, 62_000, 61_000, 60_000])
    strategy = {"entry_indicator": "RSI", "period": 14, "threshold": 0.1, "timeframe": "1h"}
    result = lab.run_backtest(strategy, candles)
    assert result["pnl"] > 0


def test_backtest_strategies_differentes_donnent_resultats_differents():
    """Deux stratégies distinctes sur les mêmes données doivent donner des résultats différents."""
    lab = BacktestLab()
    candles = _make_candles([60_000, 61_500, 59_000, 63_000, 61_000, 64_000, 62_000])
    s1 = {"entry_indicator": "EMA", "period": 10, "threshold": 0.5, "timeframe": "1h"}
    s2 = {"entry_indicator": "RSI", "period": 14, "threshold": 0.5, "timeframe": "1h"}
    r1 = lab.run_backtest(s1, candles)
    r2 = lab.run_backtest(s2, candles)
    # Au moins une métrique doit différer
    assert r1["pnl"] != r2["pnl"] or r1["sharpe"] != r2["sharpe"]


def test_backtest_fallback_synthétique_si_une_seule_bougie():
    """Avec une seule bougie, le fallback synthétique est utilisé sans erreur."""
    lab = BacktestLab()
    strategy = {"entry_indicator": "EMA", "period": 20, "threshold": 0.5, "timeframe": "1h"}
    single_candle = _make_candles([60_000])
    result = lab.run_backtest(strategy, single_candle)
    assert "sharpe" in result
    assert "pnl" in result


def test_backtest_fallback_synthétique_si_liste_vide():
    """Avec une liste vide, le fallback synthétique est utilisé sans erreur."""
    lab = BacktestLab()
    strategy = {"entry_indicator": "EMA", "period": 20, "threshold": 0.5, "timeframe": "1h"}
    result = lab.run_backtest(strategy, [])
    assert "sharpe" in result


def test_backtest_drawdown_toujours_positif():
    """Le drawdown est toujours entre 0 et 1."""
    lab = BacktestLab()
    for candles in [_BULL_CANDLES, _BEAR_CANDLES, _FLAT_CANDLES]:
        strategy = {"entry_indicator": "EMA", "period": 14, "threshold": 0.5, "timeframe": "1h"}
        result = lab.run_backtest(strategy, candles)
        assert 0.0 <= result["drawdown"] <= 1.0, f"drawdown invalide : {result['drawdown']}"


# ---------------------------------------------------------------------------
# Test intégration : fetch_history → BacktestLab
# ---------------------------------------------------------------------------

def test_fetch_history_puis_backtest(monkeypatch):
    """Simule un fetch_history complet → backtest."""
    from unittest.mock import MagicMock
    from agents.market.market_scanner import MarketScanner

    scanner = MarketScanner(symbols=["BTCUSDT"])

    closes = [60_000 + i * 100 for i in range(200)]
    fake_ohlcv = [[i * 3_600_000, c * 0.999, c * 1.005, c * 0.995, c, 500.0]
                  for i, c in enumerate(closes)]

    exchange = MagicMock()
    exchange.fetch_ohlcv.return_value = fake_ohlcv
    scanner._exchange = exchange

    history = scanner.fetch_history("BTCUSDT", limit=200)
    assert len(history) == 200

    lab = BacktestLab()
    strategy = {"entry_indicator": "EMA", "period": 20, "threshold": 0.1, "timeframe": "1h"}
    result = lab.run_backtest(strategy, history)

    assert result["pnl"] > 0        # tendance haussière
    assert result["sharpe"] > 0
    assert result["drawdown"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
