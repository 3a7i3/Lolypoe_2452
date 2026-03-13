"""Tests for the AI Market Radar module."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from market_radar.token_scanner import TokenScanner, TokenInfo
from market_radar.whale_tracker import WhaleTracker
from market_radar.social_scanner import SocialScanner
from market_radar.anomaly_detector import AnomalyDetector, MarketAnomaly
from market_radar.radar_core import MarketRadar


# ====================================================================
# TokenScanner tests
# ====================================================================

def test_token_scanner_scan():
    scanner = TokenScanner()
    tokens = scanner.scan()
    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert all(isinstance(t, TokenInfo) for t in tokens)
    print(f"  [PASS] TokenScanner.scan() → {len(tokens)} tokens")


def test_token_scanner_filter():
    scanner = TokenScanner(min_liquidity_usd=5_000, min_volume_usd=1_000, max_token_age_s=3600)
    all_tokens = [
        TokenInfo(symbol="GOOD", name="Good", platform="test", liquidity_usd=10_000, volume_24h_usd=5_000, age_seconds=300),
        TokenInfo(symbol="LOW_LIQ", name="LowLiq", platform="test", liquidity_usd=100, volume_24h_usd=5_000, age_seconds=300),
        TokenInfo(symbol="LOW_VOL", name="LowVol", platform="test", liquidity_usd=10_000, volume_24h_usd=100, age_seconds=300),
        TokenInfo(symbol="OLD", name="Old", platform="test", liquidity_usd=10_000, volume_24h_usd=5_000, age_seconds=99_999),
    ]
    filtered = scanner.filter_tokens(all_tokens)
    assert len(filtered) == 1
    assert filtered[0].symbol == "GOOD"
    print("  [PASS] TokenScanner.filter_tokens() filters correctly")


def test_token_scorer():
    scanner = TokenScanner()

    # High-quality token
    good = TokenInfo(
        symbol="ALPHA", name="Alpha", platform="test",
        liquidity_usd=100_000, volume_24h_usd=200_000,
        holder_count=1000, whale_holders=4, age_seconds=60,
    )
    score = scanner.score_token(good)
    assert score >= 8.0, f"Expected high score, got {score}"

    # Low-quality token
    bad = TokenInfo(
        symbol="JUNK", name="Junk", platform="test",
        liquidity_usd=100, volume_24h_usd=50,
        holder_count=3, whale_holders=0, age_seconds=50_000,
    )
    score_bad = scanner.score_token(bad)
    assert score_bad <= 2.0, f"Expected low score, got {score_bad}"

    print(f"  [PASS] TokenScanner.score_token() → good={good.score}, bad={bad.score}")


# ====================================================================
# WhaleTracker tests
# ====================================================================

def test_whale_tracker_scan():
    tracker = WhaleTracker(threshold_usd=500_000)
    report = tracker.scan(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    assert report is not None
    assert isinstance(report.smart_money_flow, str)
    assert report.smart_money_flow in ("bullish", "bearish", "neutral")
    print(f"  [PASS] WhaleTracker.scan() → flow={report.smart_money_flow}, activities={len(report.activities)}")


def test_whale_accumulation_detection():
    tracker = WhaleTracker()
    result = tracker.detect_accumulation("NONEXISTENT")
    assert result["pattern"] == "no_data"
    print("  [PASS] WhaleTracker.detect_accumulation() handles empty data")


def test_whale_alerts_format():
    tracker = WhaleTracker(threshold_usd=100_000)
    report = tracker.scan(["BTCUSDT", "ETHUSDT"])
    alerts = tracker.get_alerts(report)
    assert isinstance(alerts, list)
    assert all(isinstance(a, str) for a in alerts)
    print(f"  [PASS] WhaleTracker.get_alerts() → {len(alerts)} alerts")


# ====================================================================
# SocialScanner tests
# ====================================================================

def test_social_scanner():
    scanner = SocialScanner(min_mentions=10, sentiment_threshold=0.3)
    report = scanner.scan(["BTCUSDT", "MEMEAI"])
    assert report is not None
    assert isinstance(report.overall_sentiment, float)
    assert -1.0 <= report.overall_sentiment <= 1.0
    print(f"  [PASS] SocialScanner.scan() → sentiment={report.overall_sentiment:.2f}, trending={report.trending_tokens}")


def test_social_viral_detection():
    scanner = SocialScanner()
    result = scanner.detect_viral("NEWTOKEN")
    assert "viral" in result
    assert "acceleration" in result
    print(f"  [PASS] SocialScanner.detect_viral() → viral={result['viral']}")


# ====================================================================
# AnomalyDetector tests
# ====================================================================

def test_anomaly_volume_spike():
    detector = AnomalyDetector(volume_spike_factor=3.0)
    candles = [
        {"symbol": "BTCUSDT", "open": 100, "close": 101, "high": 102, "low": 99, "volume": 1000},
        {"symbol": "ETHUSDT", "open": 50, "close": 51, "high": 52, "low": 49, "volume": 1000},
        {"symbol": "ADAUSDT", "open": 1, "close": 1.01, "high": 1.02, "low": 0.99, "volume": 1000},
        {"symbol": "DOTUSDT", "open": 20, "close": 20.1, "high": 20.5, "low": 19.8, "volume": 1000},
        {"symbol": "SPIKE", "open": 10, "close": 11, "high": 12, "low": 9, "volume": 100_000},
    ]
    features = {"realized_volatility": 0.02, "momentum": 0.01}
    report = detector.detect(candles, features)
    volume_anomalies = [a for a in report.anomalies if a.anomaly_type == "volume_spike"]
    assert len(volume_anomalies) >= 1
    print(f"  [PASS] AnomalyDetector volume spike → {len(volume_anomalies)} detected")


def test_anomaly_price_crash():
    detector = AnomalyDetector(price_move_threshold=0.10)
    candles = [
        {"symbol": "CRASH", "open": 100, "close": 70, "high": 100, "low": 65, "volume": 5000},
    ]
    features = {"realized_volatility": 0.02, "momentum": -0.05}
    report = detector.detect(candles, features)
    crashes = [a for a in report.anomalies if a.anomaly_type == "price_crash"]
    assert len(crashes) == 1
    assert crashes[0].severity in ("medium", "high", "critical")
    print(f"  [PASS] AnomalyDetector price crash → severity={crashes[0].severity}")


def test_anomaly_empty_data():
    detector = AnomalyDetector()
    report = detector.detect([], {})
    assert report.risk_level == "normal"
    assert len(report.anomalies) == 0
    print("  [PASS] AnomalyDetector handles empty data")


# ====================================================================
# MarketRadar (integration) tests
# ====================================================================

def test_radar_full_sweep():
    radar = MarketRadar(min_opportunity_score=0)
    candles = [
        {"symbol": "BTCUSDT", "open": 50000, "close": 51000, "high": 51500, "low": 49500, "volume": 100_000},
        {"symbol": "ETHUSDT", "open": 3000, "close": 3050, "high": 3100, "low": 2950, "volume": 50_000},
        {"symbol": "SOLUSDT", "open": 150, "close": 155, "high": 160, "low": 145, "volume": 30_000},
    ]
    features = {"realized_volatility": 0.03, "momentum": 0.02, "volume_trend": 1.1}

    report = radar.sweep(candles, features)
    assert report is not None
    assert report.tokens_scanned > 0
    assert report.whale_report is not None
    assert report.social_report is not None
    assert report.anomaly_report is not None
    assert isinstance(report.risk_level, str)

    summary = report.as_dict()
    assert "opportunities_count" in summary
    assert "whale_flow" in summary
    assert "social_sentiment" in summary

    print(f"  [PASS] MarketRadar.sweep() → {len(report.opportunities)} opportunities, risk={report.risk_level}")
    print(f"         Top 3: {[(o.symbol, round(o.score, 1)) for o in report.top(3)]}")


def test_radar_report_dict():
    radar = MarketRadar(min_opportunity_score=0)
    candles = [{"symbol": "BTCUSDT", "open": 100, "close": 102, "high": 105, "low": 98, "volume": 5000}]
    features = {"realized_volatility": 0.02, "momentum": 0.01}
    report = radar.sweep(candles, features)
    d = report.as_dict()
    assert isinstance(d, dict)
    required_keys = {"opportunities_count", "whale_flow", "social_sentiment", "risk_level", "anomaly_count"}
    assert required_keys.issubset(d.keys())
    print(f"  [PASS] RadarReport.as_dict() → {d}")


# ====================================================================
# Run all tests
# ====================================================================

if __name__ == "__main__":
    print("\n🔬 AI Market Radar — Test Suite\n")

    tests = [
        ("TokenScanner.scan", test_token_scanner_scan),
        ("TokenScanner.filter", test_token_scanner_filter),
        ("TokenScanner.score", test_token_scorer),
        ("WhaleTracker.scan", test_whale_tracker_scan),
        ("WhaleTracker.accumulation", test_whale_accumulation_detection),
        ("WhaleTracker.alerts", test_whale_alerts_format),
        ("SocialScanner.scan", test_social_scanner),
        ("SocialScanner.viral", test_social_viral_detection),
        ("AnomalyDetector.volume", test_anomaly_volume_spike),
        ("AnomalyDetector.crash", test_anomaly_price_crash),
        ("AnomalyDetector.empty", test_anomaly_empty_data),
        ("MarketRadar.sweep", test_radar_full_sweep),
        ("MarketRadar.report", test_radar_report_dict),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
