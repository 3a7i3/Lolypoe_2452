"""Option R — SentimentFeed : Fear & Greed Index + fallback synthétique.

Source : https://api.alternative.me/fng/ (API publique, pas de clé)
Fallback : score neutre (50) si l'API est inaccessible.

Score 0-100 :
  0-24  → Extreme Fear
  25-44 → Fear
  45-55 → Neutral
  56-74 → Greed
  75-100 → Extreme Greed

Workflow :
    feed = SentimentFeed()
    result = feed.fetch()
    # → {"score": 65, "label": "Greed", "trend": "bullish", "source": "fng"}
"""
from __future__ import annotations

import json
import logging
import time
import urllib.request
import urllib.error
from typing import Any

logger = logging.getLogger(__name__)

_FNG_URL = "https://api.alternative.me/fng/?limit=2&format=json"
_TIMEOUT = 5  # secondes

# Seuils de label
_THRESHOLDS = [
    (0, 24, "Extreme Fear", "bearish"),
    (25, 44, "Fear", "bearish"),
    (45, 55, "Neutral", "neutral"),
    (56, 74, "Greed", "bullish"),
    (75, 100, "Extreme Greed", "bullish"),
]


def _score_to_label(score: int) -> tuple[str, str]:
    """Retourne (label, trend) depuis un score 0-100."""
    for low, high, label, trend in _THRESHOLDS:
        if low <= score <= high:
            return label, trend
    return "Neutral", "neutral"


class SentimentFeed:
    """Récupère le Fear & Greed Index avec cache TTL et fallback.

    Args:
        cache_ttl:     durée de vie du cache en secondes (défaut 300).
        fallback_score: score retourné si l'API est inaccessible (défaut 50).
        timeout:       timeout HTTP en secondes.
    """

    def __init__(
        self,
        cache_ttl: float = 300.0,
        fallback_score: int = 50,
        timeout: float = float(_TIMEOUT),
    ) -> None:
        if not (0 <= fallback_score <= 100):
            raise ValueError(f"fallback_score doit être dans [0, 100], reçu: {fallback_score}")
        if cache_ttl < 0:
            raise ValueError(f"cache_ttl doit être >= 0, reçu: {cache_ttl}")

        self.cache_ttl = cache_ttl
        self.fallback_score = fallback_score
        self.timeout = timeout

        self._cache: dict[str, Any] | None = None
        self._cache_ts: float = 0.0

    # ------------------------------------------------------------------
    # API principale
    # ------------------------------------------------------------------

    def fetch(self) -> dict[str, Any]:
        """Retourne le score Fear & Greed courant.

        Returns:
            dict avec :
            - ``score`` (int 0-100)
            - ``label`` (str : "Extreme Fear" → "Extreme Greed")
            - ``trend`` (str : "bearish" | "neutral" | "bullish")
            - ``source`` (str : "fng" | "fallback")
            - ``previous_score`` (int | None) : score précédent si dispo
        """
        now = time.monotonic()
        if self._cache is not None and (now - self._cache_ts) < self.cache_ttl:
            return self._cache

        result = self._fetch_live()
        self._cache = result
        self._cache_ts = now
        return result

    def should_trade_bullish(self) -> bool:
        """Retourne True si le sentiment est neutre ou haussier (score >= 45)."""
        return self.fetch()["score"] >= 45

    def score(self) -> int:
        """Score courant (0-100)."""
        return self.fetch()["score"]

    def invalidate_cache(self) -> None:
        """Force le prochain fetch à aller chercher les données fraîches."""
        self._cache = None
        self._cache_ts = 0.0

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _fetch_live(self) -> dict[str, Any]:
        try:
            req = urllib.request.Request(
                _FNG_URL,
                headers={"User-Agent": "quant-hedge-ai/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            return self._parse(raw)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("SentimentFeed: fallback (API inaccessible: %s)", exc)
            return self._fallback()

    @staticmethod
    def _parse(raw: dict) -> dict[str, Any]:
        data = raw.get("data", [])
        if not data:
            raise ValueError("FNG API: champ 'data' vide")

        current = data[0]
        score = int(current["value"])
        label, trend = _score_to_label(score)

        previous_score: int | None = None
        if len(data) >= 2:
            try:
                previous_score = int(data[1]["value"])
            except (KeyError, ValueError):
                pass

        return {
            "score": score,
            "label": label,
            "trend": trend,
            "source": "fng",
            "previous_score": previous_score,
        }

    def _fallback(self) -> dict[str, Any]:
        label, trend = _score_to_label(self.fallback_score)
        return {
            "score": self.fallback_score,
            "label": label,
            "trend": trend,
            "source": "fallback",
            "previous_score": None,
        }
