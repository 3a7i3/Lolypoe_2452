from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from typing import List

from v26.runtime_profile import profile_from_env


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _build_commands(args: argparse.Namespace) -> tuple[List[str], List[str]]:
    dashboard_port = str(args.dashboard_port)
    symbol = args.symbol
    timeframe = args.timeframe
    exchange = args.exchange
    poll = str(args.poll)
    profile = str(args.profile)

    dashboard_cmd = [
        sys.executable,
        "-m",
        "panel",
        "serve",
        "ui/quant_dashboard_v26.py",
        "--port",
        dashboard_port,
        "--show",
    ]

    alert_cmd = [
        sys.executable,
        "binance_alert_app.py",
        "--symbol",
        symbol,
        "--timeframe",
        timeframe,
        "--exchange",
        exchange,
        "--poll",
        poll,
        "--profile",
        profile,
    ]
    if args.no_telegram:
        alert_cmd.append("--no-telegram")

    return dashboard_cmd, alert_cmd


def parse_args() -> argparse.Namespace:
    _load_env_file()
    env_profile = profile_from_env()

    parser = argparse.ArgumentParser(description="Launch V30 full suite (dashboard + alerts)")
    parser.add_argument("--dashboard-port", type=int, default=int(_env_str("DASHBOARD_PORT", "5026")))
    parser.add_argument("--symbol", default=_env_str("ALERT_SYMBOL", "BTC/USDT"))
    parser.add_argument("--timeframe", default=_env_str("ALERT_TIMEFRAME", "1h"))
    parser.add_argument("--exchange", default=_env_str("ALERT_EXCHANGE", "binance"))
    parser.add_argument("--profile", default=str(env_profile["name"]), choices=["conservative", "balanced", "aggressive"])
    parser.add_argument("--poll", type=int, default=int(_env_str("ALERT_POLL_SECONDS", str(env_profile["poll_seconds"]))))
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram sending in alert process")
    parser.add_argument(
        "--detached",
        action="store_true",
        help="Start child processes and exit immediately",
    )
    parser.add_argument("--skip-healthcheck", action="store_true", help="Skip pre-launch healthcheck")
    parser.add_argument("--healthcheck-only", action="store_true", help="Run healthcheck and exit")
    parser.add_argument("--strict-healthcheck", action="store_true", help="Treat warnings as failures")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cwd = os.path.dirname(os.path.abspath(__file__))

    if not args.skip_healthcheck or args.healthcheck_only:
        health_cmd = [
            sys.executable,
            "healthcheck_v30.py",
            "--dashboard-port",
            str(args.dashboard_port),
            "--symbol",
            args.symbol,
            "--timeframe",
            args.timeframe,
            "--exchange",
            args.exchange,
            "--profile",
            str(args.profile),
        ]
        if args.strict_healthcheck:
            health_cmd.append("--strict")

        print("[INFO] Running V30 healthcheck...")
        health = subprocess.run(health_cmd, cwd=cwd)
        if health.returncode != 0:
            print("[ERROR] Healthcheck failed. Fix issues or use --skip-healthcheck.")
            sys.exit(health.returncode)
        print("[OK] Healthcheck passed.")

    if args.healthcheck_only:
        return

    dashboard_cmd, alert_cmd = _build_commands(args)

    print(f"[INFO] Launching V30 suite from {cwd}")
    print(f"[INFO] Dashboard: http://localhost:{args.dashboard_port}/quant_dashboard_v26")

    creationflags = 0
    if os.name == "nt" and args.detached:
        creationflags = subprocess.CREATE_NEW_CONSOLE

    dash_proc = subprocess.Popen(dashboard_cmd, cwd=cwd, creationflags=creationflags)
    time.sleep(2)
    alert_proc = subprocess.Popen(alert_cmd, cwd=cwd, creationflags=creationflags)

    print(f"[OK] Dashboard PID={dash_proc.pid} | Alerts PID={alert_proc.pid}")

    if args.detached:
        return

    try:
        while True:
            if dash_proc.poll() is not None:
                print("[WARN] Dashboard process exited.")
                break
            if alert_proc.poll() is not None:
                print("[WARN] Alert process exited.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Stopping V30 suite...")
    finally:
        for proc in (dash_proc, alert_proc):
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        time.sleep(1)
        for proc in (dash_proc, alert_proc):
            if proc.poll() is None:
                try:
                    if os.name == "nt":
                        proc.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        proc.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
