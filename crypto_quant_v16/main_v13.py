"""
main_v13.py — V13 Autonomous Continuous Trading Loop
  - Starts a persistent pool of distributed workers (default: 4)
  - Runs run_cycle() indefinitely using those workers across cycles
  - Workers are NOT recreated between cycles (zero overhead per cycle)
  - Stops cleanly on Ctrl+C
"""
import time
import sys

from core.orchestrator import (
    run_cycle,
    start_persistent_workers,
    stop_persistent_workers,
    CLUSTER_METRICS,
)

WORKER_COUNT = 4
SLEEP_SECONDS = 5          # pause between cycles
STRATEGY_COUNT = 100
TOP_K = 10


def run_autonomous(max_cycles: int = 0, sleep_seconds: int = SLEEP_SECONDS) -> None:
    """
    Run continuously.  Set max_cycles=0 for infinite loop.
    """
    print("[V13] Starting persistent worker pool ...")
    start_persistent_workers(count=WORKER_COUNT)
    print(f"[V13] Pool ready ({WORKER_COUNT} workers). Starting autonomous loop.")
    print("[V13] Press Ctrl+C to stop.\n")

    cycle = 0
    try:
        while True:
            cycle += 1
            if max_cycles and cycle > max_cycles:
                break

            print(f"[V13] === Cycle {cycle} ===")
            t0 = time.monotonic()
            result = run_cycle(
                strategy_count=STRATEGY_COUNT,
                top_k=TOP_K,
                use_distributed=True,
            )
            elapsed = time.monotonic() - t0

            best_sharpe = round(float(result["best_strategies"][0][1]), 4) if result["best_strategies"] else 0.0
            print(f"  Regime        : {result['regime']}")
            print(f"  Risk          : {result['risk']['status']}")
            print(f"  Orders        : {len(result['orders'])}")
            print(f"  Top Sharpe    : {best_sharpe}")
            print(f"  Cycle time    : {elapsed:.2f}s")
            print(f"  Tasks done    : {CLUSTER_METRICS['tasks_completed']}")
            print(f"  Avg BT time   : {CLUSTER_METRICS['avg_backtest_ms']:.1f}ms\n")

            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        print("\n[V13] Interrupted by user.")
    finally:
        print("[V13] Stopping workers ...")
        stop_persistent_workers()
        print(f"[V13] Done. Total cycles: {CLUSTER_METRICS['cycles']}, "
              f"Total tasks: {CLUSTER_METRICS['tasks_completed']}")


if __name__ == "__main__":
    # Optional: pass --cycles N as first arg for finite run
    max_c = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run_autonomous(max_cycles=max_c)
