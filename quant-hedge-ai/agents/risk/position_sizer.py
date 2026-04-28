"""Option V — Position Sizing adaptatif (Kelly + CVaR).

Combine le Kelly Criterion et la limite CVaR pour calculer la fraction
de capital à allouer à chaque trade.

Formule:
    kelly_f = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win
    kelly_capped = min(kelly_f, max_kelly_fraction)
    cvar_cap = 1 - CVaR / initial_balance   (si CVaR disponible)
    size = min(kelly_capped, cvar_cap, max_size)

Workflow dans main_v91.py :
    sizer = PositionSizer(cfg)
    size = sizer.compute(
        win_rate=paper_state["win_rate"],
        avg_win=paper_state.get("avg_win", 0.0),
        avg_loss=paper_state.get("avg_loss", 0.0),
        cvar=cvar_result.get("cvar_95", 0.0),
        portfolio_value=paper_state["equity"],
    )
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SizingResult:
    """Résultat du calcul de taille de position."""

    size: float           # fraction [0, 1] du capital à allouer
    kelly_f: float        # Kelly brut
    kelly_capped: float   # Kelly plafonné
    cvar_cap: float       # plafond CVaR (1.0 si CVaR non disponible)
    method: str           # "kelly_cvar" | "kelly_only" | "min_fallback"
    reason: str           # explication courte


class PositionSizer:
    """Calcule la taille de position adaptative via Kelly + CVaR.

    Args:
        max_kelly_fraction: fraction Kelly max (ex. 0.25 = 25% du capital).
        max_position_size:  taille max absolue quel que soit le calcul.
        min_position_size:  taille min si Kelly positif (évite les micro-trades).
        kelly_half:         si True, utilise le demi-Kelly (plus conservateur).
        cvar_safety_factor: multiplicateur sur le plafond CVaR (ex. 0.5 = doublement conservateur).

    Raises:
        ValueError: si un paramètre est invalide.
    """

    def __init__(
        self,
        max_kelly_fraction: float = 0.25,
        max_position_size: float = 1.0,
        min_position_size: float = 0.01,
        kelly_half: bool = True,
        cvar_safety_factor: float = 1.0,
    ) -> None:
        if not (0.0 < max_kelly_fraction <= 1.0):
            raise ValueError(f"max_kelly_fraction doit être dans (0, 1], reçu: {max_kelly_fraction}")
        if not (0.0 < max_position_size <= 1.0):
            raise ValueError(f"max_position_size doit être dans (0, 1], reçu: {max_position_size}")
        if min_position_size < 0:
            raise ValueError(f"min_position_size doit être >= 0, reçu: {min_position_size}")
        if cvar_safety_factor <= 0:
            raise ValueError(f"cvar_safety_factor doit être > 0, reçu: {cvar_safety_factor}")

        self.max_kelly_fraction = max_kelly_fraction
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.kelly_half = kelly_half
        self.cvar_safety_factor = cvar_safety_factor

    def _compute_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """Kelly Criterion classique (fraction f*).

        Returns:
            Kelly brut (peut être négatif → pas de trade).
        """
        if avg_win <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0

        loss_rate = 1.0 - win_rate
        # f* = (p * b - q) / b  où b = avg_win/avg_loss
        if avg_loss <= 0:
            return 0.0

        b = avg_win / avg_loss
        kelly_f = (win_rate * b - loss_rate) / b

        if self.kelly_half:
            kelly_f = kelly_f / 2.0

        return kelly_f

    def _compute_cvar_cap(
        self,
        cvar: float,
        portfolio_value: float,
    ) -> float:
        """Plafond de position basé sur le CVaR (perte attendue en extrême).

        On veut que la perte maximale attendue (CVaR en $) ne dépasse pas
        une fraction du portefeuille.

        Returns:
            Fraction max [0, 1] basée sur le CVaR.
        """
        if portfolio_value <= 0 or cvar <= 0:
            return 1.0  # pas de contrainte CVaR

        # CVaR est en valeur absolue (perte en $)
        cvar_fraction = cvar / portfolio_value
        cap = max(0.0, 1.0 - cvar_fraction * self.cvar_safety_factor)
        return min(cap, 1.0)

    def compute(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        cvar: float = 0.0,
        portfolio_value: float = 0.0,
    ) -> SizingResult:
        """Calcule la taille de position optimale.

        Args:
            win_rate:        taux de victoire des trades [0, 1].
            avg_win:         gain moyen par trade gagnant (en $ ou %).
            avg_loss:        perte moyenne par trade perdant (en $ ou %, valeur positive).
            cvar:            CVaR 95% en valeur absolue (0 = non disponible).
            portfolio_value: valeur totale du portefeuille (0 = non disponible).

        Returns:
            SizingResult avec la taille recommandée et les détails du calcul.
        """
        kelly_f = self._compute_kelly(win_rate, avg_win, avg_loss)
        kelly_capped = max(0.0, min(kelly_f, self.max_kelly_fraction))

        cvar_cap = self._compute_cvar_cap(cvar, portfolio_value)

        if kelly_capped <= 0:
            return SizingResult(
                size=0.0,
                kelly_f=round(kelly_f, 6),
                kelly_capped=0.0,
                cvar_cap=round(cvar_cap, 6),
                method="min_fallback",
                reason="Kelly négatif ou nul — pas de trade recommandé",
            )

        # Taille finale = min(kelly plafonné, CVaR cap, max absolu)
        if cvar > 0 and portfolio_value > 0:
            size = min(kelly_capped, cvar_cap, self.max_position_size)
            method = "kelly_cvar"
        else:
            size = min(kelly_capped, self.max_position_size)
            method = "kelly_only"

        # Applique la taille minimum si le résultat est positif mais trop faible
        if 0 < size < self.min_position_size:
            size = self.min_position_size

        return SizingResult(
            size=round(size, 6),
            kelly_f=round(kelly_f, 6),
            kelly_capped=round(kelly_capped, 6),
            cvar_cap=round(cvar_cap, 6),
            method=method,
            reason=(
                f"Kelly({'½' if self.kelly_half else '1x'})={kelly_f:.3f} "
                f"→ capped={kelly_capped:.3f} | CVaR_cap={cvar_cap:.3f} "
                f"→ size={size:.3f}"
            ),
        )

    def as_dict(self, result: "SizingResult") -> dict:
        """Sérialise un SizingResult pour le dashboard."""
        return {
            "size": result.size,
            "kelly_f": result.kelly_f,
            "kelly_capped": result.kelly_capped,
            "cvar_cap": result.cvar_cap,
            "method": result.method,
            "reason": result.reason,
        }
