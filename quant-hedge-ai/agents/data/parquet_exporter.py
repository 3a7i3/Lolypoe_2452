"""
Option AJ — Export Parquet OHLCV (sauvegarde données CCXT).

Sauvegarde les données OHLCV récupérées via CCXT au format Parquet
pour réutilisation rapide sans appels réseau répétés.

Caractéristiques :
  - Compression snappy (rapide, bonne compression)
  - Partitionnement par symbol/timeframe dans le nom de fichier
  - Append ou overwrite configurable
  - Index temporel (timestamp ms → datetime UTC)
  - Lecture avec filtre since_ts / until_ts optionnel

Usage :
    from agents.data.parquet_exporter import ParquetExporter
    exp = ParquetExporter(output_dir="data/ohlcv_cache")
    meta = exp.save(symbol="BTC/USDT", timeframe="1h", ohlcv=[[ts, o, h, l, c, v], ...])
    df = exp.load(symbol="BTC/USDT", timeframe="1h")
"""
from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass
from typing import Optional
import time

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    _PARQUET_AVAILABLE = True
except ImportError:
    _PARQUET_AVAILABLE = False


# ── Dataclass métadonnées ─────────────────────────────────────────────────────

@dataclass
class ExportMetadata:
    symbol: str
    timeframe: str
    n_bars: int
    start_ts: int          # timestamp ms
    end_ts: int            # timestamp ms
    file_path: str
    compression: str
    file_size_bytes: int
    exported_at: str       # ISO 8601


# ── Colonnes OHLCV ────────────────────────────────────────────────────────────

_OHLCV_COLS = ["timestamp", "open", "high", "low", "close", "volume"]


# ── Exportateur ───────────────────────────────────────────────────────────────

class ParquetExporter:
    """
    Exporte et importe des données OHLCV au format Apache Parquet.

    Structure fichier : <output_dir>/<symbol_safe>_<timeframe>.parquet
    Ex : data/ohlcv_cache/BTC_USDT_1h.parquet
    """

    def __init__(self, output_dir: str = "data/ohlcv_cache", compression: str = "snappy") -> None:
        if not _PARQUET_AVAILABLE:
            raise ImportError(
                "pandas et pyarrow sont requis : pip install pandas pyarrow"
            )
        self._dir = pathlib.Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._compression = compression

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save(
        self,
        symbol: str,
        timeframe: str,
        ohlcv: list[list],
        append: bool = False,
    ) -> ExportMetadata:
        """
        Sauvegarde des données OHLCV CCXT au format Parquet.

        ohlcv : liste de listes [[timestamp_ms, open, high, low, close, volume], ...]
        """
        df_new = self._to_dataframe(ohlcv)

        path = self._file_path(symbol, timeframe)

        if append and path.exists():
            df_existing = self._read_parquet(path)
            df_combined = pd.concat([df_existing, df_new]).drop_duplicates(
                subset=["timestamp"]
            ).sort_values("timestamp").reset_index(drop=True)
        else:
            df_combined = df_new

        self._write_parquet(df_combined, path)

        stat = path.stat()
        start_ts = int(df_combined["timestamp"].iloc[0].timestamp() * 1000) if len(df_combined) > 0 else 0
        end_ts = int(df_combined["timestamp"].iloc[-1].timestamp() * 1000) if len(df_combined) > 0 else 0

        import datetime as dt
        return ExportMetadata(
            symbol=symbol,
            timeframe=timeframe,
            n_bars=len(df_combined),
            start_ts=start_ts,
            end_ts=end_ts,
            file_path=str(path),
            compression=self._compression,
            file_size_bytes=stat.st_size,
            exported_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        )

    # ── Chargement ────────────────────────────────────────────────────────────

    def load(
        self,
        symbol: str,
        timeframe: str,
        since_ts: Optional[int] = None,
        until_ts: Optional[int] = None,
    ) -> "pd.DataFrame":
        """
        Charge les données OHLCV depuis Parquet.
        Retourne un DataFrame vide (avec colonnes) si le fichier est absent.

        since_ts / until_ts : filtres en timestamp ms (optionnels).
        """
        path = self._file_path(symbol, timeframe)
        if not path.exists():
            logger.warning("ParquetExporter: fichier absent pour %s/%s", symbol, timeframe)
            return self._empty_dataframe()

        df = self._read_parquet(path)

        if since_ts is not None:
            since_dt = pd.Timestamp(since_ts, unit="ms", tz="UTC")
            df = df[df["timestamp"] >= since_dt]
        if until_ts is not None:
            until_dt = pd.Timestamp(until_ts, unit="ms", tz="UTC")
            df = df[df["timestamp"] <= until_dt]

        return df.reset_index(drop=True)

    # ── Inventaire ────────────────────────────────────────────────────────────

    def list_available(self, symbol: Optional[str] = None) -> list[dict]:
        """Liste les fichiers disponibles avec métadonnées basiques."""
        results = []
        for path in sorted(self._dir.glob("*.parquet")):
            name = path.stem  # ex: BTC_USDT_1h
            parts = name.rsplit("_", 1)
            if len(parts) != 2:
                continue
            sym_safe, tf = parts
            sym = sym_safe.replace("_", "/")

            if symbol is not None and sym != symbol:
                continue

            stat = path.stat()
            results.append({
                "symbol": sym,
                "timeframe": tf,
                "file": str(path),
                "size_bytes": stat.st_size,
                "mtime": stat.st_mtime,
            })
        return results

    def delete(self, symbol: str, timeframe: str) -> bool:
        """Supprime le fichier Parquet d'un symbole/timeframe. Retourne True si supprimé."""
        path = self._file_path(symbol, timeframe)
        if path.exists():
            path.unlink()
            logger.info("ParquetExporter: supprimé %s", path)
            return True
        return False

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _symbol_to_filename(self, symbol: str, timeframe: str) -> str:
        safe = symbol.replace("/", "_").replace(":", "_")
        return f"{safe}_{timeframe}.parquet"

    def _file_path(self, symbol: str, timeframe: str) -> pathlib.Path:
        return self._dir / self._symbol_to_filename(symbol, timeframe)

    def _to_dataframe(self, ohlcv: list[list]) -> "pd.DataFrame":
        if not ohlcv:
            return self._empty_dataframe()
        df = pd.DataFrame(ohlcv, columns=_OHLCV_COLS[:len(ohlcv[0])])
        # Compléter les colonnes manquantes
        for col in _OHLCV_COLS:
            if col not in df.columns:
                df[col] = 0.0
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype("float64")
        return df[_OHLCV_COLS].sort_values("timestamp").reset_index(drop=True)

    def _empty_dataframe(self) -> "pd.DataFrame":
        df = pd.DataFrame(columns=_OHLCV_COLS)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.Series(dtype="float64")
        return df

    def _write_parquet(self, df: "pd.DataFrame", path: pathlib.Path) -> None:
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, str(path), compression=self._compression)
        logger.debug("ParquetExporter: écrit %d lignes → %s", len(df), path)

    def _read_parquet(self, path: pathlib.Path) -> "pd.DataFrame":
        table = pq.read_table(str(path))
        df = table.to_pandas()
        if "timestamp" in df.columns and not hasattr(df["timestamp"], "dt"):
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        elif "timestamp" in df.columns and df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        return df
