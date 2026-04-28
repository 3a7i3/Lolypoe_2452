"""Option Y — HTML Reporter.

Génère un rapport HTML autonome des performances du système
(equity curve, trades, métriques clés) sans dépendance externe.

Le rapport est écrit dans un fichier local lisible dans n'importe quel
navigateur, et peut aussi être retourné comme chaîne HTML.

Workflow dans main_v91.py :
    reporter = HtmlReporter(output_dir="reports/")
    if cycle % cfg.report_frequency == 0:
        path = reporter.generate(
            paper_state=paper_state,
            backtest_summary=backtest_summary,
            wfo_result=wfo_result,
            symbol=symbol,
            cycle=cycle,
        )
        print(f"📄 Rapport généré → {path}")
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Quant Hedge AI — Rapport Cycle {cycle}</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 20px; }}
    h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
    h2 {{ color: #79c0ff; margin-top: 30px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }}
    .card .label {{ font-size: 12px; color: #8b949e; text-transform: uppercase; }}
    .card .value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
    .positive {{ color: #3fb950; }}
    .negative {{ color: #f85149; }}
    .neutral {{ color: #e6edf3; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th {{ background: #21262d; color: #8b949e; padding: 8px 12px; text-align: left; font-size: 12px; text-transform: uppercase; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; font-size: 14px; }}
    tr:hover {{ background: #161b22; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
    .badge-green {{ background: #1f4f2a; color: #3fb950; }}
    .badge-red {{ background: #4f1f1f; color: #f85149; }}
    .badge-yellow {{ background: #4f3f1f; color: #d29922; }}
    footer {{ margin-top: 40px; font-size: 12px; color: #8b949e; border-top: 1px solid #30363d; padding-top: 10px; }}
  </style>
</head>
<body>
  <h1>🤖 Quant Hedge AI — Rapport Cycle {cycle}</h1>
  <p style="color:#8b949e">Généré le {timestamp} | Symbole : <strong>{symbol}</strong></p>

  <h2>📊 Métriques de performance</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Equity</div>
      <div class="value {equity_class}">${equity:.2f}</div>
    </div>
    <div class="card">
      <div class="label">PnL réalisé</div>
      <div class="value {pnl_class}">${realized_pnl:+.2f}</div>
    </div>
    <div class="card">
      <div class="label">Win Rate</div>
      <div class="value neutral">{win_rate:.1%}</div>
    </div>
    <div class="card">
      <div class="label">Drawdown max</div>
      <div class="value {dd_class}">{drawdown:.1%}</div>
    </div>
    <div class="card">
      <div class="label">Trades totaux</div>
      <div class="value neutral">{total_trades}</div>
    </div>
    <div class="card">
      <div class="label">Position courante</div>
      <div class="value neutral">{position:.4f}</div>
    </div>
  </div>

  <h2>🧪 Backtest Lab</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Stratégies testées</div>
      <div class="value neutral">{bt_strategy_count}</div>
    </div>
    <div class="card">
      <div class="label">Meilleur PnL</div>
      <div class="value {bt_pnl_class}">{bt_best_pnl:+.2%}</div>
    </div>
    <div class="card">
      <div class="label">Meilleur Sharpe</div>
      <div class="value neutral">{bt_best_sharpe:.3f}</div>
    </div>
    <div class="card">
      <div class="label">Drawdown max backtest</div>
      <div class="value {bt_dd_class}">{bt_max_drawdown:.1%}</div>
    </div>
    <div class="card">
      <div class="label">Source données</div>
      <div class="value neutral">{bt_data_mode}</div>
    </div>
  </div>

  <h2>📐 Walk-Forward Optimization</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Splits OOS</div>
      <div class="value neutral">{wfo_splits}</div>
    </div>
    <div class="card">
      <div class="label">Sharpe moyen OOS</div>
      <div class="value {wfo_sharpe_class}">{wfo_mean_sharpe:.3f}</div>
    </div>
    <div class="card">
      <div class="label">Stabilité</div>
      <div class="value neutral">{wfo_stability:.1%}</div>
    </div>
    <div class="card">
      <div class="label">Robustesse</div>
      <div class="value">{wfo_robust_badge}</div>
    </div>
  </div>

  <h2>📋 Données brutes (JSON)</h2>
  <details>
    <summary style="cursor:pointer; color:#79c0ff">Afficher / Masquer</summary>
    <pre style="background:#161b22; border:1px solid #30363d; padding:15px; border-radius:8px; overflow:auto; font-size:12px; margin-top:10px">{raw_json}</pre>
  </details>

  <footer>
    Quant Hedge AI v9.1 | Cycle {cycle} | {timestamp}
  </footer>
</body>
</html>
"""


class HtmlReporter:
    """Génère des rapports HTML de performance autonomes.

    Args:
        output_dir:  répertoire de sortie pour les fichiers HTML.
        keep_last_n: nombre de rapports à conserver (supprime les anciens, 0 = tous).

    Raises:
        ValueError: si output_dir est vide.
    """

    def __init__(
        self,
        output_dir: str = "reports/",
        keep_last_n: int = 10,
    ) -> None:
        if not output_dir:
            raise ValueError("output_dir ne peut pas être vide")
        self.output_dir = Path(output_dir)
        self.keep_last_n = keep_last_n

    def _ensure_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        paper_state: dict,
        backtest_summary: dict | None = None,
        wfo_result: dict | None = None,
        symbol: str = "BTC/USDT",
        cycle: int = 0,
        write_file: bool = True,
    ) -> str:
        """Génère le rapport HTML.

        Args:
            paper_state:       état du paper engine (equity, win_rate, etc.).
            backtest_summary:  résumé du BacktestLab.
            wfo_result:        résultat WFO.
            symbol:            symbole tradé.
            cycle:             numéro de cycle.
            write_file:        si True, écrit le fichier sur disque.

        Returns:
            Chemin absolu du fichier HTML (si write_file=True) ou contenu HTML.
        """
        bt = backtest_summary or {}
        wfo = wfo_result or {}

        equity = float(paper_state.get("equity", 0.0))
        realized_pnl = float(paper_state.get("realized_pnl", 0.0))
        win_rate = float(paper_state.get("win_rate", 0.0))
        drawdown = float(paper_state.get("drawdown", 0.0))
        total_trades = int(paper_state.get("total_trades", 0))
        position = float(paper_state.get("position", 0.0))

        wfo_robust = wfo.get("stability", 0) >= 0.6 and wfo.get("mean_sharpe", 0) >= 0.5
        wfo_robust_badge = (
            '<span class="badge badge-green">✅ ROBUSTE</span>' if wfo_robust
            else '<span class="badge badge-yellow">⚠️ FRAGILE</span>'
            if wfo.get("n_splits_used", 0) > 0
            else '<span class="badge badge-yellow">N/A</span>'
        )

        raw_data = {
            "cycle": cycle,
            "symbol": symbol,
            "paper_state": paper_state,
            "backtest_summary": bt,
            "wfo_result": wfo,
        }

        html = _HTML_TEMPLATE.format(
            cycle=cycle,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol=symbol,
            equity=equity,
            equity_class="positive" if equity >= 10_000 else "negative",
            realized_pnl=realized_pnl,
            pnl_class="positive" if realized_pnl >= 0 else "negative",
            win_rate=win_rate,
            drawdown=drawdown,
            dd_class="positive" if drawdown < 0.05 else ("negative" if drawdown > 0.15 else "neutral"),
            total_trades=total_trades,
            position=position,
            bt_strategy_count=bt.get("strategy_count", 0),
            bt_best_pnl=float(bt.get("best_pnl", 0.0)),
            bt_pnl_class="positive" if float(bt.get("best_pnl", 0.0)) >= 0 else "negative",
            bt_best_sharpe=float(bt.get("best_sharpe", 0.0)),
            bt_max_drawdown=float(bt.get("max_drawdown", 0.0)),
            bt_dd_class="positive" if float(bt.get("max_drawdown", 0.0)) < 0.05 else "negative",
            bt_data_mode=bt.get("data_mode", "synthetic"),
            wfo_splits=wfo.get("n_splits_used", 0),
            wfo_mean_sharpe=float(wfo.get("mean_sharpe", 0.0)),
            wfo_sharpe_class="positive" if float(wfo.get("mean_sharpe", 0.0)) > 0.5 else "negative",
            wfo_stability=float(wfo.get("stability", 0.0)),
            wfo_robust_badge=wfo_robust_badge,
            raw_json=json.dumps(raw_data, indent=2, default=str),
        )

        if not write_file:
            return html

        self._ensure_dir()
        filename = f"report_cycle_{cycle:06d}.html"
        path = self.output_dir / filename
        path.write_text(html, encoding="utf-8")

        # Nettoyage des anciens rapports
        if self.keep_last_n > 0:
            self._cleanup()

        return str(path.absolute())

    def _cleanup(self) -> None:
        """Supprime les rapports les plus anciens si > keep_last_n."""
        reports = sorted(self.output_dir.glob("report_cycle_*.html"))
        excess = len(reports) - self.keep_last_n
        for old in reports[:excess]:
            try:
                old.unlink()
            except OSError:
                pass

    def list_reports(self) -> list[str]:
        """Retourne la liste des rapports disponibles (chemins absolus)."""
        if not self.output_dir.exists():
            return []
        return [str(p.absolute()) for p in sorted(self.output_dir.glob("report_cycle_*.html"))]
