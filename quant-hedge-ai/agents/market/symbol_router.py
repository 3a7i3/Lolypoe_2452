"""Option Q — SymbolRouter : distribution du capital sur plusieurs symboles.

Permet de dispatcher le capital et les ordres sur plusieurs paires
en parallèle, pondérées par le volume ou de façon équipondérée.

Workflow :
    router = SymbolRouter(max_symbols=3, weighting="volume")
    allocations = router.allocate(candles, total_size=0.10)
    # → {"BTCUSDT": 0.05, "ETHUSDT": 0.03, "SOLUSDT": 0.02}
    top = router.top_symbols(candles, n=3)
"""
from __future__ import annotations

from typing import Literal

WeightingMode = Literal["volume", "equal"]


class SymbolRouter:
    """Distribue la taille de position sur plusieurs symboles.

    Args:
        max_symbols:  nombre maximum de symboles tradés en parallèle.
        weighting:    ``"volume"`` pondère par volume relatif,
                      ``"equal"`` divise équitablement.
        min_volume:   volume minimum en USD pour qu'un symbole soit éligible.

    Raises:
        ValueError: si max_symbols < 1 ou weighting invalide.
    """

    VALID_WEIGHTINGS: frozenset[str] = frozenset({"volume", "equal"})

    def __init__(
        self,
        max_symbols: int = 3,
        weighting: WeightingMode = "volume",
        min_volume: float = 0.0,
    ) -> None:
        if max_symbols < 1:
            raise ValueError(f"max_symbols doit être >= 1, reçu: {max_symbols}")
        if weighting not in self.VALID_WEIGHTINGS:
            raise ValueError(f"weighting={weighting!r} invalide. Valeurs: {sorted(self.VALID_WEIGHTINGS)}")
        if min_volume < 0:
            raise ValueError(f"min_volume doit être >= 0, reçu: {min_volume}")

        self.max_symbols = max_symbols
        self.weighting: WeightingMode = weighting
        self.min_volume = min_volume

    # ------------------------------------------------------------------
    # API principale
    # ------------------------------------------------------------------

    def top_symbols(self, candles: list[dict], n: int | None = None) -> list[str]:
        """Retourne les N meilleurs symboles triés par volume décroissant.

        Args:
            candles: liste de bougies avec keys ``symbol`` et ``volume``.
            n: nombre de symboles (défaut = max_symbols).

        Returns:
            Liste de symboles triés par volume décroissant, filtrés par min_volume.
        """
        n = n if n is not None else self.max_symbols
        eligible = [
            c for c in candles
            if float(c.get("volume", 0.0)) * float(c.get("close", 1.0)) >= self.min_volume
        ]
        # Déduplique par symbole (garde le plus grand volume si doublons)
        seen: dict[str, float] = {}
        for c in eligible:
            sym = c["symbol"]
            vol = float(c.get("volume", 0.0))
            if sym not in seen or vol > seen[sym]:
                seen[sym] = vol

        sorted_symbols = sorted(seen, key=lambda s: seen[s], reverse=True)
        return sorted_symbols[:n]

    def allocate(
        self,
        candles: list[dict],
        total_size: float,
    ) -> dict[str, float]:
        """Distribue ``total_size`` entre les meilleurs symboles.

        Args:
            candles:    liste de bougies.
            total_size: fraction de capital totale à distribuer (ex. 0.10).

        Returns:
            Dict ``{symbol: fraction}`` dont la somme ≈ total_size.
            Retourne dict vide si candles est vide.
        """
        if not candles or total_size <= 0:
            return {}

        symbols = self.top_symbols(candles)
        if not symbols:
            return {}

        if self.weighting == "equal":
            per_symbol = total_size / len(symbols)
            return {s: round(per_symbol, 6) for s in symbols}

        # Volume-weighted
        vol_map: dict[str, float] = {}
        for c in candles:
            sym = c["symbol"]
            if sym in symbols:
                vol = float(c.get("volume", 0.0))
                if sym not in vol_map or vol > vol_map[sym]:
                    vol_map[sym] = vol

        total_vol = sum(vol_map.values())
        if total_vol <= 0:
            # Fallback equal
            per_symbol = total_size / len(symbols)
            return {s: round(per_symbol, 6) for s in symbols}

        return {
            s: round(vol_map.get(s, 0.0) / total_vol * total_size, 6)
            for s in symbols
        }

    def build_orders(
        self,
        candles: list[dict],
        action: str,
        total_size: float,
    ) -> list[dict]:
        """Construit la liste d'ordres pour tous les symboles alloués.

        Args:
            candles:    liste de bougies.
            action:     ``"BUY"``, ``"SELL"``, ou ``"HOLD"``.
            total_size: fraction totale du capital.

        Returns:
            Liste de dicts ``{symbol, action, size}``.
        """
        allocations = self.allocate(candles, total_size)
        return [
            {"symbol": sym, "action": action, "size": size}
            for sym, size in allocations.items()
            if size > 0
        ]
