"""Tests — Option R : SentimentFeed Fear & Greed Index."""
from __future__ import annotations

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))

from agents.research.sentiment_feed import SentimentFeed, _score_to_label


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _fng_response(score: int, previous: int | None = None) -> bytes:
    data = [{"value": str(score), "value_classification": "Fear", "timestamp": "1700000000"}]
    if previous is not None:
        data.append({"value": str(previous), "value_classification": "Greed", "timestamp": "1699913600"})
    return json.dumps({"name": "Fear and Greed Index", "data": data}).encode()


# ---------------------------------------------------------------------------
# _score_to_label
# ---------------------------------------------------------------------------

class TestScoreToLabel:
    @pytest.mark.parametrize("score,expected_label,expected_trend", [
        (0, "Extreme Fear", "bearish"),
        (10, "Extreme Fear", "bearish"),
        (24, "Extreme Fear", "bearish"),
        (25, "Fear", "bearish"),
        (44, "Fear", "bearish"),
        (45, "Neutral", "neutral"),
        (50, "Neutral", "neutral"),
        (55, "Neutral", "neutral"),
        (56, "Greed", "bullish"),
        (74, "Greed", "bullish"),
        (75, "Extreme Greed", "bullish"),
        (100, "Extreme Greed", "bullish"),
    ])
    def test_label_and_trend(self, score, expected_label, expected_trend):
        label, trend = _score_to_label(score)
        assert label == expected_label
        assert trend == expected_trend


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

class TestSentimentFeedInit:
    def test_defaults(self):
        sf = SentimentFeed()
        assert sf.cache_ttl == 300.0
        assert sf.fallback_score == 50
        assert sf.timeout > 0

    def test_custom_params(self):
        sf = SentimentFeed(cache_ttl=60.0, fallback_score=30, timeout=3.0)
        assert sf.cache_ttl == 60.0
        assert sf.fallback_score == 30
        assert sf.timeout == 3.0

    def test_invalid_fallback_score_too_high(self):
        with pytest.raises(ValueError, match="fallback_score"):
            SentimentFeed(fallback_score=101)

    def test_invalid_fallback_score_negative(self):
        with pytest.raises(ValueError, match="fallback_score"):
            SentimentFeed(fallback_score=-1)

    def test_invalid_cache_ttl_negative(self):
        with pytest.raises(ValueError, match="cache_ttl"):
            SentimentFeed(cache_ttl=-1.0)


# ---------------------------------------------------------------------------
# Fetch live (mocked)
# ---------------------------------------------------------------------------

class TestFetchLive:
    def _make_mock_response(self, body: bytes):
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_fetch_returns_score_and_label(self):
        sf = SentimentFeed(cache_ttl=0)
        mock_resp = self._make_mock_response(_fng_response(65))
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = sf.fetch()
        assert result["score"] == 65
        assert result["label"] == "Greed"
        assert result["trend"] == "bullish"
        assert result["source"] == "fng"

    def test_fetch_extreme_fear(self):
        sf = SentimentFeed(cache_ttl=0)
        mock_resp = self._make_mock_response(_fng_response(15))
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = sf.fetch()
        assert result["label"] == "Extreme Fear"
        assert result["trend"] == "bearish"

    def test_fetch_with_previous_score(self):
        sf = SentimentFeed(cache_ttl=0)
        mock_resp = self._make_mock_response(_fng_response(55, previous=48))
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = sf.fetch()
        assert result["previous_score"] == 48

    def test_fetch_no_previous_score(self):
        sf = SentimentFeed(cache_ttl=0)
        mock_resp = self._make_mock_response(_fng_response(55))
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = sf.fetch()
        assert result["previous_score"] is None


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

class TestFallback:
    def test_fallback_on_url_error(self):
        sf = SentimentFeed(cache_ttl=0, fallback_score=50)
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = sf.fetch()
        assert result["score"] == 50
        assert result["source"] == "fallback"
        assert result["label"] == "Neutral"

    def test_fallback_on_json_error(self):
        sf = SentimentFeed(cache_ttl=0, fallback_score=30)
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json {"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = sf.fetch()
        assert result["source"] == "fallback"
        assert result["score"] == 30

    def test_fallback_empty_data(self):
        sf = SentimentFeed(cache_ttl=0, fallback_score=40)
        empty = json.dumps({"data": []}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = empty
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = sf.fetch()
        assert result["source"] == "fallback"
        assert result["score"] == 40

    def test_fallback_extreme_fear(self):
        sf = SentimentFeed(cache_ttl=0, fallback_score=10)
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            result = sf.fetch()
        assert result["label"] == "Extreme Fear"
        assert result["trend"] == "bearish"
        assert result["previous_score"] is None


# ---------------------------------------------------------------------------
# Cache TTL
# ---------------------------------------------------------------------------

class TestCache:
    def _make_mock_response(self, body: bytes):
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_cache_hit_on_second_call(self):
        sf = SentimentFeed(cache_ttl=300.0)
        mock_resp = self._make_mock_response(_fng_response(70))
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            sf.fetch()
            sf.fetch()
        assert mock_open.call_count == 1  # deuxième appel depuis le cache

    def test_cache_bypass_when_ttl_zero(self):
        sf = SentimentFeed(cache_ttl=0.0)
        mock_resp = self._make_mock_response(_fng_response(70))
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            sf.fetch()
            sf.fetch()
        assert mock_open.call_count == 2

    def test_invalidate_cache(self):
        sf = SentimentFeed(cache_ttl=999.0)
        mock_resp = self._make_mock_response(_fng_response(70))
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            sf.fetch()
            sf.invalidate_cache()
            sf.fetch()
        assert mock_open.call_count == 2


# ---------------------------------------------------------------------------
# API helper : should_trade_bullish / score
# ---------------------------------------------------------------------------

class TestHelperMethods:
    def _sf_with_score(self, score: int) -> SentimentFeed:
        sf = SentimentFeed(cache_ttl=999.0, fallback_score=score)
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            sf.fetch()  # pré-chauffe le cache avec fallback
        return sf

    def test_should_trade_bullish_neutral_is_true(self):
        sf = self._sf_with_score(50)
        assert sf.should_trade_bullish() is True

    def test_should_trade_bullish_extreme_fear_is_false(self):
        sf = self._sf_with_score(10)
        assert sf.should_trade_bullish() is False

    def test_score_helper(self):
        sf = self._sf_with_score(75)
        assert sf.score() == 75

    def test_threshold_edge_45(self):
        sf = self._sf_with_score(45)
        assert sf.should_trade_bullish() is True

    def test_threshold_edge_44(self):
        sf = self._sf_with_score(44)
        assert sf.should_trade_bullish() is False
