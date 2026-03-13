"""AI Evolution Engine — continuous self-improvement loop.

Lifecycle per cycle:
    1. Recall top strategies from memory for current regime
    2. Generate fresh candidates + seed from memory
    3. Evolve population (genetic crossover + mutation)
    4. Backtest all candidates
    5. Bot Doctor validation gate
    6. Save winners to regime-aware memory
    7. Report generation stats

Usage:
    engine = EvolutionEngine()
    report = engine.run_cycle(cycle=1, regime="bull_trend", candles=candles)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agents.strategy.strategy_generator import StrategyGenerator
from agents.strategy.genetic_optimizer import GeneticOptimizer
from agents.quant.backtest_lab import BacktestLab
from ai_evolution.strategy_memory import StrategyMemoryStore

logger = logging.getLogger(__name__)


@dataclass
class EvolutionReport:
    """Snapshot of one evolution cycle."""

    cycle: int = 0
    regime: str = "unknown"
    candidates_generated: int = 0
    candidates_from_memory: int = 0
    candidates_evolved: int = 0
    backtests_run: int = 0
    best_sharpe: float = 0.0
    best_strategy: dict = field(default_factory=dict)
    avg_sharpe: float = 0.0
    saved_to_memory: int = 0
    doctor_blocked: int = 0
    generation: int = 0

    def as_dict(self) -> dict:
        strat = self.best_strategy
        best_name = (
            f"{strat.get('entry_indicator', '?')} -> {strat.get('exit_indicator', '?')}"
            if strat else "none"
        )
        return {
            "cycle": self.cycle,
            "regime": self.regime,
            "candidates": self.candidates_generated,
            "from_memory": self.candidates_from_memory,
            "evolved": self.candidates_evolved,
            "backtests": self.backtests_run,
            "best_sharpe": round(self.best_sharpe, 4),
            "avg_sharpe": round(self.avg_sharpe, 4),
            "best_strategy_name": best_name,
            "saved": self.saved_to_memory,
            "doctor_blocked": self.doctor_blocked,
            "generation": self.generation,
        }


class EvolutionEngine:
    """Continuous strategy evolution loop.

    Combines StrategyGenerator + GeneticOptimizer + BacktestLab
    with regime-aware memory persistence.
    """

    def __init__(
        self,
        population_size: int = 50,
        memory_seed_ratio: float = 0.3,
        generations: int = 3,
        min_sharpe_to_save: float = 1.0,
        max_drawdown_to_save: float = 0.25,
    ) -> None:
        self.population_size = population_size
        self.memory_seed_ratio = memory_seed_ratio
        self.generations = generations
        self.min_sharpe_to_save = min_sharpe_to_save
        self.max_drawdown_to_save = max_drawdown_to_save

        self.generator = StrategyGenerator()
        self.optimizer = GeneticOptimizer()
        self.backtest_lab = BacktestLab()
        self.memory = StrategyMemoryStore()

        self._generation_counter = 0

    def run_cycle(
        self,
        cycle: int,
        regime: str,
        candles: list[dict],
        doctor_health: float = 100.0,
    ) -> EvolutionReport:
        """Execute one full evolution cycle.

        Args:
            cycle: Current system cycle number.
            regime: Detected market regime string.
            candles: Market data for backtesting.
            doctor_health: Bot Doctor health score (0-100).
                           If < 50 (critical), skip saving to memory.
        """
        self._generation_counter += 1
        report = EvolutionReport(
            cycle=cycle,
            regime=regime,
            generation=self._generation_counter,
        )

        # --- 1. Recall from memory ---
        memory_seed_count = max(1, int(self.population_size * self.memory_seed_ratio))
        memory_strategies = self.memory.load_by_regime(regime, limit=memory_seed_count)
        seeded = [r.get("strategy", r) for r in memory_strategies if isinstance(r, dict)]
        report.candidates_from_memory = len(seeded)

        # --- 2. Generate fresh candidates ---
        fresh_count = max(1, self.population_size - len(seeded))
        fresh = self.generator.generate_population(fresh_count)
        population = seeded + fresh
        report.candidates_generated = len(population)

        # --- 3. Evolve ---
        evolved = self.optimizer.evolve(population, generations=self.generations)
        report.candidates_evolved = len(evolved)

        # --- 4. Backtest all ---
        results: list[dict] = []
        for strategy in evolved:
            result = self.backtest_lab.run_backtest(strategy=strategy, data=candles)
            results.append(result)
        report.backtests_run = len(results)

        # --- 5. Rank and filter ---
        valid = [
            r for r in results
            if float(r.get("sharpe", 0)) >= self.min_sharpe_to_save
            and float(r.get("drawdown", 1)) <= self.max_drawdown_to_save
        ]
        blocked = len(results) - len(valid)
        report.doctor_blocked = blocked

        if results:
            sharpes = [float(r.get("sharpe", 0)) for r in results]
            report.avg_sharpe = sum(sharpes) / len(sharpes)
            best = max(results, key=lambda r: float(r.get("sharpe", 0)))
            report.best_sharpe = float(best.get("sharpe", 0))
            report.best_strategy = best.get("strategy", {})

        # --- 6. Save winners to memory ---
        if doctor_health >= 50.0 and valid:
            saved = self.memory.save_for_regime(regime, valid)
            report.saved_to_memory = saved
        else:
            if doctor_health < 50.0:
                logger.warning(
                    "Evolution cycle %d: doctor health %.0f < 50, skipping memory save",
                    cycle, doctor_health,
                )

        logger.info(
            "Evolution cycle %d gen %d: %d candidates, best_sharpe=%.4f, saved=%d",
            cycle, self._generation_counter, len(evolved),
            report.best_sharpe, report.saved_to_memory,
        )
        return report

    def render(self, report: EvolutionReport) -> str:
        """Render evolution report as text."""
        best_strat = report.best_strategy
        strat_str = (
            f"{best_strat.get('entry_indicator', '?')} → {best_strat.get('exit_indicator', '?')} "
            f"p={best_strat.get('period', '?')}"
            if best_strat else "none"
        )
        return (
            f"🧬 AI EVOLUTION LAB\n"
            f"   Generation  : {report.generation}  |  Regime: {report.regime}\n"
            f"   Candidates  : {report.candidates_generated} "
            f"({report.candidates_from_memory} from memory + "
            f"{report.candidates_generated - report.candidates_from_memory} fresh)\n"
            f"   Evolved     : {report.candidates_evolved}  |  "
            f"Backtests: {report.backtests_run}\n"
            f"   Best Sharpe : {report.best_sharpe:.4f}  |  "
            f"Avg Sharpe: {report.avg_sharpe:.4f}\n"
            f"   Best Strategy: {strat_str}\n"
            f"   Saved to Memory: {report.saved_to_memory}  |  "
            f"Doctor Blocked: {report.doctor_blocked}\n"
        )
