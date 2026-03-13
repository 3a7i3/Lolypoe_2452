from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agents.monitoring.prompt_doctor_agent import CreatePrompAgent, CreatePromptAgent



def test_generate_prompt_returns_valid_json() -> None:
    agent = CreatePromptAgent()
    prompt_json = agent.generate_prompt()

    parsed = json.loads(prompt_json)
    assert parsed["action"] == "enhance_bot_platform_with_doctor"
    assert "parameters" in parsed
    assert "doctor_ai" in parsed["parameters"]



def test_apply_doctor_corrections_replaces_none_and_error() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": None, "allocation": "error", "risk_level": "medium"}

    corrected = agent.apply_doctor_corrections(strategy)

    assert corrected["trade_signal"] == "HOLD"
    assert corrected["allocation"] == 0.0
    assert corrected["risk_level"] == "medium"
    assert len(agent.get_doctor_log()) == 2



def test_apply_doctor_corrections_supports_custom_defaults() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": None, "allocation": "invalid", "risk_level": "high"}

    corrected = agent.apply_doctor_corrections(strategy, defaults={"trade_signal": "BUY", "allocation": 0.25})

    assert corrected["trade_signal"] == "BUY"
    assert corrected["allocation"] == 0.25



def test_apply_doctor_corrections_normalizes_unknown_risk_level() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": "BUY", "allocation": 0.15, "risk_level": "extreme"}

    corrected = agent.apply_doctor_corrections(strategy)

    assert corrected["risk_level"] == "medium"
    assert any("risk_level" in item for item in agent.get_doctor_log())



def test_apply_doctor_corrections_does_not_mutate_original() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": None, "allocation": "error", "risk_level": "medium"}

    _ = agent.apply_doctor_corrections(strategy)

    assert strategy["trade_signal"] is None
    assert strategy["allocation"] == "error"


def test_simulate_telegram_alerts_sends_only_current_cycle_issues() -> None:
    agent = CreatePromptAgent()
    sent_messages: list[str] = []

    def _collector(_user_id: int | str, message: str) -> None:
        sent_messages.append(message)

    strategy_one = {"trade_signal": None, "allocation": "error", "risk_level": "medium"}
    strategy_two = {"trade_signal": "BUY", "allocation": 0.2, "risk_level": "high"}

    corrected_one = agent.simulate_telegram_alerts(12345, strategy_one, send_func=_collector)
    corrected_two = agent.simulate_telegram_alerts(12345, strategy_two, send_func=_collector)

    assert corrected_one["trade_signal"] == "HOLD"
    assert corrected_one["allocation"] == 0.0
    assert corrected_two == strategy_two
    assert len(sent_messages) == 2
    assert all("Bot Doctor ALERT" in message for message in sent_messages)


def test_run_realtime_demo_returns_corrected_snapshots_without_sleep() -> None:
    agent = CreatePromptAgent()
    sent_messages: list[str] = []

    def _collector(_user_id: int | str, message: str) -> None:
        sent_messages.append(message)

    strategies = [
        {"trade_signal": None, "allocation": "error", "risk_level": "medium"},
        {"trade_signal": "BUY", "allocation": None, "risk_level": "high"},
    ]

    corrected = agent.run_realtime_demo(99, strategies, delay_seconds=0, send_func=_collector)

    assert len(corrected) == 2
    assert corrected[0]["trade_signal"] == "HOLD"
    assert corrected[1]["allocation"] == 0.0
    assert len(sent_messages) == 3


def test_build_v26_compatible_report_with_issues() -> None:
    agent = CreatePromptAgent()
    issues = [
        "Correction applied on allocation: None -> 0.0",
        "Correction applied on risk_level: 'extreme' -> 'medium'",
    ]

    report = agent.build_v26_compatible_report(issues)

    assert "health_score" in report
    assert "top_recommendation" in report
    assert len(report["findings"]) == 2
    assert report["findings"][0]["priority"] >= report["findings"][1]["priority"]


def test_build_v26_compatible_report_without_issues() -> None:
    agent = CreatePromptAgent()
    report = agent.build_v26_compatible_report([])

    assert report["findings"][0]["severity"] == "info"
    assert report["findings"][0]["component"] == "system"


def test_export_v26_report_writes_timestamped_json_file() -> None:
    agent = CreatePromptAgent()
    report = agent.build_v26_compatible_report(["Correction applied on allocation: None -> 0.0"])

    with tempfile.TemporaryDirectory() as tmp_dir:
        exported = agent.export_v26_report(report=report, output_dir=tmp_dir, cycle=7)

        assert isinstance(exported, Path)
        assert exported.exists()
        assert "bot_doctor_v26_cycle_7_" in exported.name

        payload = json.loads(exported.read_text(encoding="utf-8"))
        assert payload["cycle"] == 7
        assert "timestamp_utc" in payload
        assert payload["report"]["findings"][0]["component"] == "bot_doctor"


def test_apply_doctor_corrections_normalizes_signal_and_bounds_allocation() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": " buy ", "allocation": 1.75, "risk_level": " HIGH "}

    corrected = agent.apply_doctor_corrections(strategy)

    assert corrected["trade_signal"] == "BUY"
    assert corrected["allocation"] == 1.0
    assert corrected["risk_level"] == "high"
    assert any("allocation" in item for item in agent.get_doctor_log())


def test_apply_doctor_corrections_fixes_unknown_signal_and_string_allocation() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": "long", "allocation": "0,42", "risk_level": "medium"}

    corrected = agent.apply_doctor_corrections(strategy)

    assert corrected["trade_signal"] == "HOLD"
    assert corrected["allocation"] == 0.42


def test_build_evolution_snapshot_returns_expected_counters() -> None:
    agent = CreatePromptAgent()
    strategy = {"trade_signal": "???", "allocation": -0.5, "risk_level": "extreme"}
    _corrected, cycle_issues = agent.apply_doctor_corrections_with_issues(strategy)

    snapshot = agent.build_evolution_snapshot(cycle_issues)

    assert snapshot["cycle_corrections"] == len(cycle_issues)
    assert snapshot["total_corrections"] >= len(cycle_issues)
    assert snapshot["risk_related_corrections"] >= 1
    assert snapshot["signal_related_corrections"] >= 1
    assert isinstance(snapshot["recent_corrections"], list)


def test_director_panel_accumulates_entries() -> None:
    agent = CreatePromptAgent()
    _ = agent.apply_doctor_corrections({"trade_signal": None, "allocation": "error", "risk_level": "medium"})

    panel = agent.director_panel()

    assert panel["bot_status"]
    assert panel["performance_metrics"]["errors_corrected"] == len(agent.get_doctor_log())
    assert len(agent.director_logs) == 1


def test_developer_dashboard_reports_recent_corrections() -> None:
    agent = CreatePromptAgent()
    _ = agent.apply_doctor_corrections({"trade_signal": None, "allocation": "error", "risk_level": "medium"})

    dashboard = agent.developer_dashboard()

    assert "active_agents" in dashboard
    assert dashboard["pending_alerts"] == len(agent.get_doctor_log())
    assert isinstance(dashboard["recent_corrections"], list)


def test_interactive_doctor_panel_filters_by_strategy() -> None:
    agent = CreatePromptAgent()
    agent.doctor_log.extend(
        [
            "Correction applied on strategy_name: 'x' -> 'y'",
            "Correction applied on allocation: 2.0 -> 1.0",
        ]
    )

    panel = agent.interactive_doctor_panel(filter_by="strategy")

    assert panel["filter"] == "strategy"
    assert panel["filtered_logs_count"] == 1
    assert "strategy" in panel["logs"][0].lower()


def test_createprompagent_alias_works() -> None:
    alias_agent = CreatePrompAgent()
    assert isinstance(alias_agent, CreatePromptAgent)
