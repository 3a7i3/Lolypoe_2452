"""
Option AL — Notification Email SMTP (alternative aux webhooks Slack/Discord).

Envoie des alertes par email HTML via smtplib (stdlib — aucune dépendance externe).
Supporte Gmail (STARTTLS), SMTP classique SSL, et un mode dry-run pour les tests.

Usage :
    from agents.alerts.email_notifier import EmailNotifier, EmailConfig
    notifier = EmailNotifier(EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="bot@gmail.com",
        password="app-password",
        from_addr="bot@gmail.com",
        to_addrs=["trader@example.com"],
    ))
    notifier.send_alert(title="Drawdown critique", body="DD=15%", level="critical")
"""
from __future__ import annotations

import logging
import smtplib
import socket
import time
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.alerts.alert_engine import Alert, AlertEngine

logger = logging.getLogger(__name__)


# ── Couleurs par niveau ───────────────────────────────────────────────────────

_LEVEL_COLOR = {
    "info":     "#00d4aa",
    "warning":  "#f5a623",
    "critical": "#e94560",
}
_LEVEL_EMOJI = {
    "info":     "🟢",
    "warning":  "⚠️",
    "critical": "🔴",
}


# ── Dataclass configuration ───────────────────────────────────────────────────

@dataclass
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587                             # 587=STARTTLS, 465=SSL
    username: str = ""
    password: str = ""
    from_addr: str = ""
    to_addrs: list[str] = field(default_factory=list)
    use_tls: bool = True                             # STARTTLS ; False = SSL
    dry_run: bool = False                            # si True, n'envoie pas vraiment
    timeout_s: float = 10.0


# ── Notifier ─────────────────────────────────────────────────────────────────

class EmailNotifier:
    """
    Notificateur email HTML via smtplib.

    Aucune dépendance externe — utilise uniquement la bibliothèque standard Python.
    """

    def __init__(self, config: EmailConfig) -> None:
        self._cfg = config

    def is_configured(self) -> bool:
        """Retourne True si tous les champs nécessaires sont renseignés."""
        c = self._cfg
        return bool(c.smtp_host and c.username and c.from_addr and c.to_addrs)

    # ── Envois publics ────────────────────────────────────────────────────────

    def send_alert(
        self,
        title: str,
        body: str,
        level: str = "info",
        fields: dict[str, str] | None = None,
    ) -> bool:
        """Envoie une alerte email HTML. Retourne True si succès (ou dry_run)."""
        if not self.is_configured() and not self._cfg.dry_run:
            logger.debug("EmailNotifier: non configuré, alerte ignorée")
            return False
        html = self._build_html(title, body, level, fields or {})
        subject = f"{_LEVEL_EMOJI.get(level, '📧')} V9.1 — {title}"
        return self._send_smtp(subject, html)

    def send_summary(
        self,
        total_cycles: int,
        equity: float,
        pnl: float,
        best_sharpe: float,
    ) -> bool:
        """Envoie un résumé de fin de session."""
        body = (
            f"La boucle V9.1 s'est terminée après <strong>{total_cycles}</strong> cycles.<br>"
            f"Equity finale : <strong>${equity:,.0f}</strong> | "
            f"PnL : <strong>${pnl:+,.0f}</strong> | "
            f"Meilleur Sharpe : <strong>{best_sharpe:.3f}</strong>"
        )
        return self.send_alert(
            title=f"Résumé boucle — {total_cycles} cycles",
            body=body,
            level="info",
            fields={
                "Cycles": str(total_cycles),
                "Equity": f"${equity:,.0f}",
                "PnL": f"${pnl:+,.0f}",
                "Sharpe": f"{best_sharpe:.3f}",
            },
        )

    # ── Intégration AlertEngine ───────────────────────────────────────────────

    def attach_to_alert_engine(self, engine: "AlertEngine") -> None:
        """
        Monkey-patch l'AlertEngine pour aussi envoyer par email.
        Chaque alerte envoyée via l'engine sera également reçue par email.
        """
        original_dispatch = engine._dispatch

        def _patched_dispatch(alert: "Alert") -> None:
            original_dispatch(alert)
            level = alert.level.value if hasattr(alert.level, "value") else str(alert.level)
            self.send_alert(
                title=alert.title,
                body=alert.message,
                level=level,
                fields=alert.fields,
            )

        engine._dispatch = _patched_dispatch  # type: ignore[method-assign]
        logger.info("EmailNotifier: attaché à l'AlertEngine")

    # ── Construction HTML ─────────────────────────────────────────────────────

    def _build_html(
        self,
        title: str,
        body: str,
        level: str,
        fields: dict[str, str],
    ) -> str:
        color = _LEVEL_COLOR.get(level, "#00d4aa")
        emoji = _LEVEL_EMOJI.get(level, "📧")

        fields_html = ""
        if fields:
            rows = "".join(
                f'<tr><td style="padding:4px 12px;font-weight:bold;color:#888">{k}</td>'
                f'<td style="padding:4px 12px;color:#e0e0e0">{v}</td></tr>'
                for k, v in fields.items()
            )
            fields_html = f"""
            <table style="margin-top:16px;border-collapse:collapse;width:100%">
                {rows}
            </table>"""

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="background:#1a1a2e;font-family:Courier New,monospace;padding:0;margin:0">
  <div style="max-width:600px;margin:20px auto;background:#16213e;border-radius:8px;
              border-top:4px solid {color};overflow:hidden">
    <div style="padding:20px 24px;background:{color}22">
      <h2 style="color:{color};margin:0;font-size:18px">{emoji} {title}</h2>
    </div>
    <div style="padding:20px 24px;color:#e0e0e0;font-size:14px;line-height:1.6">
      {body}
      {fields_html}
    </div>
    <div style="padding:12px 24px;background:#0f3460;color:#888;font-size:11px;text-align:right">
      Quant Hedge AI V9.1
    </div>
  </div>
</body></html>"""

    # ── Envoi SMTP ────────────────────────────────────────────────────────────

    def _send_smtp(self, subject: str, html_body: str) -> bool:
        if self._cfg.dry_run:
            logger.info("EmailNotifier [dry-run]: subject=%r to=%s", subject, self._cfg.to_addrs)
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._cfg.from_addr
        msg["To"] = ", ".join(self._cfg.to_addrs)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        for attempt in range(1, 3):
            try:
                if self._cfg.use_tls:
                    with smtplib.SMTP(self._cfg.smtp_host, self._cfg.smtp_port,
                                      timeout=self._cfg.timeout_s) as smtp:
                        smtp.ehlo()
                        smtp.starttls()
                        smtp.ehlo()
                        if self._cfg.username:
                            smtp.login(self._cfg.username, self._cfg.password)
                        smtp.sendmail(self._cfg.from_addr, self._cfg.to_addrs, msg.as_string())
                else:
                    with smtplib.SMTP_SSL(self._cfg.smtp_host, self._cfg.smtp_port,
                                          timeout=self._cfg.timeout_s) as smtp:
                        if self._cfg.username:
                            smtp.login(self._cfg.username, self._cfg.password)
                        smtp.sendmail(self._cfg.from_addr, self._cfg.to_addrs, msg.as_string())
                logger.info("EmailNotifier: email envoyé — %r", subject)
                return True
            except (smtplib.SMTPException, socket.error, OSError) as exc:
                logger.warning("EmailNotifier: erreur tentative %d — %s", attempt, exc)
                if attempt < 2:
                    time.sleep(1.0)
        logger.error("EmailNotifier: abandon après 2 tentatives — %r", subject)
        return False
