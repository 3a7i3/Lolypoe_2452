"""
Option AF — Moteur d'alertes Slack / Discord.

Envoie des notifications webhook lorsque des seuils critiques sont franchis
dans la boucle de trading V9.1 :
  - Drawdown > seuil warning ou critical
  - Circuit breaker déclenché
  - Nouvelle meilleure stratégie (amélioration Sharpe significative)
  - Pause / reprise de la boucle
  - Boucle terminée (résumé final)

Usage:
    from agents.alerts.alert_engine import AlertEngine
    engine = AlertEngine(slack_url="...", discord_url="...")
    engine.maybe_alert_drawdown(cycle=5, drawdown_pct=12.0, equity=95000.0)
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ── Niveaux d'alerte ──────────────────────────────────────────────────────────

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


_LEVEL_COLOR = {
    AlertLevel.INFO: 0x00D4AA,        # vert
    AlertLevel.WARNING: 0xF5A623,     # orange
    AlertLevel.CRITICAL: 0xE94560,    # rouge
}

_LEVEL_EMOJI = {
    AlertLevel.INFO: "🟢",
    AlertLevel.WARNING: "⚠️",
    AlertLevel.CRITICAL: "🔴",
}


# ── Dataclass alerte ──────────────────────────────────────────────────────────

@dataclass
class Alert:
    title: str
    message: str
    level: AlertLevel = AlertLevel.INFO
    fields: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# ── Moteur principal ──────────────────────────────────────────────────────────

class AlertEngine:
    """
    Envoie des alertes vers Slack et/ou Discord via webhooks HTTP.

    - File thread-safe + thread daemon worker pour ne pas bloquer la boucle
    - Cooldown anti-spam par type d'alerte
    - Retry automatique sur erreur réseau (max 2 tentatives)
    """

    def __init__(
        self,
        slack_url: str = "",
        discord_url: str = "",
        cooldown_s: int = 300,
        drawdown_warning_pct: float = 5.0,
        drawdown_critical_pct: float = 10.0,
        sharpe_improvement_threshold: float = 0.5,
        enabled: bool = True,
        max_queue_size: int = 100,
        http_timeout_s: float = 5.0,
        max_retries: int = 2,
    ) -> None:
        self.slack_url = slack_url.strip()
        self.discord_url = discord_url.strip()
        self.cooldown_s = cooldown_s
        self.drawdown_warning_pct = drawdown_warning_pct
        self.drawdown_critical_pct = drawdown_critical_pct
        self.sharpe_improvement_threshold = sharpe_improvement_threshold
        self.enabled = enabled
        self.http_timeout_s = http_timeout_s
        self.max_retries = max_retries

        self._last_sent: dict[str, float] = {}
        self._last_sent_lock = threading.Lock()
        self._queue: queue.Queue[Alert | None] = queue.Queue(maxsize=max_queue_size)
        self._best_sharpe_seen: float = 0.0
        self._last_dd_level: AlertLevel | None = None

        # Thread daemon worker — envoie les alertes sans bloquer la boucle
        self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="v91-alert-worker")
        self._worker.start()

    # ── API publique ───────────────────────────────────────────────────────────

    def send(self, alert: Alert) -> None:
        """Enfile une alerte (non-bloquant). Ignorée si queue pleine."""
        if not self.enabled:
            return
        if not (self.slack_url or self.discord_url):
            logger.debug("AlertEngine: aucun webhook configuré, alerte ignorée")
            return
        try:
            self._queue.put_nowait(alert)
        except queue.Full:
            logger.warning("AlertEngine: queue pleine, alerte ignorée: %s", alert.title)

    def maybe_alert_drawdown(self, cycle: int, drawdown_pct: float, equity: float) -> bool:
        """
        Envoie une alerte si le drawdown franchit un seuil (avec cooldown).
        Retourne True si une alerte a été envoyée.
        """
        if drawdown_pct >= self.drawdown_critical_pct:
            level = AlertLevel.CRITICAL
            key = "drawdown_critical"
        elif drawdown_pct >= self.drawdown_warning_pct:
            level = AlertLevel.WARNING
            key = "drawdown_warning"
        else:
            self._last_dd_level = None
            return False

        # Ne pas re-envoyer le même niveau si cooldown actif
        if self._last_dd_level == level and not self._cooldown_expired(key):
            return False

        self._last_dd_level = level
        self._mark_sent(key)
        self.send(Alert(
            title=f"{_LEVEL_EMOJI[level]} Drawdown {level.value.upper()} — Cycle {cycle}",
            message=f"Drawdown: **{drawdown_pct:.2f}%** | Equity: ${equity:,.0f}",
            level=level,
            fields={"Cycle": str(cycle), "Drawdown": f"{drawdown_pct:.2f}%", "Equity": f"${equity:,.0f}"},
        ))
        return True

    def maybe_alert_circuit_breaker(self, cycle: int, reason: str, equity: float) -> bool:
        """Alerte critique quand le circuit breaker se déclenche."""
        key = "circuit_breaker"
        if not self._cooldown_expired(key):
            return False
        self._mark_sent(key)
        self.send(Alert(
            title=f"🔴 Circuit Breaker déclenché — Cycle {cycle}",
            message=f"Raison: **{reason}** | Equity: ${equity:,.0f}",
            level=AlertLevel.CRITICAL,
            fields={"Cycle": str(cycle), "Raison": reason, "Equity": f"${equity:,.0f}"},
        ))
        return True

    def maybe_alert_new_best_strategy(self, cycle: int, strategy_type: str, sharpe: float) -> bool:
        """Alerte info si la meilleure stratégie s'améliore significativement."""
        if sharpe - self._best_sharpe_seen < self.sharpe_improvement_threshold:
            return False
        key = "new_best_strategy"
        if not self._cooldown_expired(key):
            return False
        self._best_sharpe_seen = sharpe
        self._mark_sent(key)
        self.send(Alert(
            title=f"🏆 Nouvelle meilleure stratégie — Cycle {cycle}",
            message=f"Type: **{strategy_type}** | Sharpe: **{sharpe:.3f}**",
            level=AlertLevel.INFO,
            fields={"Cycle": str(cycle), "Stratégie": strategy_type, "Sharpe": f"{sharpe:.3f}"},
        ))
        return True

    def alert_loop_paused(self, cycle: int) -> None:
        """Alerte info quand la boucle est mise en pause via l'API."""
        self.send(Alert(
            title=f"⏸ Boucle mise en pause — Cycle {cycle}",
            message="La boucle V9.1 a été mise en pause via l'API REST.",
            level=AlertLevel.INFO,
        ))

    def alert_loop_resumed(self, cycle: int) -> None:
        """Alerte info quand la boucle reprend."""
        self.send(Alert(
            title=f"▶️ Boucle reprise — Cycle {cycle}",
            message="La boucle V9.1 a repris après une pause.",
            level=AlertLevel.INFO,
        ))

    def alert_loop_finished(self, total_cycles: int, equity: float, pnl: float, best_sharpe: float) -> None:
        """Résumé final quand la boucle se termine."""
        self.send(Alert(
            title="🏁 Boucle terminée — Résumé V9.1",
            message=(
                f"Cycles: **{total_cycles}** | Equity finale: **${equity:,.0f}** | "
                f"PnL: **${pnl:+,.0f}** | Meilleur Sharpe: **{best_sharpe:.3f}**"
            ),
            level=AlertLevel.INFO,
            fields={
                "Cycles": str(total_cycles),
                "Equity": f"${equity:,.0f}",
                "PnL": f"${pnl:+,.0f}",
                "Sharpe": f"{best_sharpe:.3f}",
            },
        ))

    def flush(self, timeout_s: float = 10.0) -> None:
        """Attend que toutes les alertes en queue soient traitées (pour les tests/fin de boucle)."""
        # queue.join() bloque jusqu'à ce que tous les task_done() soient appelés
        joiner = threading.Thread(target=self._queue.join, daemon=True)
        joiner.start()
        joiner.join(timeout=timeout_s)

    def shutdown(self) -> None:
        """Arrête le worker proprement."""
        self._queue.put(None)  # sentinel
        self._worker.join(timeout=5.0)

    # ── Cooldown ───────────────────────────────────────────────────────────────

    def _cooldown_expired(self, key: str) -> bool:
        with self._last_sent_lock:
            last = self._last_sent.get(key, 0.0)
        return (time.time() - last) >= self.cooldown_s

    def _mark_sent(self, key: str) -> None:
        with self._last_sent_lock:
            self._last_sent[key] = time.time()

    # ── Worker thread ──────────────────────────────────────────────────────────

    def _worker_loop(self) -> None:
        while True:
            try:
                alert = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            if alert is None:
                break
            self._dispatch(alert)
            self._queue.task_done()

    def _dispatch(self, alert: Alert) -> None:
        """Envoie l'alerte vers Slack et/ou Discord."""
        if self.slack_url:
            self._send_slack(alert)
        if self.discord_url:
            self._send_discord(alert)

    # ── Slack ──────────────────────────────────────────────────────────────────

    def _build_slack_payload(self, alert: Alert) -> dict[str, Any]:
        color_hex = f"#{_LEVEL_COLOR[alert.level]:06X}"
        attachment: dict[str, Any] = {
            "color": color_hex,
            "title": alert.title,
            "text": alert.message,
            "footer": "Quant Hedge AI V9.1",
            "ts": int(alert.timestamp),
        }
        if alert.fields:
            attachment["fields"] = [
                {"title": k, "value": v, "short": True}
                for k, v in alert.fields.items()
            ]
        return {"attachments": [attachment]}

    def _send_slack(self, alert: Alert) -> None:
        payload = self._build_slack_payload(alert)
        self._http_post(self.slack_url, payload, source="Slack")

    # ── Discord ────────────────────────────────────────────────────────────────

    def _build_discord_payload(self, alert: Alert) -> dict[str, Any]:
        embed: dict[str, Any] = {
            "title": alert.title,
            "description": alert.message,
            "color": _LEVEL_COLOR[alert.level],
            "footer": {"text": "Quant Hedge AI V9.1"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(alert.timestamp)),
        }
        if alert.fields:
            embed["fields"] = [
                {"name": k, "value": v, "inline": True}
                for k, v in alert.fields.items()
            ]
        return {"embeds": [embed]}

    def _send_discord(self, alert: Alert) -> None:
        payload = self._build_discord_payload(alert)
        self._http_post(self.discord_url, payload, source="Discord")

    # ── HTTP ───────────────────────────────────────────────────────────────────

    def _http_post(self, url: str, payload: dict[str, Any], source: str) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "quant-hedge-ai/v91"},
            method="POST",
        )
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.http_timeout_s) as resp:
                    status = resp.status
                    if 200 <= status < 300:
                        logger.debug("AlertEngine: %s OK (HTTP %d) — %s", source, status, payload.get("attachments", payload.get("embeds", ""))[:1])
                        return
                    logger.warning("AlertEngine: %s HTTP %d (tentative %d)", source, status, attempt)
            except urllib.error.URLError as exc:
                logger.warning("AlertEngine: %s erreur réseau (tentative %d): %s", source, attempt, exc)
            except Exception as exc:
                logger.error("AlertEngine: %s erreur inattendue (tentative %d): %s", source, attempt, exc)
                break
            if attempt < self.max_retries:
                time.sleep(0.5 * attempt)
        logger.error("AlertEngine: %s — abandon après %d tentatives", source, self.max_retries)
