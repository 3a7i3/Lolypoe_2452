"""Option P — Circuit Breaker / Kill Switch.

Coupe automatiquement le trading quand une ou plusieurs règles de
sécurité sont franchies :
  - perte journalière > daily_loss_limit
  - drawdown courant > drawdown_limit
  - pertes consécutives >= consecutive_losses

Chaque règle peut être désactivée en passant la valeur 0 ou inf.
``is_triggered()`` retourne True si AU MOINS une règle est franchie.
``reason()`` retourne le message explicatif pour le log / Telegram.
``reset_daily()`` remet à zéro les compteurs journaliers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class CircuitBreakerState:
    """État interne mutable du circuit breaker."""

    daily_loss: float = 0.0          # perte cumulée du jour (valeur positive = perte)
    consecutive_losses: int = 0       # trades perdants d'affilée
    total_trades: int = 0
    triggers_today: int = 0
    triggered: bool = False
    last_reason: str = ""


class CircuitBreaker:
    """Protège le capital en bloquant les trades quand les seuils sont dépassés.

    Args:
        daily_loss_limit: perte journalière max en fraction du capital
                          (ex. 0.05 = 5%). 0 ou inf pour désactiver.
        drawdown_limit:   drawdown max en fraction du capital
                          (ex. 0.15 = 15%). 0 ou inf pour désactiver.
        consecutive_losses: nombre de trades perdants d'affilée avant
                            blocage. 0 pour désactiver.

    Raises:
        ValueError: si une valeur invalide est passée (négative).
    """

    def __init__(
        self,
        daily_loss_limit: float = 0.05,
        drawdown_limit: float = 0.15,
        consecutive_losses: int = 3,
    ) -> None:
        if daily_loss_limit < 0:
            raise ValueError(f"daily_loss_limit doit être >= 0, reçu: {daily_loss_limit}")
        if drawdown_limit < 0:
            raise ValueError(f"drawdown_limit doit être >= 0, reçu: {drawdown_limit}")
        if consecutive_losses < 0:
            raise ValueError(f"consecutive_losses doit être >= 0, reçu: {consecutive_losses}")

        self.daily_loss_limit = daily_loss_limit
        self.drawdown_limit = drawdown_limit
        self.consecutive_losses_limit = consecutive_losses
        self._state = CircuitBreakerState()

    # ------------------------------------------------------------------
    # API principale
    # ------------------------------------------------------------------

    def is_triggered(
        self,
        current_drawdown_pct: float = 0.0,
        realized_pnl_today: float = 0.0,
        initial_balance: float = 100_000.0,
    ) -> bool:
        """Évalue toutes les règles et retourne True si le breaker est déclenché.

        Args:
            current_drawdown_pct: drawdown courant en % (ex. 8.5 = 8.5%).
            realized_pnl_today:   PnL réalisé du jour (négatif = perte).
            initial_balance:      capital initial pour calculer la perte relative.
        """
        reasons: list[str] = []

        # Règle 1 : perte journalière
        if self.daily_loss_limit > 0 and initial_balance > 0:
            daily_loss_frac = -realized_pnl_today / initial_balance
            if daily_loss_frac > self.daily_loss_limit:
                reasons.append(
                    f"perte journalière {daily_loss_frac:.1%} > limite {self.daily_loss_limit:.1%}"
                )

        # Règle 2 : drawdown
        if self.drawdown_limit > 0:
            dd_frac = current_drawdown_pct / 100.0
            if dd_frac > self.drawdown_limit:
                reasons.append(
                    f"drawdown {current_drawdown_pct:.1f}% > limite {self.drawdown_limit:.1%}"
                )

        # Règle 3 : pertes consécutives
        if (
            self.consecutive_losses_limit > 0
            and self._state.consecutive_losses >= self.consecutive_losses_limit
        ):
            reasons.append(
                f"{self._state.consecutive_losses} pertes consécutives >= limite {self.consecutive_losses_limit}"
            )

        if reasons:
            self._state.triggered = True
            self._state.triggers_today += 1
            self._state.last_reason = " | ".join(reasons)
            return True

        self._state.triggered = False
        self._state.last_reason = ""
        return False

    def record_trade_result(self, pnl: float) -> None:
        """Enregistre le résultat d'un trade pour suivre les pertes consécutives.

        Args:
            pnl: PnL du trade (positif = gain, négatif = perte).
        """
        self._state.total_trades += 1
        if pnl < 0:
            self._state.consecutive_losses += 1
        else:
            self._state.consecutive_losses = 0  # reset sur un gain

    def reset_daily(self) -> None:
        """Remet à zéro les compteurs journaliers (à appeler à minuit)."""
        self._state.daily_loss = 0.0
        self._state.triggers_today = 0
        self._state.triggered = False
        self._state.last_reason = ""

    def reset_consecutive(self) -> None:
        """Remet à zéro le compteur de pertes consécutives."""
        self._state.consecutive_losses = 0

    def reason(self) -> str:
        """Retourne la raison du dernier déclenchement (vide si OK)."""
        return self._state.last_reason

    def status(self) -> dict[str, object]:
        """Résumé de l'état pour le dashboard."""
        return {
            "triggered": self._state.triggered,
            "reason": self._state.last_reason,
            "consecutive_losses": self._state.consecutive_losses,
            "triggers_today": self._state.triggers_today,
            "total_trades_recorded": self._state.total_trades,
            "limits": {
                "daily_loss_limit": self.daily_loss_limit,
                "drawdown_limit": self.drawdown_limit,
                "consecutive_losses_limit": self.consecutive_losses_limit,
            },
        }
