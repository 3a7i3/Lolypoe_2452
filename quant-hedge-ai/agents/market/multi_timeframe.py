"""Option AD — Multi-Timeframe Signal Aggregator.

Ce module fournit :
- ``MultiTimeframeScanner``  : récupère des bougies OHLCV pour plusieurs timeframes
  simultanément via le ``MarketScanner`` existant.
- ``TimeframeSignal``        : signal de direction calculé sur un seul timeframe.
- ``MultiTimeframeAggregator``: combine les signaux de tous les timeframes en un
  score d'alignement et un signal composite (BUY / SELL / HOLD).

Logique de consensus
--------------------
Pour chaque timeframe, un signal est calculé comme suit :
- ``BUY``  si ``SMA_fast > SMA_slow`` ET ``close > SMA_fast``  (trend haussière)
- ``SELL`` si ``SMA_fast < SMA_slow`` ET ``close < SMA_fast``  (trend baissière)
- ``HOLD`` sinon (régime incertain)

Le score d'alignement est la fraction de timeframes qui partagent la direction
majoritaire (entre BUY et SELL, HOLD est neutre).

  alignment_score = (nombre de TF dans la direction majoritaire) / (nombre total de TF)

Un signal composite est retourné si ``alignment_score >= min_alignment`` ;
sinon ``HOLD`` est retourné.

Variables d'environnement
--------------------------
- ``V9_MTF_ENABLED``           : active le multi-timeframe (bool, défaut False)
- ``V9_MTF_TIMEFRAMES``        : timeframes à combiner (str CSV, défaut "1h,4h,1d")
- ``V9_MTF_REQUIRE_ALIGNMENT`` : bloque les trades si pas d'alignement (bool, défaut True)
- ``V9_MTF_MIN_ALIGNMENT``     : fraction minimale de TF alignés (float 0-1, défaut 0.67)
- ``V9_MTF_SMA_FAST``          : période de la SMA rapide (int, défaut 20)
- ``V9_MTF_SMA_SLOW``          : période de la SMA lente (int, défaut 50)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from agents.market.market_scanner import MarketScanner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structures de données
# ---------------------------------------------------------------------------


@dataclass
class TimeframeSignal:
    """Signal calculé pour un seul timeframe."""

    timeframe: str
    direction: str          # "BUY", "SELL" ou "HOLD"
    strength: float         # 0.0 – 1.0  (distance relative close/SMA)
    sma_fast: float
    sma_slow: float
    close: float
    n_candles: int          # nombre de bougies utilisées pour le calcul


@dataclass
class MultiTimeframeResult:
    """Résultat agrégé de tous les timeframes pour un symbole."""

    symbol: str
    signals: list[TimeframeSignal] = field(default_factory=list)
    alignment_score: float = 0.0   # 0.0 – 1.0
    composite_signal: str = "HOLD"  # "BUY", "SELL", "HOLD"
    dominant_direction: str = "HOLD"
    n_bull: int = 0
    n_bear: int = 0
    n_neutral: int = 0

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "composite_signal": self.composite_signal,
            "alignment_score": self.alignment_score,
            "dominant_direction": self.dominant_direction,
            "n_bull": self.n_bull,
            "n_bear": self.n_bear,
            "n_neutral": self.n_neutral,
            "signals": [
                {
                    "timeframe": s.timeframe,
                    "direction": s.direction,
                    "strength": round(s.strength, 4),
                    "close": s.close,
                    "sma_fast": round(s.sma_fast, 4),
                    "sma_slow": round(s.sma_slow, 4),
                    "n_candles": s.n_candles,
                }
                for s in self.signals
            ],
        }


# ---------------------------------------------------------------------------
# Calcul de signal sur un seul timeframe
# ---------------------------------------------------------------------------


def _sma(values: list[float], period: int) -> float | None:
    """Simple Moving Average sur les ``period`` dernières valeurs."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute_timeframe_signal(
    candles: list[dict],
    timeframe: str,
    sma_fast: int = 20,
    sma_slow: int = 50,
) -> TimeframeSignal:
    """Calcule un signal directionnel à partir d'une liste de bougies OHLCV.

    Paramètres
    ----------
    candles:
        Liste de bougies avec au moins la clé ``"close"`` (format MarketScanner).
    timeframe:
        Label du timeframe (ex: ``"1h"``).
    sma_fast, sma_slow:
        Périodes des deux moyennes mobiles simples.
    """
    closes = [float(c["close"]) for c in candles if "close" in c]

    if len(closes) < sma_slow:
        # Pas assez de données → signal neutre
        last_close = closes[-1] if closes else 0.0
        return TimeframeSignal(
            timeframe=timeframe,
            direction="HOLD",
            strength=0.0,
            sma_fast=last_close,
            sma_slow=last_close,
            close=last_close,
            n_candles=len(closes),
        )

    fast = _sma(closes, sma_fast)
    slow = _sma(closes, sma_slow)
    close = closes[-1]

    assert fast is not None and slow is not None  # garantis par la vérification len >= sma_slow

    if fast > slow and close > fast:
        direction = "BUY"
        strength = (fast - slow) / slow if slow > 0 else 0.0
    elif fast < slow and close < fast:
        direction = "SELL"
        strength = (slow - fast) / slow if slow > 0 else 0.0
    else:
        direction = "HOLD"
        strength = 0.0

    return TimeframeSignal(
        timeframe=timeframe,
        direction=direction,
        strength=min(strength, 1.0),
        sma_fast=fast,
        sma_slow=slow,
        close=close,
        n_candles=len(closes),
    )


# ---------------------------------------------------------------------------
# Agrégateur multi-timeframe
# ---------------------------------------------------------------------------


class MultiTimeframeAggregator:
    """Agrège les signaux de plusieurs timeframes en un signal composite.

    Paramètres
    ----------
    timeframes:
        Liste des timeframes à analyser (ex: ``["1h", "4h", "1d"]``).
    min_alignment:
        Fraction minimale de timeframes qui doivent être dans la même direction
        pour que le signal composite soit BUY ou SELL (sinon HOLD).
    sma_fast, sma_slow:
        Périodes des moyennes mobiles utilisées pour chaque timeframe.
    """

    def __init__(
        self,
        timeframes: list[str] | None = None,
        min_alignment: float = 0.67,
        sma_fast: int = 20,
        sma_slow: int = 50,
    ) -> None:
        self.timeframes = timeframes or ["1h", "4h", "1d"]
        self.min_alignment = max(0.0, min(1.0, min_alignment))
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow

    def aggregate(
        self,
        candles_per_tf: dict[str, list[dict]],
        symbol: str = "UNKNOWN",
    ) -> MultiTimeframeResult:
        """Calcule le signal composite à partir de bougies par timeframe.

        Paramètres
        ----------
        candles_per_tf:
            Dictionnaire ``{timeframe: [candles]}``.
        symbol:
            Nom du symbole pour l'affichage/logging.
        """
        signals: list[TimeframeSignal] = []

        for tf in self.timeframes:
            tf_candles = candles_per_tf.get(tf, [])
            sig = compute_timeframe_signal(
                tf_candles, tf, sma_fast=self.sma_fast, sma_slow=self.sma_slow
            )
            signals.append(sig)

        n_bull = sum(1 for s in signals if s.direction == "BUY")
        n_bear = sum(1 for s in signals if s.direction == "SELL")
        n_neutral = sum(1 for s in signals if s.direction == "HOLD")
        n_total = len(signals)

        if n_total == 0:
            return MultiTimeframeResult(symbol=symbol, signals=signals)

        dominant_direction = "HOLD"
        alignment_count = 0

        if n_bull >= n_bear:
            dominant_direction = "BUY" if n_bull > 0 else "HOLD"
            alignment_count = n_bull
        else:
            dominant_direction = "SELL"
            alignment_count = n_bear

        alignment_score = alignment_count / n_total

        if alignment_score >= self.min_alignment and dominant_direction != "HOLD":
            composite_signal = dominant_direction
        else:
            composite_signal = "HOLD"

        result = MultiTimeframeResult(
            symbol=symbol,
            signals=signals,
            alignment_score=alignment_score,
            composite_signal=composite_signal,
            dominant_direction=dominant_direction,
            n_bull=n_bull,
            n_bear=n_bear,
            n_neutral=n_neutral,
        )

        logger.info(
            "MultiTimeframe %s: %s (align=%.0f%%, bull=%d bear=%d neutral=%d)",
            symbol,
            composite_signal,
            alignment_score * 100,
            n_bull,
            n_bear,
            n_neutral,
        )

        return result


# ---------------------------------------------------------------------------
# Scanner multi-timeframe (wrapping MarketScanner)
# ---------------------------------------------------------------------------


class MultiTimeframeScanner:
    """Récupère les bougies OHLCV pour plusieurs timeframes via ``MarketScanner``.

    Crée un ``MarketScanner`` dédié par timeframe (même exchange, cache TTL
    indépendant par timeframe). L'agrégateur est ensuite utilisé pour produire
    un ``MultiTimeframeResult`` par symbole.

    Paramètres
    ----------
    base_scanner:
        Instance ``MarketScanner`` existante (utilisée pour sa config : exchanges,
        symboles, cache_db_path). On emprunte ses exchanges pour éviter de
        re-créer des connexions.
    timeframes:
        Timeframes à récupérer (ex: ``["1h", "4h", "1d"]``).
    history_limit:
        Nombre de bougies à récupérer par timeframe.
    min_alignment:
        Seuil d'alignement pour le signal composite (transmis à l'agrégateur).
    sma_fast, sma_slow:
        Périodes des SMA (transmises à l'agrégateur).
    """

    def __init__(
        self,
        base_scanner: MarketScanner,
        timeframes: list[str] | None = None,
        history_limit: int = 200,
        min_alignment: float = 0.67,
        sma_fast: int = 20,
        sma_slow: int = 50,
    ) -> None:
        self._base = base_scanner
        self.timeframes = timeframes or ["1h", "4h", "1d"]
        self.history_limit = history_limit
        self.aggregator = MultiTimeframeAggregator(
            timeframes=self.timeframes,
            min_alignment=min_alignment,
            sma_fast=sma_fast,
            sma_slow=sma_slow,
        )

        # Crée un MarketScanner par timeframe additionnel (différent du timeframe
        # principal déjà géré par base_scanner).
        self._scanners: dict[str, "MarketScanner"] = {}
        self._init_tf_scanners()

    def _init_tf_scanners(self) -> None:
        """Initialise un scanner léger par timeframe."""
        for tf in self.timeframes:
            if tf == self._base.timeframe:
                # Réutilise le scanner principal pour son propre timeframe
                self._scanners[tf] = self._base
            else:
                scanner = MarketScanner(
                    symbols=self._base.symbols,
                    timeframe=tf,
                    cache_ttl=self._base._cache.ttl,
                    exchanges=list(self._base._exchanges.keys()),
                )
                # Injecte les mêmes objets exchange pour éviter des connexions dupliquées
                scanner._exchanges = self._base._exchanges
                self._scanners[tf] = scanner

    def fetch_multi(self, symbol: str) -> dict[str, list[dict]]:
        """Retourne un dict ``{timeframe: [candles]}`` pour le symbole donné."""
        result: dict[str, list[dict]] = {}
        for tf, scanner in self._scanners.items():
            candles = scanner.fetch_history(symbol, limit=self.history_limit)
            result[tf] = candles
            logger.debug(
                "MultiTimeframeScanner: %s/%s → %d bougies", symbol, tf, len(candles)
            )
        return result

    def analyze(self, symbol: str) -> MultiTimeframeResult:
        """Récupère les données et retourne le signal composite pour un symbole."""
        candles_per_tf = self.fetch_multi(symbol)
        return self.aggregator.aggregate(candles_per_tf, symbol=symbol)

    def analyze_all(self) -> dict[str, MultiTimeframeResult]:
        """Analyse tous les symboles du scanner de base."""
        return {sym: self.analyze(sym) for sym in self._base.symbols}
