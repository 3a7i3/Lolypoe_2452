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
    """Récupère les données OHLCV réelles via CCXT avec fallback multi-exchange.

    - `scan()` retourne la dernière bougie pour chaque symbole configuré.
    - `fetch_history()` retourne N bougies pour un symbole (utilisé par BacktestLab).
    - Un cache TTL évite les appels réseau répétés entre cycles.
    - Les exchanges sont essayés dans l'ordre configuré (défaut : binance → kraken → okx).
    - Fallback automatique sur des données synthétiques si tous les exchanges échouent.

    Paramètres
    ----------
    symbols:
        Liste de symboles au format interne (ex: ["BTCUSDT", "ETHUSDT"]).
    timeframe:
        Timeframe CCXT (ex: "1h", "4h", "15m"). Configurable via V9_CCXT_TIMEFRAME.
    cache_ttl:
        Durée de vie du cache en secondes. 0 = cache désactivé.
        Configurable via V9_CCXT_CACHE_TTL.
    exchanges:
        Ordre de priorité des exchanges CCXT (noms minuscules).
        Configurable via V9_CCXT_EXCHANGES (ex: "binance,kraken,okx").
    """

    def __init__(
        self,
        symbols: list[str] | None = None,
        timeframe: str = "1h",
        cache_ttl: float = 60.0,
        exchanges: list[str] | None = None,
    ) -> None:
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        self.timeframe = timeframe
        self.exchange_names = exchanges or ["binance"]
        self._cache = _Cache(ttl_seconds=cache_ttl)
        self._exchanges = self._init_exchanges()

    # ------------------------------------------------------------------
    # Compatibilité rétroactive — les tests existants utilisent _exchange
    # ------------------------------------------------------------------

    @property
    def _exchange(self):
        """Retourne le premier exchange disponible (compatibilité rétroactive)."""
        return next(iter(self._exchanges.values()), None)

    @_exchange.setter
    def _exchange(self, value) -> None:
        """Permet l'injection directe dans les tests (compatibilité rétroactive)."""
        if value is None:
            self._exchanges.clear()
        else:
            first_name = self.exchange_names[0] if self.exchange_names else "binance"
            self._exchanges = {first_name: value}

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_exchanges(self) -> dict:
        """Initialise tous les exchanges configurés via ccxt."""
        result: dict = {}
        try:
            import ccxt  # noqa: PLC0415

            for name in self.exchange_names:
                cls = getattr(ccxt, name, None)
                if cls is None:
                    logger.warning("Exchange '%s' non supporté par ccxt — ignoré", name)
                    continue
                try:
                    result[name] = cls({"timeout": 10_000, "enableRateLimit": True})
                    logger.info("MarketScanner: exchange '%s' initialisé via ccxt", name)
                except Exception as exc:
                    logger.warning("Impossible d'initialiser '%s' (%s) — ignoré", name, exc)
        except ImportError:
            logger.warning("ccxt non installé — MarketScanner utilisera des données synthétiques")
        return result

    # ------------------------------------------------------------------
    # scan() — dernière bougie par symbole
    # ------------------------------------------------------------------

    def _fetch_real(self) -> tuple[list[dict], str] | None:
        """Essaie chaque exchange dans l'ordre jusqu'au premier succès.

        Retourne ``(candles, exchange_name)`` ou ``None`` si tous échouent.
        """
        for name, exchange in self._exchanges.items():
            try:
                snapshots: list[dict] = []
                for internal_symbol in self.symbols:
                    ccxt_symbol = _to_ccxt_symbol(internal_symbol)
                    ohlcv = exchange.fetch_ohlcv(ccxt_symbol, self.timeframe, limit=2)
                    if not ohlcv:
                        logger.warning("Réponse OHLCV vide pour %s sur %s", ccxt_symbol, name)
                        raise ValueError(f"réponse vide pour {ccxt_symbol}")
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
                    "MarketScanner: OHLCV réel (%s, %s) depuis %s pour %d symboles [réseau]",
                    self.timeframe,
                    snapshots[0]["timestamp"] if snapshots else "?",
                    name,
                    len(snapshots),
                )
                return snapshots, name
            except Exception as exc:
                logger.warning(
                    "Échec fetch OHLCV %s (%s) — essai exchange suivant", name, exc
                )
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
        Si tous les exchanges échouent, bascule sur des données synthétiques.

        Le champ ``data_source`` indique l'origine des données :
        - ``"binance_real"``       : données live Binance via CCXT
        - ``"kraken_real"``        : données live Kraken (fallback)
        - ``"okx_real"``           : données live OKX (fallback)
        - ``"<name>_real"``        : tout exchange ccxt configuré
        - ``"synthetic_fallback"`` : données synthétiques (tous exchanges inaccessibles)
        """
        cache_key = f"scan:{self.timeframe}"
        cached = self._cache.get(cache_key)
        if cached is not _SENTINEL:
            logger.debug("MarketScanner: scan() servi depuis le cache")
            return cached  # cached est le dict complet {candles, data_source}

        result = self._fetch_real()
        if result is not None:
            candles, exchange_name = result
            response = {"candles": candles, "data_source": f"{exchange_name}_real"}
            self._cache.set(cache_key, response)
            return response

        synthetic = self._generate_synthetic()
        # On ne met PAS les données synthétiques en cache : on réessaie au prochain cycle
        return {"candles": synthetic, "data_source": "synthetic_fallback"}

    # ------------------------------------------------------------------
    # fetch_history() — N bougies pour un symbole
    # ------------------------------------------------------------------

    def fetch_history(self, symbol: str, limit: int = 200) -> list[dict]:
        """Retourne les ``limit`` dernières bougies OHLCV pour un seul symbole.

        Utilisé par BacktestLab pour calculer des métriques sur données réelles.
        Le résultat est mis en cache pendant ``cache_ttl`` secondes.
        Les exchanges sont essayés dans l'ordre ; retourne une liste vide si tous échouent.
        """
        cache_key = f"history:{symbol}:{self.timeframe}:{limit}"
        cached = self._cache.get(cache_key)
        if cached is not _SENTINEL:
            logger.debug("MarketScanner: fetch_history(%s) servi depuis le cache", symbol)
            return cached

        if not self._exchanges:
            return []

        ccxt_symbol = _to_ccxt_symbol(symbol)
        for name, exchange in self._exchanges.items():
            try:
                ohlcv = exchange.fetch_ohlcv(ccxt_symbol, self.timeframe, limit=limit)
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
                    "MarketScanner: historique %s (%d bougies, %s) depuis %s [réseau]",
                    symbol,
                    len(candles),
                    self.timeframe,
                    name,
                )
                self._cache.set(cache_key, candles)
                return candles
            except Exception as exc:
                logger.warning(
                    "fetch_history(%s) échoué sur %s (%s) — essai exchange suivant",
                    symbol,
                    name,
                    exc,
                )
        logger.warning("fetch_history(%s) — tous les exchanges ont échoué, historique vide", symbol)
        return []

