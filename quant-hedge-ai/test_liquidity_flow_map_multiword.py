from liquidity_map.flow_analyzer import LiquidityFlowMap

def test_multiword_alert_mapping():
    fm = LiquidityFlowMap()
    candles = []
    alerts = [
        "1M USD EXCHANGE STABLECOIN outflow",  # doit mapper STABLECOINS
        "2M USD DEFI ALTCOIN transfer",        # doit mapper DEFI (priorité DEFI)
        "3M USD AI NFT sale",                  # doit mapper AI_TOKENS (priorité AI)
    ]
    report = fm.analyze(candles=candles, whale_alerts=alerts, regime="test", cycle=1)
    mapping = {
        "STABLECOINS": 1_000_000,
        "DEFI": 2_000_000,
        "AI_TOKENS": 3_000_000,
    }
    for sector, expected in mapping.items():
        total = sum(sf.whale_flow_usd for sf in report.sector_flows if sf.sector == sector)
        assert total == expected, f"Sector {sector} should have total whale flow {expected}, got {total}"
