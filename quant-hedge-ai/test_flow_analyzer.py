"""Tests for Liquidity Flow Map analyzer."""

import pytest

from liquidity_map.flow_analyzer import (
    LiquidityFlowMap,
    FlowReport,
    SectorFlow,
    _classify_sector,
)


# --- Fixtures ---

SAMPLE_CANDLES = [
    {"symbol": "BTCUSDT", "close": 50000, "open": 49500, "volume": 100},
    {"symbol": "ETHUSDT", "close": 3000, "open": 2950, "volume": 200},
    {"symbol": "SOLUSDT", "close": 150, "open": 145, "volume": 1000},
    {"symbol": "DOGEUSDT", "close": 0.15, "open": 0.14, "volume": 5000000},
]

SAMPLE_WHALE_ALERTS = [
    "WHALE_BUY: 2.4M USD on BTC",
    "OUTFLOW_FROM_EXCHANGE: 1.5M USD ETH",
    "WHALE_TRANSFER: 0.5M USD on DOGEUSDT",
]


@pytest.fixture
def flow_map():
    return LiquidityFlowMap(opportunity_threshold=40.0)


# --- Sector classification tests ---


class TestSectorClassification:
    def test_known_symbols(self):
        assert _classify_sector("BTCUSDT") == "BTC"
        assert _classify_sector("ETHUSDT") == "ETH_L1"
        assert _classify_sector("SOLUSDT") == "SOL_L1"
        assert _classify_sector("DOGEUSDT") == "MEMECOINS"
        assert _classify_sector("UNIUSDT") == "DEFI"
        assert _classify_sector("FETUSDT") == "AI_TOKENS"

    def test_case_insensitive(self):
        assert _classify_sector("btcusdt") == "BTC"
        assert _classify_sector("BtCuSdT") == "BTC"

    def test_unknown_symbol(self):
        assert _classify_sector("XYZUSDT") == "ALTCOINS"
        assert _classify_sector("") == "ALTCOINS"


# --- SectorFlow tests ---


class TestSectorFlow:
    def test_total_flow(self):
        sf = SectorFlow(sector="BTC", volume_usd=1000, whale_flow_usd=500)
        assert sf.total_flow == 1500

    def test_opportunity_score_no_whale(self):
        sf = SectorFlow(sector="BTC", volume_usd=1000, whale_flow_usd=0)
        assert sf.opportunity_score >= 0

    def test_opportunity_score_high_whale(self):
        sf = SectorFlow(
            sector="BTC",
            volume_usd=1_000_000,
            whale_flow_usd=50_000_000,
            token_count=3,
            momentum_score=0.5,
        )
        score = sf.opportunity_score
        assert 0 <= score <= 100

    def test_opportunity_score_max_100(self):
        sf = SectorFlow(
            sector="MAX",
            volume_usd=999_999_999,
            whale_flow_usd=999_999_999,
            token_count=100,
            momentum_score=1.0,
        )
        assert sf.opportunity_score == 100.0


# --- Whale amount parser tests ---


class TestWhaleParser:
    def test_simple_m_usd(self):
        assert LiquidityFlowMap._parse_whale_amount("2.4M USD outflow") == 2_400_000

    def test_simple_usd_no_m(self):
        assert LiquidityFlowMap._parse_whale_amount("100 USD small tx") == 100

    def test_large_m_usd(self):
        assert LiquidityFlowMap._parse_whale_amount("5M USD whale") == 5_000_000

    def test_comma_number(self):
        assert LiquidityFlowMap._parse_whale_amount("transferred 1,500 USD") == 1_500

    def test_no_false_m_from_medium(self):
        """'MEDIUM' should NOT be treated as 'M USD'."""
        assert LiquidityFlowMap._parse_whale_amount("MEDIUM risk 200 USD") == 200

    def test_no_false_m_from_momentum(self):
        """'momentum' should NOT be treated as 'M USD'."""
        assert LiquidityFlowMap._parse_whale_amount("momentum 50 USD trade") == 50

    def test_no_amount(self):
        assert LiquidityFlowMap._parse_whale_amount("no amount here") == 0

    def test_empty_string(self):
        assert LiquidityFlowMap._parse_whale_amount("") == 0

    def test_real_whale_alert_format(self):
        assert LiquidityFlowMap._parse_whale_amount("OUTFLOW_FROM_EXCHANGE: 2.4M USD") == 2_400_000

    def test_whale_transfer_format(self):
        assert LiquidityFlowMap._parse_whale_amount("WHALE_TRANSFER: 4.4M USD on BTCUSDT") == 4_400_000


# --- FlowReport tests ---


class TestFlowReport:
    def test_default(self):
        r = FlowReport()
        assert r.cycle == 0
        assert r.top_sector == "none"
        assert r.sector_flows == []
        assert r.opportunities == []

    def test_as_dict_keys(self):
        r = FlowReport(cycle=1, top_sector="BTC")
        d = r.as_dict()
        expected_keys = {
            "cycle", "top_sector", "top_sector_score", "total_volume_usd",
            "total_whale_flow_usd", "parsed_whale_alerts_usd", "whale_unmapped_usd",
            "whale_mapping_coverage", "whale_consistency_gap_usd", "capital_concentration",
            "sectors_active", "opportunities", "regime", "sector_details",
            "multi_sector_opportunities",
        }
        assert set(d.keys()) == expected_keys

    def test_as_dict_sector_details(self):
        r = FlowReport(
            sector_flows=[SectorFlow(sector="BTC", volume_usd=1000, whale_flow_usd=500)]
        )
        d = r.as_dict()
        assert len(d["sector_details"]) == 1
        assert d["sector_details"][0]["sector"] == "BTC"


# --- LiquidityFlowMap.analyze tests ---


class TestFlowMapAnalyze:
    def test_basic_analysis(self, flow_map):
        r = flow_map.analyze(SAMPLE_CANDLES, SAMPLE_WHALE_ALERTS, "bull_trend", cycle=1)
        assert isinstance(r, FlowReport)
        assert r.cycle == 1
        assert r.regime == "bull_trend"
        assert len(r.sector_flows) > 0
        assert r.total_volume_usd > 0

    def test_empty_candles(self, flow_map):
        r = flow_map.analyze([], [], "test")
        assert r.top_sector == "none"
        assert len(r.sector_flows) == 0
        assert r.capital_concentration == 0.0

    def test_empty_whale_alerts(self, flow_map):
        r = flow_map.analyze(SAMPLE_CANDLES, [], "test")
        assert r.total_whale_flow_usd == 0

    def test_whale_flow_attribution(self, flow_map):
        candles = [{"symbol": "BTCUSDT", "close": 50000, "open": 49000, "volume": 100}]
        alerts = ["WHALE_BUY 2.4M USD on BTC"]
        r = flow_map.analyze(candles, alerts, "test")
        btc_flow = next((sf for sf in r.sector_flows if sf.sector == "BTC"), None)
        assert btc_flow is not None
        assert btc_flow.whale_flow_usd == 2_400_000

    def test_concentration_single_sector(self, flow_map):
        """Single sector = concentration 1.0 (max)."""
        candles = [{"symbol": "BTCUSDT", "close": 50000, "open": 49000, "volume": 100}]
        r = flow_map.analyze(candles, [], "test")
        assert r.capital_concentration == 1.0

    def test_concentration_two_equal_sectors(self, flow_map):
        """Two equal sectors = concentration 0.5."""
        candles = [
            {"symbol": "BTCUSDT", "close": 100, "open": 100, "volume": 100},
            {"symbol": "ETHUSDT", "close": 100, "open": 100, "volume": 100},
        ]
        r = flow_map.analyze(candles, [], "test")
        assert abs(r.capital_concentration - 0.5) < 0.01

    def test_open_zero_no_crash(self, flow_map):
        """open=0 should not cause division by zero."""
        candles = [{"symbol": "ETHUSDT", "close": 3000, "open": 0, "volume": 50}]
        r = flow_map.analyze(candles, [], "test")
        assert len(r.sector_flows) == 1

    def test_sectors_sorted_by_opportunity(self, flow_map):
        r = flow_map.analyze(SAMPLE_CANDLES, SAMPLE_WHALE_ALERTS, "test")
        scores = [sf.opportunity_score for sf in r.sector_flows]
        assert scores == sorted(scores, reverse=True)

    def test_history_builds(self, flow_map):
        for i in range(5):
            flow_map.analyze(SAMPLE_CANDLES, [], "test", cycle=i)
        assert len(flow_map._history) == 5

    def test_history_trimming(self, flow_map):
        for i in range(210):
            flow_map.analyze(
                [{"symbol": "BTCUSDT", "close": 100, "open": 99, "volume": 1}],
                [], "test", cycle=i,
            )
        assert len(flow_map._history) <= 112  # trimmed from 201+ to ~100

    def test_opportunities_above_threshold(self):
        fm = LiquidityFlowMap(opportunity_threshold=5.0)  # low threshold
        candles = [
            {"symbol": "BTCUSDT", "close": 50000, "open": 49000, "volume": 100},
        ]
        alerts = ["WHALE_BUY 10M USD on BTC"]
        r = fm.analyze(candles, alerts, "test")
        assert len(r.opportunities) > 0

    def test_opportunities_below_threshold(self):
        fm = LiquidityFlowMap(opportunity_threshold=99.0)  # very high
        candles = [{"symbol": "BTCUSDT", "close": 100, "open": 100, "volume": 1}]
        r = fm.analyze(candles, [], "test")
        assert len(r.opportunities) == 0


# --- Render tests ---


class TestFlowMapRender:
    def test_render_basic(self, flow_map):
        r = flow_map.analyze(SAMPLE_CANDLES, SAMPLE_WHALE_ALERTS, "bull_trend", cycle=1)
        text = flow_map.render(r)
        assert "LIQUIDITY FLOW MAP" in text
        assert "Concentration" in text
        assert "Sectors Active" in text

    def test_render_empty(self, flow_map):
        r = FlowReport()
        text = flow_map.render(r)
        assert "LIQUIDITY FLOW MAP" in text

    def test_render_with_opportunities(self):
        fm = LiquidityFlowMap(opportunity_threshold=5.0)
        candles = [{"symbol": "BTCUSDT", "close": 50000, "open": 49000, "volume": 100}]
        alerts = ["WHALE_BUY 10M USD on BTC"]
        r = fm.analyze(candles, alerts, "test")
        text = fm.render(r)
        if r.opportunities:
            assert "Opportunities" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
