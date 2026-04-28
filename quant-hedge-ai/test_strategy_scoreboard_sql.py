"""Tests option N — StrategyScoreboardSQL (persistance SQLite)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from databases.strategy_scoreboard_sql import StrategyScoreboardSQL


# ---------------------------------------------------------------------------
# Fixture — scoreboard en mémoire (fichier temp)
# ---------------------------------------------------------------------------


@pytest.fixture
def sb(tmp_path: Path) -> StrategyScoreboardSQL:
    return StrategyScoreboardSQL(db_path=str(tmp_path / "test_scoreboard.db"))


def _make_strategy(name: str = "MomentumV1") -> dict:
    return {"name": name, "params": {"window": 14}}


def _make_metrics(sharpe: float = 1.5, pnl: float = 0.10,
                  win_rate: float = 0.55, drawdown: float = 0.05,
                  kelly: float = 0.12, cycle: int = 1) -> dict:
    return {
        "sharpe": sharpe, "pnl": pnl, "win_rate": win_rate,
        "drawdown": drawdown, "kelly": kelly, "cycle": cycle,
    }


# ---------------------------------------------------------------------------
# Tests add + top
# ---------------------------------------------------------------------------


class TestScoreboardAdd:
    def test_add_single_strategy(self, sb):
        sb.add(_make_strategy(), _make_metrics())
        assert len(sb.top()) == 1

    def test_add_multiple_strategies(self, sb):
        for i in range(5):
            sb.add(_make_strategy(f"Strat{i}"), _make_metrics(sharpe=float(i)))
        assert len(sb.top()) == 5

    def test_top_sorted_by_sharpe_desc(self, sb):
        sb.add(_make_strategy("A"), _make_metrics(sharpe=1.0))
        sb.add(_make_strategy("B"), _make_metrics(sharpe=3.5))
        sb.add(_make_strategy("C"), _make_metrics(sharpe=2.0))
        top = sb.top()
        sharpes = [r["sharpe"] for r in top]
        assert sharpes == sorted(sharpes, reverse=True)

    def test_top_n_limits_results(self, sb):
        for i in range(10):
            sb.add(_make_strategy(f"S{i}"), _make_metrics(sharpe=float(i)))
        assert len(sb.top(n=3)) == 3

    def test_strategy_dict_preserved(self, sb):
        strat = {"name": "KellyMomentum", "params": {"alpha": 0.01}}
        sb.add(strat, _make_metrics())
        result = sb.top(n=1)[0]
        assert result["strategy"]["name"] == "KellyMomentum"
        assert result["strategy"]["params"]["alpha"] == 0.01


# ---------------------------------------------------------------------------
# Tests stats
# ---------------------------------------------------------------------------


class TestScoreboardStats:
    def test_empty_stats(self, sb):
        s = sb.stats()
        assert s["total_strategies"] == 0
        assert s["avg_sharpe"] == 0.0
        assert s["best_sharpe"] == 0.0

    def test_stats_total(self, sb):
        for i in range(5):
            sb.add(_make_strategy(f"S{i}"), _make_metrics(sharpe=float(i + 1)))
        s = sb.stats()
        assert s["total_strategies"] == 5

    def test_stats_best_sharpe(self, sb):
        sb.add(_make_strategy("A"), _make_metrics(sharpe=1.0))
        sb.add(_make_strategy("B"), _make_metrics(sharpe=4.0))
        assert sb.stats()["best_sharpe"] == pytest.approx(4.0)

    def test_stats_avg_sharpe(self, sb):
        sb.add(_make_strategy("A"), _make_metrics(sharpe=2.0))
        sb.add(_make_strategy("B"), _make_metrics(sharpe=4.0))
        assert sb.stats()["avg_sharpe"] == pytest.approx(3.0)

    def test_stats_median_sharpe(self, sb):
        for v in [1.0, 2.0, 3.0]:
            sb.add(_make_strategy(), _make_metrics(sharpe=v))
        assert sb.stats()["median_sharpe"] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Tests top_by_metric
# ---------------------------------------------------------------------------


class TestTopByMetric:
    def test_top_by_pnl(self, sb):
        sb.add(_make_strategy("A"), _make_metrics(pnl=0.05))
        sb.add(_make_strategy("B"), _make_metrics(pnl=0.20))
        sb.add(_make_strategy("C"), _make_metrics(pnl=0.10))
        top = sb.top_by_metric("pnl", n=1)
        assert top[0]["pnl"] == pytest.approx(0.20)

    def test_top_by_drawdown_asc(self, sb):
        """Meilleur drawdown = le plus bas."""
        sb.add(_make_strategy("A"), _make_metrics(drawdown=0.15))
        sb.add(_make_strategy("B"), _make_metrics(drawdown=0.03))
        top = sb.top_by_metric("drawdown", n=1)
        assert top[0]["drawdown"] == pytest.approx(0.03)

    def test_top_by_win_rate(self, sb):
        sb.add(_make_strategy("A"), _make_metrics(win_rate=0.45))
        sb.add(_make_strategy("B"), _make_metrics(win_rate=0.70))
        top = sb.top_by_metric("win_rate", n=1)
        assert top[0]["win_rate"] == pytest.approx(0.70)

    def test_top_by_kelly(self, sb):
        sb.add(_make_strategy("A"), _make_metrics(kelly=0.05))
        sb.add(_make_strategy("B"), _make_metrics(kelly=0.22))
        top = sb.top_by_metric("kelly", n=1)
        assert top[0]["kelly"] == pytest.approx(0.22)

    def test_invalid_metric_raises(self, sb):
        with pytest.raises(ValueError, match="invalide"):
            sb.top_by_metric("total_nonsense")

    def test_valid_metrics_list(self, sb):
        for m in ["sharpe", "pnl", "win_rate", "drawdown", "kelly", "cycle"]:
            sb.top_by_metric(m, n=1)  # ne doit pas lever d'exception


# ---------------------------------------------------------------------------
# Tests persistance (rouverture de la base)
# ---------------------------------------------------------------------------


class TestScoreboardPersistence:
    def test_data_persists_across_instances(self, tmp_path):
        db_path = str(tmp_path / "persist.db")
        sb1 = StrategyScoreboardSQL(db_path=db_path)
        sb1.add(_make_strategy("Persist"), _make_metrics(sharpe=5.0))

        sb2 = StrategyScoreboardSQL(db_path=db_path)
        assert sb2.stats()["total_strategies"] == 1
        assert sb2.top(n=1)[0]["sharpe"] == pytest.approx(5.0)

    def test_clear_removes_all(self, sb):
        sb.add(_make_strategy(), _make_metrics())
        sb.add(_make_strategy("B"), _make_metrics(sharpe=2.0))
        sb.clear()
        assert sb.stats()["total_strategies"] == 0

    def test_add_after_clear(self, sb):
        sb.add(_make_strategy(), _make_metrics())
        sb.clear()
        sb.add(_make_strategy("Post"), _make_metrics(sharpe=3.0))
        assert sb.stats()["total_strategies"] == 1


# ---------------------------------------------------------------------------
# Tests edge cases
# ---------------------------------------------------------------------------


class TestScoreboardEdgeCases:
    def test_missing_metrics_default_to_zero(self, sb):
        sb.add(_make_strategy(), {"cycle": 1})  # pas de sharpe/pnl/etc.
        s = sb.stats()
        assert s["total_strategies"] == 1
        assert s["avg_sharpe"] == pytest.approx(0.0)

    def test_top_empty_scoreboard(self, sb):
        assert sb.top() == []

    def test_strategy_none_field_handled(self, sb):
        """None dans metrics → converti en 0.0 via float()."""
        sb.add(_make_strategy(), {"sharpe": None, "cycle": 1})
        # float(None) lève TypeError → on vérifie que ça ne plante pas
        # Note: si ça plante, on voit l'erreur explicitement
        assert sb.stats()["total_strategies"] == 1

    def test_max_entries_trim(self, tmp_path):
        db_path = str(tmp_path / "trim.db")
        sb = StrategyScoreboardSQL(db_path=db_path, max_entries=5)
        for i in range(10):
            sb.add(_make_strategy(f"S{i}"), _make_metrics(sharpe=float(i)))
        # Après trim, max 5 entrées
        assert sb.stats()["total_strategies"] <= 5


# ---------------------------------------------------------------------------
# Tests runtime_config (option N)
# ---------------------------------------------------------------------------


class TestRuntimeConfigScoreboardSQL:
    def test_default_path(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert "strategy_scoreboard.db" in cfg.scoreboard_sql_path

    def test_env_scoreboard_path(self):
        import os
        from unittest.mock import patch
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_SCOREBOARD_SQL_PATH": "/tmp/test.db"}):
            cfg = load_runtime_config_from_env()
        assert cfg.scoreboard_sql_path == "/tmp/test.db"

    def test_as_dict_contains_field(self):
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "scoreboard_sql_path" in d
