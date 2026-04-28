"""Options S+T — Stop Loss / Take Profit + Trailing Stop.

Gère les niveaux SL/TP par position ouverte et déclenche automatiquement
les ordres de sortie dans la boucle principale.

Modes supportés :
  - Fixe (pourcentage) : ``set_levels(symbol, entry, sl_pct, tp_pct)``
  - ATR-based         : ``set_levels_atr(symbol, entry, atr, sl_mult, tp_mult)``
  - Trailing stop     : activé via ``trailing_pct``

Workflow dans la boucle principale :
    1. Après un BUY → ``sl_manager.set_levels(symbol, price, ...)``
    2. Début cycle  → ``triggers = sl_manager.check_all(price_map)``
    3. Pour chaque trigger → forcer un ordre SELL

``check_all`` appelle aussi ``update_trailing`` avant de vérifier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TriggerType = Literal["stop_loss", "take_profit", "trailing_stop"]


@dataclass
class PositionLevel:
    """Niveaux SL/TP pour une position ouverte."""

    symbol: str
    entry_price: float
    sl_price: float                   # seuil de stop loss absolu
    tp_price: float | None            # seuil de take profit (None = désactivé)
    trailing_pct: float | None        # % trailing stop (None = désactivé)
    trailing_stop_price: float | None = field(default=None)  # calculé dynamiquement


@dataclass
class TriggerResult:
    """Résultat d'une vérification SL/TP."""

    triggered: bool
    trigger_type: TriggerType | None
    symbol: str
    trigger_price: float | None       # prix qui a déclenché
    current_price: float


class StopLossManager:
    """Suit les niveaux SL/TP/Trailing pour toutes les positions ouvertes.

    Args:
        default_sl_pct:    stop loss en % de l'entrée (ex. 0.05 = 5%).
        default_tp_pct:    take profit en % de l'entrée (ex. 0.10 = 10%).
                           0 ou None pour désactiver.
        trailing_pct:      trailing stop en % en dessous du pic (ex. 0.03 = 3%).
                           0 ou None pour désactiver.

    Raises:
        ValueError: si une valeur invalide est fournie.
    """

    def __init__(
        self,
        default_sl_pct: float = 0.05,
        default_tp_pct: float = 0.10,
        trailing_pct: float | None = None,
    ) -> None:
        if default_sl_pct < 0:
            raise ValueError(f"default_sl_pct doit être >= 0, reçu: {default_sl_pct}")
        if default_tp_pct is not None and default_tp_pct < 0:
            raise ValueError(f"default_tp_pct doit être >= 0, reçu: {default_tp_pct}")
        if trailing_pct is not None and trailing_pct < 0:
            raise ValueError(f"trailing_pct doit être >= 0, reçu: {trailing_pct}")

        self.default_sl_pct = default_sl_pct
        self.default_tp_pct = default_tp_pct
        self.trailing_pct = trailing_pct

        self._levels: dict[str, PositionLevel] = {}

    # ------------------------------------------------------------------
    # Configuration des niveaux
    # ------------------------------------------------------------------

    def set_levels(
        self,
        symbol: str,
        entry_price: float,
        sl_pct: float | None = None,
        tp_pct: float | None = None,
        trailing_pct: float | None = None,
    ) -> PositionLevel:
        """Enregistre les niveaux SL/TP pour une position.

        Args:
            symbol:      identifiant de l'actif.
            entry_price: prix d'entrée du trade.
            sl_pct:      stop loss % (défaut = ``default_sl_pct``).
            tp_pct:      take profit % (défaut = ``default_tp_pct``).
                         0 ou None pour désactiver le TP.
            trailing_pct: trailing stop % (défaut = ``trailing_pct`` de l'instance).

        Returns:
            PositionLevel enregistré.
        """
        if entry_price <= 0:
            raise ValueError(f"entry_price doit être > 0, reçu: {entry_price}")

        _sl = sl_pct if sl_pct is not None else self.default_sl_pct
        _tp = tp_pct if tp_pct is not None else self.default_tp_pct
        _trail = trailing_pct if trailing_pct is not None else self.trailing_pct

        sl_price = entry_price * (1.0 - _sl)
        tp_price = (entry_price * (1.0 + _tp)) if _tp and _tp > 0 else None

        # Prix de départ du trailing stop = entry - trailing_pct
        trailing_stop_price: float | None = None
        if _trail and _trail > 0:
            trailing_stop_price = entry_price * (1.0 - _trail)

        level = PositionLevel(
            symbol=symbol,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            trailing_pct=_trail if _trail and _trail > 0 else None,
            trailing_stop_price=trailing_stop_price,
        )
        self._levels[symbol] = level
        return level

    def set_levels_atr(
        self,
        symbol: str,
        entry_price: float,
        atr: float,
        sl_multiplier: float = 2.0,
        tp_multiplier: float = 4.0,
        trailing_pct: float | None = None,
    ) -> PositionLevel:
        """Niveaux SL/TP basés sur l'ATR (Average True Range).

        Args:
            symbol:        identifiant de l'actif.
            entry_price:   prix d'entrée.
            atr:           ATR courant (en unité de prix).
            sl_multiplier: distance SL = ATR × sl_multiplier.
            tp_multiplier: distance TP = ATR × tp_multiplier.
            trailing_pct:  trailing stop % (optionnel).

        Raises:
            ValueError: si atr <= 0.
        """
        if atr <= 0:
            raise ValueError(f"atr doit être > 0, reçu: {atr}")
        if sl_multiplier <= 0:
            raise ValueError(f"sl_multiplier doit être > 0, reçu: {sl_multiplier}")

        sl_pct = (atr * sl_multiplier) / entry_price
        tp_pct = (atr * tp_multiplier) / entry_price if tp_multiplier > 0 else 0.0
        return self.set_levels(symbol, entry_price, sl_pct=sl_pct, tp_pct=tp_pct, trailing_pct=trailing_pct)

    # ------------------------------------------------------------------
    # Vérification
    # ------------------------------------------------------------------

    def update_trailing(self, symbol: str, current_price: float) -> None:
        """Met à jour le trailing stop si le prix a monté depuis l'entrée.

        Appelé à chaque cycle pour chaque position ouverte.
        """
        level = self._levels.get(symbol)
        if level is None or level.trailing_pct is None:
            return

        new_trailing = current_price * (1.0 - level.trailing_pct)
        if (
            level.trailing_stop_price is None
            or new_trailing > level.trailing_stop_price
        ):
            level.trailing_stop_price = new_trailing

    def check(self, symbol: str, current_price: float) -> TriggerResult:
        """Vérifie si SL/TP/Trailing est déclenché pour un symbole.

        Met automatiquement à jour le trailing stop avant de vérifier.

        Args:
            symbol:        identifiant de l'actif.
            current_price: prix courant.

        Returns:
            TriggerResult (triggered=False si pas de niveau enregistré).
        """
        level = self._levels.get(symbol)
        if level is None:
            return TriggerResult(triggered=False, trigger_type=None, symbol=symbol,
                                 trigger_price=None, current_price=current_price)

        # Mise à jour du trailing avant vérification
        self.update_trailing(symbol, current_price)

        # 1. Stop Loss fixe
        if current_price <= level.sl_price:
            return TriggerResult(
                triggered=True,
                trigger_type="stop_loss",
                symbol=symbol,
                trigger_price=level.sl_price,
                current_price=current_price,
            )

        # 2. Trailing Stop (priorité avant TP car plus dynamique)
        if (
            level.trailing_stop_price is not None
            and current_price <= level.trailing_stop_price
            and current_price > level.sl_price  # évite le double-déclenchement
        ):
            return TriggerResult(
                triggered=True,
                trigger_type="trailing_stop",
                symbol=symbol,
                trigger_price=level.trailing_stop_price,
                current_price=current_price,
            )

        # 3. Take Profit
        if level.tp_price is not None and current_price >= level.tp_price:
            return TriggerResult(
                triggered=True,
                trigger_type="take_profit",
                symbol=symbol,
                trigger_price=level.tp_price,
                current_price=current_price,
            )

        return TriggerResult(triggered=False, trigger_type=None, symbol=symbol,
                             trigger_price=None, current_price=current_price)

    def check_all(self, price_map: dict[str, float]) -> list[TriggerResult]:
        """Vérifie tous les symboles suivis et retourne les déclenchements.

        Args:
            price_map: dict ``{symbol: current_price}`` des prix courants.

        Returns:
            Liste des ``TriggerResult`` où ``triggered=True``.
        """
        results: list[TriggerResult] = []
        for symbol in list(self._levels.keys()):
            price = price_map.get(symbol)
            if price is None:
                continue
            result = self.check(symbol, price)
            if result.triggered:
                results.append(result)
        return results

    # ------------------------------------------------------------------
    # Gestion des positions
    # ------------------------------------------------------------------

    def clear(self, symbol: str) -> None:
        """Supprime les niveaux d'un symbole (position fermée)."""
        self._levels.pop(symbol, None)

    def clear_all(self) -> None:
        """Supprime tous les niveaux."""
        self._levels.clear()

    def active_symbols(self) -> list[str]:
        """Retourne la liste des symboles avec des niveaux actifs."""
        return list(self._levels.keys())

    def get_level(self, symbol: str) -> PositionLevel | None:
        """Retourne les niveaux d'un symbole."""
        return self._levels.get(symbol)

    def status(self) -> dict[str, dict]:
        """Résumé de tous les niveaux actifs pour le dashboard."""
        result: dict[str, dict] = {}
        for sym, level in self._levels.items():
            result[sym] = {
                "entry_price": level.entry_price,
                "sl_price": round(level.sl_price, 6),
                "tp_price": round(level.tp_price, 6) if level.tp_price else None,
                "trailing_pct": level.trailing_pct,
                "trailing_stop_price": (
                    round(level.trailing_stop_price, 6)
                    if level.trailing_stop_price else None
                ),
            }
        return result
