from __future__ import annotations


def render_console_report(heartbeat: dict, best: dict | None, performance: dict, portfolio: dict[str, float], model_info: dict) -> str:
    best_line = "none"
    if best:
        s = best.get("strategy", {})
        best_line = f"{s.get('entry_indicator')}->{s.get('exit_indicator')} p={s.get('period')} sharpe={best.get('sharpe')} dd={best.get('drawdown')}"

    return (
        f"[Cycle {heartbeat['cycle']}] {heartbeat['status']} @ {heartbeat['timestamp']}\n"
        f"Best: {best_line}\n"
        f"Perf: sharpe={performance['avg_sharpe']} dd={performance['avg_drawdown']} pnl={performance['avg_pnl']}\n"
        f"Model: v{model_info.get('model_version', 0)} score={model_info.get('training_score', 0.0)}\n"
        f"Portfolio: {portfolio}\n"
    )
