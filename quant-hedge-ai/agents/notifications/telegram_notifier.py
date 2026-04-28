"""Option H — Alertes Telegram pour signaux de trading.

Envoie des notifications via l'API Bot Telegram.
Désactivé automatiquement si bot_token ou chat_id sont vides.

Activation :
    export V9_TELEGRAM_BOT_TOKEN="123456:ABC..."
    export V9_TELEGRAM_CHAT_ID="@moncanal"   # ou ID numérique

Cooldown par défaut : 60s par type d'alerte (évite le flood).
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
_DEFAULT_COOLDOWN = 60.0  # secondes entre deux alertes du même type


class TelegramNotifier:
    """Client léger Telegram pour alertes de trading.

    Parameters
    ----------
    bot_token:
        Token du bot Telegram (format ``123456:ABCdef...``).
        Vide = notificateur désactivé.
    chat_id:
        ID du chat ou nom du canal (ex: ``@moncanal`` ou ``-100123456``).
        Vide = notificateur désactivé.
    cooldown_seconds:
        Délai minimum (secondes) entre deux alertes du même type.
        Empêche le flood si les cycles sont rapides.
    """

    def __init__(
        self,
        bot_token: str = "",
        chat_id: str = "",
        cooldown_seconds: float = _DEFAULT_COOLDOWN,
    ) -> None:
        self._token = bot_token.strip()
        self._chat_id = chat_id.strip()
        self._cooldown = cooldown_seconds
        self._last_sent: dict[str, float] = {}  # {alert_key: timestamp}

        if self.enabled:
            logger.info(
                "TelegramNotifier: activé (chat_id=%s, cooldown=%.0fs)",
                self._chat_id,
                self._cooldown,
            )
        else:
            logger.debug("TelegramNotifier: désactivé (token ou chat_id manquant)")

    @property
    def enabled(self) -> bool:
        """True si le notificateur est configuré et peut envoyer des messages."""
        return bool(self._token and self._chat_id)

    def _on_cooldown(self, key: str) -> bool:
        """Retourne True si l'alerte `key` est encore en cooldown."""
        last = self._last_sent.get(key, 0.0)
        return (time.monotonic() - last) < self._cooldown

    def send(self, text: str, alert_key: str = "generic") -> bool:
        """Envoie un message texte brut.

        Parameters
        ----------
        text:
            Message à envoyer (Markdown autorisé).
        alert_key:
            Clé de déduplication pour le cooldown (ex: ``"buy_signal"``).

        Returns
        -------
        bool
            True si le message a été envoyé, False sinon (désactivé, cooldown, erreur).
        """
        if not self.enabled:
            return False
        if self._on_cooldown(alert_key):
            logger.debug("TelegramNotifier: cooldown actif pour '%s'", alert_key)
            return False

        url = _TELEGRAM_API.format(token=self._token)
        payload: dict[str, Any] = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            import requests  # import local pour ne pas forcer la dépendance au module level

            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                self._last_sent[alert_key] = time.monotonic()
                logger.info("TelegramNotifier: message envoyé [%s]", alert_key)
                return True
            logger.warning(
                "TelegramNotifier: échec HTTP %d — %s", resp.status_code, resp.text[:200]
            )
        except Exception as exc:
            logger.warning("TelegramNotifier: erreur réseau (%s)", exc)
        return False

    def send_signal(
        self,
        action: str,
        symbol: str,
        price: float,
        score: float | None = None,
        data_source: str = "",
    ) -> bool:
        """Envoie une alerte signal de trading (BUY/SELL)."""
        if action.upper() == "HOLD":
            return False
        icon = "🟢" if action.upper() == "BUY" else "🔴"
        score_str = f" | score={score:.1f}" if score is not None else ""
        source_str = f" | source={data_source}" if data_source else ""
        text = (
            f"{icon} *{action.upper()} {symbol}*\n"
            f"Prix : `{price:,.2f}` USDT"
            f"{score_str}{source_str}"
        )
        return self.send(text, alert_key=f"signal_{action.lower()}")

    def send_whale_alert(self, alerts: list[str]) -> bool:
        """Envoie une alerte whale si la liste est non vide."""
        if not alerts:
            return False
        text = "🐋 *WHALE ALERT*\n" + "\n".join(f"  • {a}" for a in alerts[:5])
        if len(alerts) > 5:
            text += f"\n  …et {len(alerts) - 5} autre(s)"
        return self.send(text, alert_key="whale_alert")

    def send_health_alert(self, health_score: float, recommendation: str = "") -> bool:
        """Envoie une alerte si le score de santé est critique (< 50)."""
        if health_score >= 50:
            return False
        icon = "🔴" if health_score < 30 else "🟡"
        rec_str = f"\n💡 {recommendation}" if recommendation else ""
        text = (
            f"{icon} *ALERTE SANTÉ SYSTÈME*\n"
            f"Score : `{health_score:.0f}/100`{rec_str}"
        )
        return self.send(text, alert_key="health_alert")
