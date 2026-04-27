from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_SENTINEL = object()  # valeur sentinelle pour distinguer "pas de cache" de None


def _to_ccxt_symbol(symbol: str) -> str:
    """Convertit le format interne (ex: BTCUSDT) vers le format CCXT (BTC/USDT)."""
    if "/" in symbol:
        return symbol
    if symbol.endswith("USDT"):
        return symbol[:-4] + "/USDT"
    if symbol.endswith("BTC"):
        return symbol[:-3] + "/BTC"
    return symbol


def _to_internal_symbol(ccxt_symbol: str) -> str:
    """Convertit le format CCXT (BTC/USDT) vers le format interne (BTCUSDT)."""
    return ccxt_symbol.replace("/", "")


class _Cache:
    """Cache TTL générique pour éviter les appels réseau répétés.

    Chaque entrée est indexée par une clé et expire après ``ttl_seconds``.
    Un TTL de 0 désactive le cache (toujours invalide).
    """

    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}  # clé → (timestamp, valeur)

    def get(self, key: str) -> Any:
        """Retourne la valeur si valide, sinon ``_SENTINEL``."""
        if self.ttl <= 0:
            return _SENTINEL
        entry = self._store.get(key)
        if entry is None:
            return _SENTINEL
        ts, value = entry
        if time.monotonic() - ts > self.ttl:
            del self._store[key]
            return _SENTINEL
        return value

    def set(self, key: str, value: Any) -> None:
        if self.ttl > 0:
            self._store[key] = (time.monotonic(), value)

    def invalidate(self, key: str | None = None) -> None:
        """Invalide une clé spécifique ou tout le cache."""
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)

    @property
    def size(self) -> int:
        return len(self._store)


class MarketScanner:
    """Récupère les données OHLCV réelles depuis Binance via CCXT.

    - `scan()` retourne la dernière bougie pour chaque symbole configuré.
    - `fetch_history()` retourne N bougies pour un symbole (utilisé par BacktestLab).
    - Un cache TTL évite les appels réseau répétés entre cycles.
    - Fallback automatique sur des données synthétiques si Binance est inaccessible.

    Paramètres
    ----------
    symbols:
        Liste de symboles au format interne (ex: ["BTCUSDT", "ETHUSDT"]).
    timeframe:
        Timeframe CCXT (ex: "1h", "4h", "15m"). Configurable via V9_CCXT_TIMEFRAME.
    cache_ttl:
        Durée de vie du cache en secondes. 0 = cache désactivé.
        Configurable via V9_CCXT_CACHE_TTL.
    """

    def __init__(
        self,
        symbols: list[str] | None = None,
        timeframe: str = "1h",
        cache_ttl: float = 60.0,
    ) -> None:
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        self.timeframe = timeframe
        self._cache = _Cache(ttl_seconds=cache_ttl)
        self._exchange = self._init_exchange()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_exchange(self):
        try:
            import ccxt  # noqa: PLC0415

            exchange = ccxt.binance({"timeout": 10_000, "enableRateLimit": True})
            logger.info("MarketScanner: exchange Binance initialisé via ccxt")
            return exchange
        except ImportError:
            logger.warning("ccxt non installé — MarketScanner utilisera des données synthétiques")
        except Exception as exc:
            logger.warning("Impossible d'initialiser Binance (%s) — données synthétiques", exc)
        return None

    # ------------------------------------------------------------------
    # scan() — dernière bougie par symbole
    # ------------------------------------------------------------------

    def _fetch_real(self) -> list[dict] | None:
        """Récupère la dernière bougie OHLCV pour chaque symbole depuis Binance."""
        if self._exchange is None:
            return None
        try:
            snapshots: list[dict] = []
            for internal_symbol in self.symbols:
                ccxt_symbol = _to_ccxt_symbol(internal_symbol)
                ohlcv = self._exchange.fetch_ohlcv(ccxt_symbol, self.timeframe, limit=2)
                if not ohlcv:
                    logger.warning("Réponse OHLCV vide pour %s", ccxt_symbol)
                    return None
                ts, open_, high, low, close, volume = ohlcv[-1]
                snapshots.append(
                    {
                        "symbol": internal_symbol,
                        "timestamp": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat(),
                        "open": float(open_),
                        "high": float(high),
                        "low": float(low),
                        "close": float(close),
                        "volume": float(volume),
                    }
                )
            logger.info(
                "MarketScanner: OHLCV réel (%s, %s) pour %d symboles [réseau]",
                self.timeframe,
                snapshots[0]["timestamp"] if snapshots else "?",
                len(snapshots),
            )
            return snapshots
        except Exception as exc:
            logger.warning("Échec fetch OHLCV Binance (%s) — bascule sur données synthétiques", exc)
            return None

    def _generate_synthetic(self) -> list[dict]:
        """Génère des données OHLCV synthétiques (fallback)."""
        snapshots: list[dict] = []
        for symbol in self.symbols:
            base = random.uniform(100, 70_000)
            close = base * random.uniform(0.995, 1.005)
            snapshots.append(
                {
                    "symbol": symbol,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "open": base,
                    "close": close,
                    "high": max(base, close) * random.uniform(1.0, 1.01),
                    "low": min(base, close) * random.uniform(0.99, 1.0),
                    "volume": random.uniform(1_000, 500_000),
                }
            )
        return snapshots

    def scan(self) -> dict:
        """Retourne la dernière bougie OHLCV pour chaque symbole.

        Le résultat est mis en cache pendant ``cache_ttl`` secondes.
        Si Binance est inaccessible, bascule sur des données synthétiques.

        Le champ ``data_source`` indique l'origine des données :
        - ``"binance_real"``       : données live Binance via CCXT
        - ``"synthetic_fallback"`` : données synthétiques (Binance inaccessible)
        """
        cache_key = f"scan:{self.timeframe}"
        cached = self._cache.get(cache_key)
        if cached is not _SENTINEL:
            logger.debug("MarketScanner: scan() servi depuis le cache")
            return {"candles": cached, "data_source": "binance_real"}

        real = self._fetch_real()
        if real is not None:
            self._cache.set(cache_key, real)
            return {"candles": real, "data_source": "binance_real"}

        synthetic = self._generate_synthetic()
        # On ne met PAS les données synthétiques en cache : on réessaie Binance au prochain cycle
        return {"candles": synthetic, "data_source": "synthetic_fallback"}

    # ------------------------------------------------------------------
    # fetch_history() — N bougies pour un symbole
    # ------------------------------------------------------------------

    def fetch_history(self, symbol: str, limit: int = 200) -> list[dict]:
        """Retourne les ``limit`` dernières bougies OHLCV pour un seul symbole.

        Utilisé par BacktestLab pour calculer des métriques sur données réelles.
        Le résultat est mis en cache pendant ``cache_ttl`` secondes.
        Retourne une liste vide si Binance est inaccessible.
        """
        cache_key = f"history:{symbol}:{self.timeframe}:{limit}"
        cached = self._cache.get(cache_key)
        if cached is not _SENTINEL:
            logger.debug("MarketScanner: fetch_history(%s) servi depuis le cache", symbol)
            return cached

        if self._exchange is None:
            return []
        try:
            ccxt_symbol = _to_ccxt_symbol(symbol)
            ohlcv = self._exchange.fetch_ohlcv(ccxt_symbol, self.timeframe, limit=limit)
            candles = [
                {
                    "symbol": symbol,
                    "timestamp": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat(),
                    "open": float(o),
                    "high": float(h),
                    "low": float(lo),
                    "close": float(c),
                    "volume": float(v),
                }
                for ts, o, h, lo, c, v in ohlcv
            ]
            logger.info(
                "MarketScanner: historique %s (%d bougies, %s) [réseau]",
                symbol,
                len(candles),
                self.timeframe,
            )
            self._cache.set(cache_key, candles)
            return candles
        except Exception as exc:
            logger.warning("fetch_history(%s) échoué (%s) — historique vide", symbol, exc)
            return []

