from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from v26.config import V26_CONFIG
from v26.dex_adapter import DEX_EXCHANGES, get_dex_route, probe_dex_live_anchor


def _collect_targets() -> List[Tuple[str, str]]:
    routing = V26_CONFIG.get("dex_routing", {}) if isinstance(V26_CONFIG, dict) else {}
    out: List[Tuple[str, str]] = []
    if isinstance(routing, dict):
        for exchange_name, pairs in routing.items():
            if str(exchange_name).lower() not in DEX_EXCHANGES:
                continue
            if not isinstance(pairs, dict):
                continue
            for symbol in pairs.keys():
                out.append((str(exchange_name).lower(), str(symbol)))

    if not out:
        fallback_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        out.extend(("uniswap", s) for s in fallback_symbols)
        out.extend(("hyperliquid", s) for s in fallback_symbols)
    return out


def _validate() -> Dict[str, object]:
    checks = []
    ok_count = 0

    for exchange_name, symbol in _collect_targets():
        route = get_dex_route(exchange_name, symbol)
        price, error = probe_dex_live_anchor(exchange_name, symbol)
        is_ok = price is not None and price > 0
        if is_ok:
            ok_count += 1

        checks.append(
            {
                "exchange": exchange_name,
                "symbol": symbol,
                "ok": is_ok,
                "price": round(float(price), 8) if is_ok else None,
                "error": "" if is_ok else error,
                "route": route,
            }
        )

    total = len(checks)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total,
            "ok": ok_count,
            "failed": max(0, total - ok_count),
            "health": "ok" if ok_count == total else ("partial" if ok_count > 0 else "down"),
        },
        "checks": checks,
    }


def _print_table(report: Dict[str, object]) -> None:
    checks = report.get("checks", [])
    if not isinstance(checks, list):
        return

    print("DEX Route Validation")
    print("=" * 72)
    print(f"UTC: {report.get('timestamp_utc', '')}")
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    print(
        "Summary: "
        f"total={summary.get('total', 0)} "
        f"ok={summary.get('ok', 0)} "
        f"failed={summary.get('failed', 0)} "
        f"health={summary.get('health', 'unknown')}"
    )
    print("-" * 72)
    for row in checks:
        if not isinstance(row, dict):
            continue
        ex = row.get("exchange", "")
        symbol = row.get("symbol", "")
        ok = row.get("ok", False)
        price = row.get("price")
        error = row.get("error", "")
        status = "OK" if ok else "FAIL"
        px_txt = f"{price}" if price is not None else "-"
        print(f"[{status}] {ex:12} {symbol:10} price={px_txt:>14} error={error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate configured DEX routing live anchors.")
    parser.add_argument("--json", action="store_true", help="Print report as JSON")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any route fails")
    parser.add_argument("--out", type=str, default="", help="Optional path to save JSON report")
    args = parser.parse_args()

    report = _validate()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_table(report)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved report: {out_path}")

    failed = int(report.get("summary", {}).get("failed", 0)) if isinstance(report.get("summary"), dict) else 1
    if args.strict and failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
