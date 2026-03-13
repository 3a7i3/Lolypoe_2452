from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading
import time
from typing import Dict, List

import numpy as np

from agents.backtest_agent import backtest
from agents.execution_agent import execute_paper_orders
from agents.market_agent import collect_market_data
from agents.risk_agent import evaluate_risk
from agents.strategy_agent import generate_strategy
from distributed.task_queue import add_task
from distributed.worker import Worker, start_worker_thread
from quant.regime_detector import detect_regime
from services.portfolio_manager import optimize_portfolio

# ---------------------------------------------------------------------------
# Cluster-wide metrics (readable by the dashboard and main loop)
# ---------------------------------------------------------------------------
CLUSTER_METRICS: Dict[str, object] = {
    "workers_active": 0,
    "tasks_completed": 0,
    "avg_backtest_ms": 0.0,
    "cycles": 0,
    "last_best_sharpe": 0.0,
    "last_regime": "NORMAL",
    "last_risk": "OK",
}

# ---------------------------------------------------------------------------
# Persistent worker pool (optional – started by main_v13 continuous mode)
# ---------------------------------------------------------------------------
_PERSISTENT_WORKERS: List[Worker] = []
_PERSISTENT_THREADS: List[threading.Thread] = []
_pool_lock = threading.Lock()


def start_persistent_workers(count: int = 4) -> None:
    """Start long-lived worker threads that survive across run_cycle() calls."""
    global _PERSISTENT_WORKERS, _PERSISTENT_THREADS
    with _pool_lock:
        if _PERSISTENT_WORKERS:
            return  # already running
        for i in range(max(1, count)):
            worker = Worker(name=f"wp-{i+1}", handlers={"backtest": _backtest_handler})
            _PERSISTENT_WORKERS.append(worker)
            _PERSISTENT_THREADS.append(start_worker_thread(worker))
    print(f"[Pool] {count} persistent worker(s) started.")


def stop_persistent_workers() -> None:
    """Gracefully stop all persistent workers."""
    global _PERSISTENT_WORKERS, _PERSISTENT_THREADS
    with _pool_lock:
        for w in _PERSISTENT_WORKERS:
            w.stop()
        for t in _PERSISTENT_THREADS:
            t.join(timeout=1.0)
        _PERSISTENT_WORKERS.clear()
        _PERSISTENT_THREADS.clear()
    print("[Pool] Persistent workers stopped.")


def _build_price_series(market_data: List[Dict[str, float | str]]) -> List[float]:
    return [float(row["price"]) for row in market_data if "price" in row]


def _parallel_backtest(strategies: List[Dict[str, int | str]]) -> List[float]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(backtest, strategies))


def _backtest_handler(task: Dict[str, object]) -> float:
    strategy = task.get("strategy")
    if not isinstance(strategy, dict):
        return 0.0
    return backtest(strategy)


def _distributed_backtest(strategies: List[Dict[str, int | str]], worker_count: int = 4) -> List[float]:
    if not strategies:
        return []

    use_persistent = bool(_PERSISTENT_WORKERS)
    response_queue: "Queue[Dict[str, object]]" = Queue()
    local_workers: List[Worker] = []
    local_threads = []

    if use_persistent:
        # Re-register handler (in case pool was started before handler was defined)
        with _pool_lock:
            for w in _PERSISTENT_WORKERS:
                w.handlers["backtest"] = _backtest_handler
        active_count = len(_PERSISTENT_WORKERS)
    else:
        for i in range(max(1, worker_count)):
            worker = Worker(name=f"worker-{i+1}", handlers={"backtest": _backtest_handler})
            local_workers.append(worker)
            local_threads.append(start_worker_thread(worker))
        active_count = len(local_workers)

    CLUSTER_METRICS["workers_active"] = active_count
    t0 = time.monotonic()

    for task_id, strategy in enumerate(strategies):
        add_task(
            {
                "task_id": task_id,
                "type": "backtest",
                "strategy": strategy,
                "response_queue": response_queue,
            }
        )

    results_by_id: Dict[int, float] = {}
    for _ in range(len(strategies)):
        msg = response_queue.get(timeout=15.0)
        idx = int(msg["task_id"])
        score = float(msg["result"])
        results_by_id[idx] = score

    elapsed_ms = (time.monotonic() - t0) * 1000.0
    prev_avg = float(CLUSTER_METRICS["avg_backtest_ms"])
    prev_count = int(CLUSTER_METRICS["tasks_completed"])
    new_count = prev_count + len(strategies)
    CLUSTER_METRICS["avg_backtest_ms"] = (
        (prev_avg * prev_count + elapsed_ms) / new_count if new_count else elapsed_ms
    )
    CLUSTER_METRICS["tasks_completed"] = new_count

    if not use_persistent:
        for worker in local_workers:
            worker.stop()
        for thread in local_threads:
            thread.join(timeout=1.0)

    return [results_by_id[i] for i in range(len(strategies))]


def run_cycle(
    symbols: List[str] | None = None,
    strategy_count: int = 100,
    top_k: int = 10,
    use_distributed: bool = True,
) -> Dict[str, object]:
    symbols = symbols or [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
        "ADA/USDT", "AVAX/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT",
    ]

    market_data = collect_market_data(symbols)
    prices = _build_price_series(market_data)
    regime = detect_regime(prices)

    strategies = [generate_strategy() for _ in range(strategy_count)]
    if use_distributed:
        try:
            scores = _distributed_backtest(strategies, worker_count=4)
        except Exception:
            scores = _parallel_backtest(strategies)
    else:
        scores = _parallel_backtest(strategies)

    ranked = sorted(zip(strategies, scores), key=lambda x: x[1], reverse=True)
    best = ranked[:top_k]

    selected_symbols = [symbols[i % len(symbols)] for i in range(top_k)]
    allocation = optimize_portfolio(selected_symbols)

    synthetic_drawdown = float(max(0.0, np.random.normal(0.08, 0.04)))
    risk = evaluate_risk(synthetic_drawdown)

    trade_signals = [
        {"symbol": selected_symbols[i], "action": "BUY" if score > 0.3 else "SELL"}
        for i, (_, score) in enumerate(best)
    ]
    orders = execute_paper_orders(trade_signals, regime)

    # Update cluster-wide metrics for dashboard visibility
    best_sharpe = float(best[0][1]) if best else 0.0
    CLUSTER_METRICS["cycles"] = int(CLUSTER_METRICS["cycles"]) + 1
    CLUSTER_METRICS["last_best_sharpe"] = round(best_sharpe, 4)
    CLUSTER_METRICS["last_regime"] = regime
    CLUSTER_METRICS["last_risk"] = str(risk.get("status", "OK"))

    return {
        "regime": regime,
        "market_size": len(market_data),
        "best_strategies": best,
        "allocation": allocation,
        "risk": risk,
        "orders": orders,
    }
