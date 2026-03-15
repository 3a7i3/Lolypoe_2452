import datetime

import os

class ReportGenerator:
    def __init__(self, patterns, hypotheses, recommendations, report_dir="reports"):
        self.patterns = patterns
        self.hypotheses = hypotheses
        self.recommendations = recommendations
        self.timestamp = datetime.datetime.utcnow().isoformat()
        self.report_dir = report_dir

    def generate(self, auto_send=True):
        # Placeholder pour visualisation (ex: matplotlib, plotly)
        visualizations = ["pattern_chart.png", "risk_score_plot.png"]
        # Audit trail
        audit = {
            "generated_at": self.timestamp,
            "pattern_count": len(self.patterns),
            "hypothesis_count": len(self.hypotheses),
            "recommendation_count": len(self.recommendations)
        }
        # Rapport enrichi
        report = {
            "patterns_detected": self.patterns,
            "research_hypotheses": self.hypotheses,
            "strategy_recommendations": self.recommendations,
            "explanations": self._explanations(),
            "visualizations": visualizations,
            "audit": audit
        }
        # Sauvegarde locale
        self._save_report(report)
        # Envoi automatique (placeholder)
        if auto_send:
            self._send_report(report)
        return report

    def _save_report(self, report):
        os.makedirs(self.report_dir, exist_ok=True)
        fname = os.path.join(self.report_dir, f"report_{self.timestamp.replace(':','-')}.json")
        try:
            import json
            with open(fname, "w") as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde rapport: {e}")

    def _send_report(self, report):
        # Placeholder: ici tu pourrais envoyer par email, Slack, Telegram, etc.
        print("[AIResearchAgent] Rapport envoyé automatiquement (placeholder)")

    def _explanations(self):
        exp = {}
        if self.patterns.get("liquidation_cluster"):
            exp["liquidation_cluster"] = "Un cluster de liquidations a été détecté, signalant un risque de squeeze ou de crash."
        if self.patterns.get("whale_activity"):
            exp["whale_activity"] = "Une activité inhabituelle de whales a été détectée (gros ordres)."
        if self.patterns.get("regime_shift"):
            exp["regime_shift"] = "Changement de régime de marché détecté (trend/momentum)."
        if self.patterns.get("anomaly"):
            exp["anomaly"] = "Anomalie de prix détectée (jump/drop inhabituel)."
        if not exp:
            exp["general"] = "Aucun pattern critique détecté."
        return exp
