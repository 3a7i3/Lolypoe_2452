from __future__ import annotations

import json
import logging
import random
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
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


class _PersistentCache(_Cache):
    """Cache TTL avec persistance SQLite pour survivre aux redémarrages.

    Étend ``_Cache`` en synchronisant chaque écriture vers un fichier SQLite.
    Au démarrage, les entrées non expirées sont rechargées depuis le disque.

    Paramètres
    ----------
    ttl_seconds:
        Durée de vie des entrées (en secondes). 0 = cache désactivé.
    db_path:
        Chemin du fichier SQLite. Les répertoires parents sont créés si nécessaire.
    """

    _CREATE_SQL = """
        CREATE TABLE IF NOT EXISTS cache_entries (
            key       TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """

    def __init__(self, ttl_seconds: float = 60.0, db_path: str | Path = "market_cache.db") -> None:
        super().__init__(ttl_seconds)
        self._db_path = Path(db_path)
        self._init_db()
        self._load_from_disk()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")  # évite les locks sur Windows
        return conn

    def _init_db(self) -> None:
        """Crée le répertoire et la table SQLite si nécessaire."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as conn:
                conn.execute(self._CREATE_SQL)
        except Exception as exc:
            logger.warning("_PersistentCache: impossible d'initialiser SQLite (%s)", exc)

    def _load_from_disk(self) -> None:
        """Charge les entrées non expirées depuis SQLite vers le store en mémoire."""
        if self.ttl <= 0:
            return
        now = time.time()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT key, value_json FROM cache_entries WHERE expires_at > ?", (now,)
                ).fetchall()
            for key, value_json in rows:
                try:
                    value = json.loads(value_json)
                    # On insère dans le store mémoire avec le timestamp actuel —
                    # l'entrée sera valide pour un TTL complet à partir du rechargement.
                    self._store[key] = (time.monotonic(), value)
                except json.JSONDecodeError:
                    logger.warning("_PersistentCache: entrée corrompue pour la clé '%s' — ignorée", key)
            if rows:
                logger.info("_PersistentCache: %d entrée(s) rechargée(s) depuis %s", len(rows), self._db_path)
        except Exception as exc:
            logger.warning("_PersistentCache: échec lecture disque (%s) — démarrage à froid", exc)

    def set(self, key: str, value: Any) -> None:
        """Écrit dans le store mémoire ET sur disque."""
        super().set(key, value)
        if self.ttl <= 0:
            return
        expires_at = time.time() + self.ttl
        try:
            value_json = json.dumps(value)
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache_entries (key, value_json, expires_at) VALUES (?, ?, ?)",
                    (key, value_json, expires_at),
                )
        except Exception as exc:
            logger.warning("_PersistentCache: échec écriture disque pour '%s' (%s)", key, exc)

    def invalidate(self, key: str | None = None) -> None:
        """Invalide en mémoire ET sur disque."""
        super().invalidate(key)
        try:
            with self._connect() as conn:
                if key is None:
                    conn.execute("DELETE FROM cache_entries")
                else:
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        except Exception as exc:
            logger.warning("_PersistentCache: échec invalidation disque (%s)", exc)

    def purge_expired(self) -> int:
        """Supprime les entrées expirées du disque. Retourne le nombre supprimé."""
        now = time.time()
        try:
            with self._connect() as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE expires_at <= ?", (now,))
                return cursor.rowcount
        except Exception as exc:
            logger.warning("_PersistentCache: échec purge disque (%s)", exc)
            return 0


@dataclass
class _ExchangeMetrics:
    """Métriques de performance pour un exchange CCXT."""

    name: str
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    last_success_at: float = 0.0  # time.time() du dernier succès

    @property
    def avg_latency_ms(self) -> float:
        if self.successes == 0:
            return 0.0
        return self.total_latency_ms / self.successes

    @property
    def success_rate(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.successes / self.calls

    def record_success(self, latency_ms: float) -> None:
        self.calls += 1
        self.successes += 1
        self.total_latency_ms += latency_ms
        self.last_success_at = time.time()

    def record_failure(self) -> None:
        self.calls += 1
        self.failures += 1


class _LiveTickerFeed:
    """Thread daemon qui rafraîchit les prix en continu via fetch_tickers().

    Fonctionne en arrière-plan et met à jour ``latest_snapshot`` toutes les
    ``interval`` secondes. Si un exchange échoue, essaie le suivant
    (même logique de fallback que ``_fetch_real``).

    ``data_source`` est suffixé ``_ws`` (ex: ``"binance_ws"``) pour distinguer
    les données live des données REST OHLCV.
    """

    def __init__(
        self,
        exchanges: dict,  # {name: ccxt_exchange}
        symbols: list[str],
        interval: float = 5.0,
    ) -> None:
        self._exchanges = exchanges
        self._symbols = symbols
        self._interval = interval
        self.latest_snapshot: dict | None = None  # {candles, data_source, fetched_at}
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="LiveTickerFeed")

    def start(self) -> None:
        self._thread.start()
        logger.info("_LiveTickerFeed: démarré (interval=%.1fs)", self._interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=self._interval + 2)
        logger.info("_LiveTickerFeed: arrêté")

    @property
    def is_fresh(self) -> bool:
        """Retourne True si le dernier snapshot a moins de 2*interval secondes."""
        if self.latest_snapshot is None:
            return False
        age = time.monotonic() - self.latest_snapshot["fetched_at"]
        return age < self._interval * 2

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._refresh()
            self._stop_event.wait(timeout=self._interval)

    def _refresh(self) -> None:
        for name, exchange in self._exchanges.items():
            try:
                ccxt_symbols = [_to_ccxt_symbol(s) for s in self._symbols]
                tickers = exchange.fetch_tickers(ccxt_symbols)
                candles: list[dict] = []
                for internal_symbol in self._symbols:
                    ccxt_sym = _to_ccxt_symbol(internal_symbol)
                    t = tickers.get(ccxt_sym)
                    if t is None:
                        raise ValueError(f"ticker absent pour {ccxt_sym}")
                    candles.append({
                        "symbol": internal_symbol,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "open": float(t.get("open") or t.get("last") or 0),
                        "high": float(t.get("high") or t.get("last") or 0),
                        "low": float(t.get("low") or t.get("last") or 0),
                        "close": float(t.get("last") or 0),
                        "volume": float(t.get("baseVolume") or 0),
                    })
                self.latest_snapshot = {
                    "candles": candles,
                    "data_source": f"{name}_ws",
                    "fetched_at": time.monotonic(),
                }
                logger.debug("_LiveTickerFeed: snapshot rafraîchi depuis %s", name)
                return  # succès — on ne tente pas l'exchange suivant
            except Exception as exc:
                logger.debug("_LiveTickerFeed: %s échoué (%s) — essai suivant", name, exc)
        logger.debug("_LiveTickerFeed: tous les exchanges ont échoué ce cycle")


class MarketScanner:
    """Récupère les données OHLCV réelles via CCXT avec fallback multi-exchange.

    - `scan()` retourne la dernière bougie pour chaque symbole configuré.
    - `fetch_history()` retourne N bougies pour un symbole (utilisé par BacktestLab).
    - Un cache TTL évite les appels réseau répétés entre cycles.
    - Les exchanges sont essayés dans l'ordre configuré (défaut : binance → kraken → okx).
    - Fallback automatique sur des données synthétiques si tous les exchanges échouent.
    - Live feed optionnel : thread daemon qui rafraîchit les prix toutes les N secondes.
    - Métriques par exchange : latence moyenne, taux de succès, nombre d'appels.

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
    cache_db_path:
        Chemin SQLite pour la persistance du cache (option F). None = mémoire seule.
    live_feed_interval:
        Intervalle en secondes du live ticker feed (option G). 0 = désactivé.
        Configurable via V9_CCXT_WS_INTERVAL (activé si V9_CCXT_WS_ENABLED=true).
    """

    def __init__(
        self,
        symbols: list[str] | None = None,
        timeframe: str = "1h",
        cache_ttl: float = 60.0,
        exchanges: list[str] | None = None,
        cache_db_path: str | Path | None = None,
        live_feed_interval: float = 0.0,
    ) -> None:
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        self.timeframe = timeframe
        self.exchange_names = exchanges or ["binance"]
        if cache_db_path:
            self._cache: _Cache = _PersistentCache(ttl_seconds=cache_ttl, db_path=cache_db_path)
            logger.info("MarketScanner: cache persistant activé → %s", cache_db_path)
        else:
            self._cache = _Cache(ttl_seconds=cache_ttl)
        self._exchanges = self._init_exchanges()
        self._metrics: dict[str, _ExchangeMetrics] = {
            name: _ExchangeMetrics(name=name) for name in self.exchange_names
        }
        self._live_feed: _LiveTickerFeed | None = None
        if live_feed_interval > 0 and self._exchanges:
            self._live_feed = _LiveTickerFeed(
                exchanges=self._exchanges,
                symbols=self.symbols,
                interval=live_feed_interval,
            )
            self._live_feed.start()

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
    # Cycle de vie
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Arrête proprement le live feed si actif."""
        if self._live_feed is not None:
            self._live_feed.stop()
            self._live_feed = None

    # ------------------------------------------------------------------
    # Métriques par exchange (option I)
    # ------------------------------------------------------------------

    @property
    def exchange_metrics(self) -> dict[str, _ExchangeMetrics]:
        """Retourne les métriques de performance par exchange."""
        return self._metrics

    def get_metrics_report(self) -> str:
        """Retourne un rapport texte des métriques par exchange."""
        if not self._metrics:
            return "📊 EXCHANGE METRICS\n   Aucune donnée\n"
        lines = ["📊 EXCHANGE METRICS"]
        for name, m in self._metrics.items():
            last_ok = (
                datetime.fromtimestamp(m.last_success_at, tz=timezone.utc).strftime("%H:%M:%S")
                if m.last_success_at > 0
                else "jamais"
            )
            status = "🟢" if m.success_rate >= 0.8 else ("🟡" if m.success_rate >= 0.5 else "🔴")
            lines.append(
                f"   {status} {name:<10s}  appels={m.calls:3d}  succès={m.successes:3d}"
                f"  échecs={m.failures:2d}  taux={m.success_rate:.0%}"
                f"  latence_moy={m.avg_latency_ms:.0f}ms  dernier_ok={last_ok}"
            )
        return "\n".join(lines) + "\n"

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
        Enregistre les métriques de latence et de succès/échec par exchange.
        """
        for name, exchange in self._exchanges.items():
            t0 = time.monotonic()
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
                latency_ms = (time.monotonic() - t0) * 1000
                if name in self._metrics:
                    self._metrics[name].record_success(latency_ms)
                logger.info(
                    "MarketScanner: OHLCV réel (%s, %s) depuis %s pour %d symboles [réseau, %.0fms]",
                    self.timeframe,
                    snapshots[0]["timestamp"] if snapshots else "?",
                    name,
                    len(snapshots),
                    latency_ms,
                )
                return snapshots, name
            except Exception as exc:
                if name in self._metrics:
                    self._metrics[name].record_failure()
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

        Priorité : live feed (option G) > cache TTL > REST OHLCV > synthétique.
        Si tous les exchanges échouent, bascule sur des données synthétiques.

        ``data_source`` :
        - ``"<name>_ws"``          : live ticker feed (background thread)
        - ``"<name>_real"``        : REST OHLCV via CCXT
        - ``"synthetic_fallback"`` : données synthétiques
        """
        # 1. Live feed en priorité (option G)
        if self._live_feed is not None and self._live_feed.is_fresh:
            logger.debug("MarketScanner: scan() servi depuis le live feed")
            return self._live_feed.latest_snapshot  # type: ignore[return-value]

        # 2. Cache TTL
        cache_key = f"scan:{self.timeframe}"
        cached = self._cache.get(cache_key)
        if cached is not _SENTINEL:
            logger.debug("MarketScanner: scan() servi depuis le cache")
            return cached

        # 3. REST OHLCV
        result = self._fetch_real()
        if result is not None:
            candles, exchange_name = result
            response = {"candles": candles, "data_source": f"{exchange_name}_real"}
            self._cache.set(cache_key, response)
            return response

        # 4. Synthétique
        synthetic = self._generate_synthetic()
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
            t0 = time.monotonic()
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
                latency_ms = (time.monotonic() - t0) * 1000
                if name in self._metrics:
                    self._metrics[name].record_success(latency_ms)
                logger.info(
                    "MarketScanner: historique %s (%d bougies, %s) depuis %s [réseau, %.0fms]",
                    symbol,
                    len(candles),
                    self.timeframe,
                    name,
                    latency_ms,
                )
                self._cache.set(cache_key, candles)
                return candles
            except Exception as exc:
                if name in self._metrics:
                    self._metrics[name].record_failure()
                logger.warning(
                    "fetch_history(%s) échoué sur %s (%s) — essai exchange suivant",
                    symbol,
                    name,
                    exc,
                )
        logger.warning("fetch_history(%s) — tous les exchanges ont échoué, historique vide", symbol)
        return []

