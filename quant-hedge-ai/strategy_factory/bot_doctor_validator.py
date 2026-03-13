from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidatorDecision:
    approved: bool
    health_score: float
    reason: str
    findings: list[dict]


class BotDoctorValidator:
    """Risk validator for strategy candidates following Bot Doctor style scoring."""

    def validate(self, result: dict) -> ValidatorDecision:
        sharpe = float(result.get("sharpe", 0.0))
        drawdown = float(result.get("drawdown", 1.0))
        win_rate = float(result.get("win_rate", 0.0))
        pnl = float(result.get("pnl", 0.0))

        findings: list[dict] = []
        score = 100.0

        if sharpe < 1.0:
            score -= 35
            findings.append({
                "severity": "critical",
                "component": "strategy_quality",
                "issue": f"Low Sharpe ({sharpe:.2f})",
                "recommendation": "Reject or retrain strategy",
            })
        elif sharpe < 1.5:
            score -= 20
            findings.append({
                "severity": "warning",
                "component": "strategy_quality",
                "issue": f"Moderate Sharpe ({sharpe:.2f})",
                "recommendation": "Reduce allocation",
            })

        if drawdown > 0.10:
            score -= 30
            findings.append({
                "severity": "critical" if drawdown > 0.15 else "warning",
                "component": "risk_engine",
                "issue": f"High drawdown ({drawdown:.2%})",
                "recommendation": "Apply tighter stop loss or reject",
            })
        elif drawdown > 0.05:
            score -= 15
            findings.append({
                "severity": "warning",
                "component": "risk_engine",
                "issue": f"Elevated drawdown ({drawdown:.2%})",
                "recommendation": "Reduce position size",
            })

        if win_rate < 0.45:
            score -= 20
            findings.append({
                "severity": "warning",
                "component": "execution",
                "issue": f"Low win rate ({win_rate:.1%})",
                "recommendation": "Recalibrate entry/exit conditions",
            })

        if pnl < 0:
            score -= 10
            findings.append({
                "severity": "warning",
                "component": "performance",
                "issue": f"Negative pnl ({pnl:.2f})",
                "recommendation": "Keep in sandbox only",
            })

        score = max(0.0, min(100.0, score))
        approved = score >= 50.0
        if approved:
            reason = "Approved by Bot Doctor Validator"
        else:
            reason = "Blocked by Bot Doctor Validator (health_score < 50)"

        return ValidatorDecision(
            approved=approved,
            health_score=score,
            reason=reason,
            findings=findings,
        )
