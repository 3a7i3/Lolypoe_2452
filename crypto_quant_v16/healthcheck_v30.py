from __future__ import annotations

import argparse
import importlib
import json
import os
import socket
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import List

from v26.runtime_profile import resolve_profile


@dataclass
class CheckResult:
    name: str
    ok: bool
    level: str
    detail: str


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def _check_imports(modules: List[str]) -> List[CheckResult]:
    results: List[CheckResult] = []
    for mod in modules:
        try:
            importlib.import_module(mod)
            results.append(CheckResult(name=f"import:{mod}", ok=True, level="info", detail="ok"))
        except Exception as exc:
            results.append(CheckResult(name=f"import:{mod}", ok=False, level="error", detail=str(exc)))
    return results


def _run_alert_oneshot(root: str, symbol: str, timeframe: str, exchange: str, profile: str) -> CheckResult:
    cmd = [
        sys.executable,
        "binance_alert_app.py",
        "--oneshot",
        "--no-telegram",
        "--symbol",
        symbol,
        "--timeframe",
        timeframe,
        "--exchange",
        exchange,
        "--profile",
        profile,
    ]
    try:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=30)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            tail = output.strip().splitlines()[-1] if output.strip() else "ok"
            return CheckResult(name="alert_oneshot", ok=True, level="info", detail=tail)
        return CheckResult(name="alert_oneshot", ok=False, level="error", detail=output.strip()[:300] or "failed")
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="alert_oneshot",
            ok=False,
            level="warning",
            detail="oneshot timed out (network/exchange latency). Core checks still valid.",
        )
    except Exception as exc:
        return CheckResult(name="alert_oneshot", ok=False, level="error", detail=str(exc))


def run_checks(args: argparse.Namespace) -> List[CheckResult]:
    _load_env_file()

    root = os.path.dirname(os.path.abspath(__file__))
    results: List[CheckResult] = []

    # Core file checks
    must_exist = [
        "ui/quant_dashboard_v26.py",
        "binance_alert_app.py",
        "v26/bot_doctor.py",
        "launch_v30_full.py",
    ]
    for rel in must_exist:
        path = os.path.join(root, rel.replace("/", os.sep))
        ok = os.path.exists(path)
        results.append(CheckResult(name=f"file:{rel}", ok=ok, level="error" if not ok else "info", detail=path))

    # Imports
    results.extend(_check_imports(["panel", "plotly", "pandas", "numpy", "ccxt", "ta", "dotenv"]))

    # Env checks
    dashboard_port = int(os.getenv("DASHBOARD_PORT", str(args.dashboard_port)))
    alert_symbol = os.getenv("ALERT_SYMBOL", args.symbol)
    alert_timeframe = os.getenv("ALERT_TIMEFRAME", args.timeframe)
    alert_exchange = os.getenv("ALERT_EXCHANGE", args.exchange)
    alert_profile = os.getenv("ALERT_PROFILE", args.profile)

    results.append(
        CheckResult(
            name="env:alert_params",
            ok=bool(alert_symbol and alert_timeframe and alert_exchange),
            level="error" if not (alert_symbol and alert_timeframe and alert_exchange) else "info",
            detail=f"symbol={alert_symbol} timeframe={alert_timeframe} exchange={alert_exchange} profile={alert_profile}",
        )
    )

    profile = resolve_profile(alert_profile)
    results.append(
        CheckResult(
            name="env:profile",
            ok=True,
            level="info",
            detail=(
                f"{profile['name']} sl={profile['sl_pct']:.3f} tp={profile['tp_pct']:.3f} "
                f"min_regime_conf={profile['min_regime_conf']:.2f}"
            ),
        )
    )

    # Telegram is optional, warn only if one field is missing while the other exists.
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if bool(tg_token) ^ bool(tg_chat):
        results.append(
            CheckResult(
                name="env:telegram",
                ok=False,
                level="warning",
                detail="Provide both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, or leave both empty.",
            )
        )
    else:
        results.append(
            CheckResult(
                name="env:telegram",
                ok=True,
                level="info",
                detail="configured" if (tg_token and tg_chat) else "disabled (optional)",
            )
        )

    # Port status check: open port is not a hard error; launcher can still run if existing service is expected.
    port_open = _is_port_open("127.0.0.1", dashboard_port)
    results.append(
        CheckResult(
            name="port:dashboard",
            ok=True,
            level="warning" if port_open else "info",
            detail=f"port {dashboard_port} {'already in use' if port_open else 'available'}",
        )
    )

    # Smoke check for alert app
    results.append(_run_alert_oneshot(root, alert_symbol, alert_timeframe, alert_exchange, str(profile["name"])))

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Healthcheck for V30 suite")
    parser.add_argument("--dashboard-port", type=int, default=5026)
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--profile", default="balanced", choices=["conservative", "balanced", "aggressive"])
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_checks(args)

    if args.json:
        print(json.dumps([asdict(r) for r in results], ensure_ascii=True, indent=2))
    else:
        print("=== V30 Healthcheck ===")
        for r in results:
            status = "OK" if r.ok else "FAIL"
            print(f"[{status}] [{r.level.upper()}] {r.name}: {r.detail}")

    has_error = any((not r.ok and r.level == "error") for r in results)
    has_warning_fail = args.strict and any((not r.ok and r.level == "warning") for r in results)
    sys.exit(1 if (has_error or has_warning_fail) else 0)


if __name__ == "__main__":
    main()
