from dashboard.director_dashboard import DirectorDashboard

def test_sector_coverage_full():
    dashboard = DirectorDashboard()
    # Simule un snapshot avec 5 secteurs dont 5 mappés
    flow_summary = {
        'sector_details': [
            {'sector': 'DEFI', 'whale_flow_usd': 1000000},
            {'sector': 'AI_TOKENS', 'whale_flow_usd': 500000},
            {'sector': 'ALTCOINS', 'whale_flow_usd': 200000},
            {'sector': 'NFTS', 'whale_flow_usd': 300000},
            {'sector': 'MEMECOINS', 'whale_flow_usd': 100000},
        ],
        'top_sector': 'DEFI',
        'top_sector_score': 80,
        'total_volume_usd': 0,
        'total_whale_flow_usd': 2100000,
        'parsed_whale_alerts_usd': 2100000,
        'whale_unmapped_usd': 0,
        'whale_mapping_coverage': 1.0,
        'whale_consistency_gap_usd': 0,
        'capital_concentration': 0.5,
        'sectors_active': 5,
        'opportunities': 3,
    }
    snapshot = dashboard.update(
        cycle=1,
        flow_summary=flow_summary
    )
    report = dashboard.render(snapshot)
    assert "100.0%" in report
    assert "Secteurs non mappés : aucun" in report
    assert "Secteurs mappés : DEFI, AI_TOKENS, ALTCOINS, NFTS, MEMECOINS" in report
