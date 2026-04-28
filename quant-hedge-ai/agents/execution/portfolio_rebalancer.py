"""Option X — Portfolio Rebalancer (auto-rebalancing multi-symbole).

Calcule les ordres de rééquilibrage nécessaires pour aligner les poids
courants du portefeuille sur les poids cibles, en respectant un seuil
de dérive minimum (drift threshold) pour éviter le sur-trading.

Workflow dans main_v91.py :
    rebalancer = PortfolioRebalancer(drift_threshold=0.05)
    current_weights = paper.get_weights()   # {symbol: fraction}
    target_weights = symbol_router.allocate(candles)  # {symbol: fraction}
    orders = rebalancer.compute_orders(current_weights, target_weights, equity)
    for order in orders:
        paper.execute(order, mark_price=prices[order['symbol']], cycle=cycle)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RebalanceOrder:
    """Ordre de rééquilibrage."""

    symbol: str
    action: str        # "BUY" | "SELL" | "HOLD"
    drift: float       # écart poids courant vs cible
    current_w: float   # poids actuel
    target_w: float    # poids cible
    delta_value: float  # valeur à acheter/vendre (positif = BUY, négatif = SELL)


class PortfolioRebalancer:
    """Calcule les ordres de rééquilibrage minimal.

    Args:
        drift_threshold:  seuil minimum d'écart (en fraction) pour déclencher
                          un rééquilibrage. Ex: 0.05 = 5% de dérive tolérée.
        max_orders:       nombre max d'ordres par cycle (évite le sur-trading).

    Raises:
        ValueError: si les paramètres sont invalides.
    """

    def __init__(
        self,
        drift_threshold: float = 0.05,
        max_orders: int = 5,
    ) -> None:
        if not (0.0 <= drift_threshold < 1.0):
            raise ValueError(f"drift_threshold doit être dans [0, 1), reçu: {drift_threshold}")
        if max_orders < 1:
            raise ValueError(f"max_orders doit être >= 1, reçu: {max_orders}")

        self.drift_threshold = drift_threshold
        self.max_orders = max_orders

    def compute_orders(
        self,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
        equity: float = 0.0,
    ) -> list[RebalanceOrder]:
        """Calcule les ordres de rééquilibrage nécessaires.

        Args:
            current_weights: poids actuels {symbol: fraction [0, 1]}.
            target_weights:  poids cibles {symbol: fraction [0, 1]}.
            equity:          valeur totale du portefeuille (pour delta_value).

        Returns:
            Liste d'ordres triés par drift décroissant, taille <= max_orders.
        """
        # Union de tous les symboles
        all_symbols = set(current_weights) | set(target_weights)
        orders: list[RebalanceOrder] = []

        for symbol in all_symbols:
            current_w = current_weights.get(symbol, 0.0)
            target_w = target_weights.get(symbol, 0.0)
            drift = target_w - current_w

            if abs(drift) < self.drift_threshold:
                continue  # drift insuffisant, ne pas rééquilibrer

            action = "BUY" if drift > 0 else "SELL"
            delta_value = drift * equity if equity > 0 else 0.0

            orders.append(RebalanceOrder(
                symbol=symbol,
                action=action,
                drift=round(drift, 6),
                current_w=round(current_w, 6),
                target_w=round(target_w, 6),
                delta_value=round(delta_value, 4),
            ))

        # Trier par drift absolu décroissant (priorité aux plus grands écarts)
        orders.sort(key=lambda o: abs(o.drift), reverse=True)
        return orders[:self.max_orders]

    def needs_rebalance(
        self,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
    ) -> bool:
        """Vérifie si un rééquilibrage est nécessaire (drift >= threshold)."""
        all_symbols = set(current_weights) | set(target_weights)
        for symbol in all_symbols:
            drift = abs(target_weights.get(symbol, 0.0) - current_weights.get(symbol, 0.0))
            if drift >= self.drift_threshold:
                return True
        return False

    def status(
        self,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
    ) -> dict:
        """Résumé de l'état du portefeuille pour le dashboard."""
        all_symbols = sorted(set(current_weights) | set(target_weights))
        details = []
        max_drift = 0.0
        for sym in all_symbols:
            cw = current_weights.get(sym, 0.0)
            tw = target_weights.get(sym, 0.0)
            d = tw - cw
            max_drift = max(max_drift, abs(d))
            details.append({"symbol": sym, "current": round(cw, 4), "target": round(tw, 4), "drift": round(d, 4)})

        return {
            "symbols": details,
            "max_drift": round(max_drift, 4),
            "needs_rebalance": max_drift >= self.drift_threshold,
            "drift_threshold": self.drift_threshold,
        }
