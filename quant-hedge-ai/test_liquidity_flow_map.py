from __future__ import annotations

from liquidity_map.flow_analyzer import LiquidityFlowMap


def test_parse_whale_amount_is_not_confused_by_words_with_m() -> None:
    fm = LiquidityFlowMap()
    assert fm._parse_whale_amount("100 USD small tx") == 100.0
    assert fm._parse_whale_amount("MEDIUM risk 200 USD") == 200.0
    assert fm._parse_whale_amount("momentum 50 USD trade") == 50.0


def test_parse_whale_amount_supports_common_units() -> None:
    fm = LiquidityFlowMap()
    assert fm._parse_whale_amount("2.4M USD outflow") == 2_400_000.0
    assert fm._parse_whale_amount("3.5B USD transfer") == 3_500_000_000.0
    assert fm._parse_whale_amount("250K USD move") == 250_000.0
    assert fm._parse_whale_amount("transferred 1,500 USD") == 1_500.0


def test_flow_report_exposes_whale_consistency_metrics() -> None:
    fm = LiquidityFlowMap()
    candles = [
        {"symbol": "BTCUSDT", "open": 100.0, "close": 101.0, "volume": 10.0},
        {"symbol": "ETHUSDT", "open": 100.0, "close": 99.0, "volume": 12.0},
    ]
    whale_alerts = [
        "WHALE_TRANSFER: 4.4M USD on ETHUSDT",
        "OUTFLOW_FROM_EXCHANGE: 2.4M USD",
    ]
    report = fm.analyze(candles=candles, whale_alerts=whale_alerts, regime="test", cycle=1)
    assert report.parsed_whale_alerts_usd == 6_800_000.0
    assert report.total_whale_flow_usd == 6_800_000.0
    assert report.whale_unmapped_usd == 2_400_000.0
    assert report.whale_consistency_gap_usd == 0.0
    assert 0.0 <= report.whale_mapping_coverage <= 1.0
    # Check fallback mapping to STABLECOINS sector (keyword EXCHANGE)
    found_stable = any(sf.sector == "STABLECOINS" and sf.whale_flow_usd == 2_400_000.0 for sf in report.sector_flows)
    assert found_stable, "Unmapped whale should be mapped to STABLECOINS sector via keyword EXCHANGE"

def test_sector_inference_mapping() -> None:
    fm = LiquidityFlowMap()
    candles = [{"symbol": "BTCUSDT", "open": 100.0, "close": 101.0, "volume": 10.0}]
    alerts = [
        "100M USD exchange outflow",  # STABLECOINS
        "200M USD altcoin transfer",  # ALTCOINS
        "300M USD defi whale",        # DEFI
        "400M USD meme buy",          # MEMECOINS
        "500M USD ai pump",           # AI_TOKENS
        "600M USD nft sale",          # NFTS
        "700M USD L1 bridge",         # ALT_L1
        "800M USD stablecoin mint",   # STABLECOINS
        "900M USD ETH whale",         # ETH_L1
        "1B USD SOL whale",           # SOL_L1
        "2B USD BTC whale",           # BTC
    ]
    report = fm.analyze(candles=candles, whale_alerts=alerts, regime="test", cycle=1)
    mapping = {
        "STABLECOINS": 100_000_000 + 800_000_000,
        "ALTCOINS": 200_000_000,
        "DEFI": 300_000_000,
        "MEMECOINS": 400_000_000,
        "AI_TOKENS": 500_000_000,
        "NFTS": 600_000_000,
        "ALT_L1": 700_000_000,
        "ETH_L1": 900_000_000,
        "SOL_L1": 1_000_000_000,
        "BTC": 2_000_000_000,
    }
    for sector, expected in mapping.items():
        total = sum(sf.whale_flow_usd for sf in report.sector_flows if sf.sector == sector)
        assert total == expected, f"Sector {sector} should have total whale flow {expected}, got {total}"
