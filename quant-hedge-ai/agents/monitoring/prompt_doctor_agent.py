from __future__ import annotations

import json
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CreatePromptAgent:
    """Generate enhancement prompts and apply basic doctor corrections to strategy payloads."""

    def __init__(self) -> None:
        self.doctor_log: list[str] = []
        self.director_logs: list[dict[str, Any]] = []

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        """Try to parse float from scalar values, return None when parsing fails."""
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            candidate = value.strip().replace(",", ".")
            if not candidate:
                return None
            try:
                return float(candidate)
            except ValueError:
                return None
        return None

    def generate_prompt_payload(self) -> dict[str, Any]:
        """Build the structured prompt payload as a Python dictionary."""
        return {
            "action": "enhance_bot_platform_with_doctor",
            "parameters": {
                "integration": ["Telegram", "Multi-HF", "Copy Trading"],
                "features_to_add": [
                    "Auto-strategies ML cross-market",
                    "Behavioral sentiment analysis (Bull/Bear)",
                    "Intelligent personalized alerts",
                    "Interactive multi-agent dashboard",
                    "Dynamic auto risk management",
                    "Real-time backtesting and stress tests",
                    "Automatic correction by Bot Doctor for AI-generated errors",
                ],
                "ui_improvements": [
                    "Interactive financial charts",
                    "Customizable key indicators",
                    "Bull and Bear symbol icons",
                    "Visual and audio Telegram notifications",
                    "Doctor AI interface to track errors and corrections",
                ],
                "automation": [
                    "Multi-agent consensus for trade validation",
                    "Automatic PnL optimization",
                    "Auto-adjustment of risk limits",
                    "Bot Doctor supervision and correction of generated strategies",
                ],
                "doctor_ai": {
                    "role": "supervisor",
                    "tasks": [
                        "Identify inconsistencies in generated strategies",
                        "Correct prediction or logic errors",
                        "Validate and approve strategies before execution",
                        "Provide detailed feedback to improve AI learning",
                    ],
                    "interaction": "Can alert users via Telegram or dashboard",
                },
                "output": "Detailed prompt for generating new features and proactive correction for AI bot + Telegram",
            },
        }

    def generate_prompt(self) -> str:
        """Return the prompt payload as pretty-printed JSON."""
        return json.dumps(self.generate_prompt_payload(), indent=4)

    def _apply_doctor_corrections_impl(
        self,
        strategy_output: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        """Apply basic self-healing defaults when strategy values are missing or invalid."""
        corrected_strategy = deepcopy(strategy_output)
        current_issues: list[str] = []
        resolved_defaults = {
            "trade_signal": "HOLD",
            "allocation": 0.0,
            "risk_level": "medium",
        }
        if defaults:
            resolved_defaults.update(defaults)

        for key, value in strategy_output.items():
            is_invalid_str = isinstance(value, str) and value.strip().lower() in {"error", "invalid", "nan"}
            if value is None or is_invalid_str:
                default_value = resolved_defaults.get(key, "default_value")
                corrected_strategy[key] = default_value
                issue = f"Correction applied on {key}: {value!r} -> {default_value!r}"
                current_issues.append(issue)
                self.doctor_log.append(issue)

        trade_signal = corrected_strategy.get("trade_signal")
        if isinstance(trade_signal, str):
            normalized_signal = trade_signal.strip().upper()
            if normalized_signal in {"BUY", "SELL", "HOLD"}:
                corrected_strategy["trade_signal"] = normalized_signal
            else:
                corrected_strategy["trade_signal"] = str(resolved_defaults.get("trade_signal", "HOLD")).upper()
                issue = (
                    f"Correction applied on trade_signal: {trade_signal!r} -> "
                    f"{corrected_strategy['trade_signal']!r}"
                )
                current_issues.append(issue)
                self.doctor_log.append(issue)
        elif trade_signal is not None:
            corrected_strategy["trade_signal"] = str(resolved_defaults.get("trade_signal", "HOLD")).upper()
            issue = (
                f"Correction applied on trade_signal: {trade_signal!r} -> "
                f"{corrected_strategy['trade_signal']!r}"
            )
            current_issues.append(issue)
            self.doctor_log.append(issue)

        allocation = corrected_strategy.get("allocation")
        parsed_allocation = self._coerce_float(allocation)
        if parsed_allocation is None:
            fallback_allocation = self._coerce_float(resolved_defaults.get("allocation"))
            corrected_strategy["allocation"] = 0.0 if fallback_allocation is None else fallback_allocation
            issue = f"Correction applied on allocation: {allocation!r} -> {corrected_strategy['allocation']!r}"
            current_issues.append(issue)
            self.doctor_log.append(issue)
        else:
            bounded_allocation = min(1.0, max(0.0, parsed_allocation))
            corrected_strategy["allocation"] = bounded_allocation
            if bounded_allocation != parsed_allocation:
                issue = f"Correction applied on allocation: {parsed_allocation!r} -> {bounded_allocation!r}"
                current_issues.append(issue)
                self.doctor_log.append(issue)

        risk_level = corrected_strategy.get("risk_level")
        if isinstance(risk_level, str):
            normalized_risk = risk_level.strip().lower()
            if normalized_risk in {"low", "medium", "high"}:
                corrected_strategy["risk_level"] = normalized_risk
            else:
                corrected_strategy["risk_level"] = "medium"
                issue = f"Correction applied on risk_level: {risk_level!r} -> 'medium'"
                current_issues.append(issue)
                self.doctor_log.append(issue)
        elif risk_level is not None:
            corrected_strategy["risk_level"] = "medium"
            issue = f"Correction applied on risk_level: {risk_level!r} -> 'medium'"
            current_issues.append(issue)
            self.doctor_log.append(issue)

        return corrected_strategy, current_issues

    def apply_doctor_corrections(
        self,
        strategy_output: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Apply basic self-healing defaults and return only corrected strategy."""
        corrected_strategy, _ = self._apply_doctor_corrections_impl(strategy_output, defaults=defaults)
        return corrected_strategy

    def apply_doctor_corrections_with_issues(
        self,
        strategy_output: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        """Apply corrections and return both corrected strategy and issues from this cycle."""
        return self._apply_doctor_corrections_impl(strategy_output, defaults=defaults)

    def simulate_telegram_alerts(
        self,
        user_id: int | str,
        strategy_output: dict[str, Any],
        defaults: dict[str, Any] | None = None,
        send_func: Any | None = None,
    ) -> dict[str, Any]:
        """Apply corrections then emit simulated Telegram alerts for this cycle only."""
        corrected, issues = self.apply_doctor_corrections_with_issues(
            strategy_output,
            defaults=defaults,
        )

        for issue in issues:
            message = f"[Bot Doctor ALERT] {issue} for user {user_id}"
            if send_func is not None:
                send_func(user_id, message)
            else:
                self.send_telegram_message(user_id, message)

        return corrected

    def send_telegram_message(self, user_id: int | str, message: str) -> None:
        """Simulate Telegram delivery (replace with real Telegram API in production)."""
        print(f"Telegram message sent to {user_id}: {message}")

    def run_realtime_demo(
        self,
        user_id: int | str,
        strategies: list[dict[str, Any]],
        delay_seconds: float = 2.0,
        send_func: Any | None = None,
    ) -> list[dict[str, Any]]:
        """Run a simple real-time simulation loop and return corrected strategy snapshots."""
        corrected_strategies: list[dict[str, Any]] = []
        for strategy in strategies:
            corrected = self.simulate_telegram_alerts(user_id, strategy, send_func=send_func)
            corrected_strategies.append(corrected)
            time.sleep(max(0.0, float(delay_seconds)))
        return corrected_strategies

    def build_v26_compatible_report(self, issues: list[str]) -> dict[str, Any]:
        """Build a report compatible with crypto_quant_v16/v26 Bot Doctor output shape."""
        findings: list[dict[str, Any]] = []

        for issue in issues:
            priority = 70 if "risk_level" in issue else 60
            findings.append(
                {
                    "severity": "warning",
                    "component": "bot_doctor",
                    "issue": issue,
                    "recommendation": "Review corrected fields before execution.",
                    "priority": priority,
                }
            )

        if not findings:
            findings.append(
                {
                    "severity": "info",
                    "component": "system",
                    "issue": "No critical anomalies detected",
                    "recommendation": "Maintain current configuration and continue monitoring.",
                    "priority": 10,
                }
            )

        findings_sorted = sorted(findings, key=lambda item: int(item["priority"]), reverse=True)
        avg_priority = sum(int(item["priority"]) for item in findings_sorted) / max(len(findings_sorted), 1)
        health_score = max(0.0, 100.0 - avg_priority * 0.35)

        return {
            "health_score": round(health_score, 1),
            "top_recommendation": findings_sorted[0]["recommendation"],
            "findings": findings_sorted,
            "issues_count": len(issues),
            "corrections_applied": len(issues),
        }

    def build_evolution_snapshot(self, cycle_issues: list[str]) -> dict[str, Any]:
        """Return lightweight trend metrics to track doctor evolution over time."""
        total = len(self.doctor_log)
        last_5 = self.doctor_log[-5:]
        risk_related = sum(1 for item in self.doctor_log if "risk_level" in item or "allocation" in item)
        signal_related = sum(1 for item in self.doctor_log if "trade_signal" in item)
        return {
            "cycle_corrections": len(cycle_issues),
            "total_corrections": total,
            "risk_related_corrections": risk_related,
            "signal_related_corrections": signal_related,
            "recent_corrections": last_5,
        }

    def director_panel(self) -> dict[str, Any]:
        """Return a moderator/director summary for operational visibility."""
        analysis = {
            "bot_status": "All bots running normally",
            "doctor_summary": self.doctor_log[-5:],
            "performance_metrics": {
                "strategies_executed": 42,
                "errors_corrected": len(self.doctor_log),
            },
        }
        self.director_logs.append(analysis)
        return analysis

    def developer_dashboard(self) -> dict[str, Any]:
        """Return a concise developer-focused snapshot."""
        return {
            "active_agents": ["BotDoctor1", "BotTrader2", "BotAI3"],
            "recent_corrections": self.doctor_log[-10:],
            "pending_alerts": len(self.doctor_log),
            "system_health": "Optimal",
        }

    def interactive_doctor_panel(self, filter_by: str | None = None) -> dict[str, Any]:
        """Return filtered doctor logs for lightweight interactive drill-downs."""
        normalized_filter = (filter_by or "").strip().lower()
        if normalized_filter == "user":
            filtered_logs = [log for log in self.doctor_log if "user" in log.lower() or "utilisateur" in log.lower()]
        elif normalized_filter == "strategy":
            filtered_logs = [log for log in self.doctor_log if "strategy" in log.lower()]
        else:
            filtered_logs = list(self.doctor_log)

        return {
            "filter": filter_by or "all",
            "filtered_logs_count": len(filtered_logs),
            "logs": filtered_logs[-10:],
        }

    def export_v26_report(
        self,
        report: dict[str, Any],
        output_dir: str,
        cycle: int,
    ) -> Path:
        """Export a V26-compatible report to a timestamped JSON file."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"bot_doctor_v26_cycle_{cycle}_{timestamp}.json"

        payload = {
            "cycle": int(cycle),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "report": report,
        }

        out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out_file

    def get_doctor_log(self) -> list[str]:
        """Return the list of corrections applied by the doctor."""
        return self.doctor_log


# Backward-compatible alias for earlier typo used in prototypes.
CreatePrompAgent = CreatePromptAgent
