from dashboard.director_dashboard import DirectorDashboard

def test_sector_coverage_report():
    dashboard = DirectorDashboard()
    # Simule un snapshot avec 3 secteurs dont 2 mappés
    flow_summary = {
        'sector_details': [
            {'sector': 'DEFI', 'whale_flow_usd': 1000000},
            {'sector': 'AI_TOKENS', 'whale_flow_usd': 500000},
            {'sector': 'ALTCOINS', 'whale_flow_usd': 0},
        ],
        'top_sector': 'DEFI',
        'top_sector_score': 80,
        'total_volume_usd': 0,
        'total_whale_flow_usd': 1500000,
        'parsed_whale_alerts_usd': 1500000,
        'whale_unmapped_usd': 0,
        'whale_mapping_coverage': 1.0,
        'whale_consistency_gap_usd': 0,
        'capital_concentration': 0.5,
        'sectors_active': 3,
        'opportunities': 2,
    }
    snapshot = dashboard.update(
        cycle=1,
        flow_summary=flow_summary
    )
    report = dashboard.render(snapshot)
    assert "66.7%" in report
    assert "Couverture sectorielle : [" in report
    assert "Secteurs mappés : DEFI, AI_TOKENS" in report
    assert "Secteurs non mappés : ALTCOINS" in report
