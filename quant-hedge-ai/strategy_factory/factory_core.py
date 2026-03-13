from __future__ import annotations

from dataclasses import dataclass, field

from ai_evolution import StrategyMemoryStore
from strategy_factory.backtester import FactoryBacktester
from strategy_factory.bot_doctor_validator import BotDoctorValidator
from strategy_factory.performance_analyzer import PerformanceAnalyzer
from strategy_factory.strategy_generator import FactoryStrategyGenerator


@dataclass
class StrategyFactoryReport:
    generated_count: int = 0
    backtested_count: int = 0
    filtered_count: int = 0
    approved_count: int = 0
    blocked_count: int = 0
    regime: str = "unknown"
    regime_stability: float = 0.0
    memory_loaded_count: int = 0
    memory_saved_count: int = 0
    avg_loaded_age_cycles: float = 0.0
    top_strategies: list[dict] = field(default_factory=list)
    approved_results: list[dict] = field(default_factory=list)
    blocked_results: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "generated_count": self.generated_count,
            "backtested_count": self.backtested_count,
            "filtered_count": self.filtered_count,
            "approved_count": self.approved_count,
            "blocked_count": self.blocked_count,
            "regime": self.regime,
            "regime_stability": self.regime_stability,
            "memory_loaded_count": self.memory_loaded_count,
            "memory_saved_count": self.memory_saved_count,
            "avg_loaded_age_cycles": round(self.avg_loaded_age_cycles, 2),
            "top_strategies": [
                {
                    "sharpe": round(float(s.get("sharpe", 0.0)), 3),
                    "drawdown": round(float(s.get("drawdown", 0.0)), 4),
                    "win_rate": round(float(s.get("win_rate", 0.0)), 3),
                    "pnl": round(float(s.get("pnl", 0.0)), 3),
                }
                for s in self.top_strategies[:5]
            ],
        }


class StrategyFactory:
    """End-to-end strategy factory pipeline.

    Steps:
      1. Generate candidate strategies
      2. Backtest candidates in sandbox
      3. Filter + rank performance
      4. Validate each candidate via Bot Doctor Validator
      5. Return approved and ranked strategies
    """

    def __init__(self) -> None:
        self.generator = FactoryStrategyGenerator()
        self.backtester = FactoryBacktester()
        self.analyzer = PerformanceAnalyzer()
        self.validator = BotDoctorValidator()
        self.memory = StrategyMemoryStore()

    def run(
        self,
        candles: list[dict],
        target_count: int = 120,
        generations: int = 2,
        regime: str = "unknown",
    ) -> StrategyFactoryReport:
        candidates = self.generator.generate_candidates(population_size=target_count, generations=generations)
        stability = self.memory.get_regime_stability(regime)
        # Dynamic memory sizing by regime stability:
        # Low stability (0.0) → load 50% of base; High stability (1.0) → load 150% of base
        base_load = max(5, target_count // 6)
        dynamic_limit = int(base_load * (0.5 + stability))
        memory_loaded = self.memory.load_by_regime(regime, limit=dynamic_limit)
        memory_strategies = [r.get("strategy", {}) for r in memory_loaded if isinstance(r.get("strategy"), dict)]
        candidates.extend(memory_strategies)
        backtested = self.backtester.run(candidates, candles)
        filtered = self.analyzer.filter_candidates(backtested)
        ranked = self.analyzer.rank(filtered)

        approved: list[dict] = []
        blocked: list[dict] = []
        for r in ranked:
            decision = self.validator.validate(r)
            enriched = {**r, "doctor": {
                "approved": decision.approved,
                "health_score": decision.health_score,
                "reason": decision.reason,
                "findings": decision.findings,
            }}
            if decision.approved:
                approved.append(enriched)
            else:
                blocked.append(enriched)

        memory_saved = self.memory.save_for_regime(regime, approved[:20]) if approved else 0
        avg_loaded_age = (
            sum(float(item.get("age_cycles", 0)) for item in memory_loaded) / len(memory_loaded)
            if memory_loaded
            else 0.0
        )

        return StrategyFactoryReport(
            generated_count=len(candidates),
            backtested_count=len(backtested),
            filtered_count=len(filtered),
            approved_count=len(approved),
            blocked_count=len(blocked),
            regime=regime,
            regime_stability=stability,
            memory_loaded_count=len(memory_loaded),
            memory_saved_count=memory_saved,
            avg_loaded_age_cycles=avg_loaded_age,
            top_strategies=approved[:10] if approved else ranked[:10],
            approved_results=approved,
            blocked_results=blocked,
        )
