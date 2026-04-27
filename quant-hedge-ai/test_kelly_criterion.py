"""Tests option K — KellyCriterion et compute_avg_win_loss."""
from __future__ import annotations

import pytest

from agents.risk.kelly_criterion import KellyCriterion, compute_avg_win_loss


# ---------------------------------------------------------------------------
# Tests KellyCriterion — raw_fraction
# ---------------------------------------------------------------------------


class TestKellyRawFraction:
    def test_classic_kelly(self):
        """Exemple classique : 60% win rate, payoff 1:1."""
        k = KellyCriterion()
        # f* = 0.6 - 0.4/1.0 = 0.20
        assert k.raw_fraction(win_rate=0.6, avg_win=1.0, avg_loss=1.0) == pytest.approx(0.2, abs=1e-9)

    def test_positive_payoff_ratio(self):
        """Win rate 55%, avg_win=0.03, avg_loss=0.015 → payoff=2."""
        k = KellyCriterion()
        # f* = 0.55 - 0.45/2.0 = 0.55 - 0.225 = 0.325
        result = k.raw_fraction(win_rate=0.55, avg_win=0.03, avg_loss=0.015)
        assert result == pytest.approx(0.325, abs=1e-6)

    def test_negative_kelly_returns_zero(self):
        """Stratégie perdante → Kelly < 0 → 0."""
        k = KellyCriterion()
        # f* = 0.3 - 0.7/1.0 = -0.4 → 0
        assert k.raw_fraction(win_rate=0.3, avg_win=1.0, avg_loss=1.0) == 0.0

    def test_win_rate_zero_returns_zero(self):
        k = KellyCriterion()
        assert k.raw_fraction(win_rate=0.0, avg_win=0.05, avg_loss=0.02) == 0.0

    def test_win_rate_one_returns_zero(self):
        """win_rate=1.0 est invalide (hors [0,1[ strictement)."""
        k = KellyCriterion()
        assert k.raw_fraction(win_rate=1.0, avg_win=0.05, avg_loss=0.02) == 0.0

    def test_zero_avg_loss_returns_zero(self):
        k = KellyCriterion()
        assert k.raw_fraction(win_rate=0.6, avg_win=0.05, avg_loss=0.0) == 0.0

    def test_zero_avg_win_returns_zero(self):
        k = KellyCriterion()
        assert k.raw_fraction(win_rate=0.6, avg_win=0.0, avg_loss=0.02) == 0.0


# ---------------------------------------------------------------------------
# Tests KellyCriterion — adjusted_fraction (half-Kelly + clamp)
# ---------------------------------------------------------------------------


class TestKellyAdjustedFraction:
    def test_half_kelly_divides_by_two(self):
        k = KellyCriterion(max_fraction=1.0, half_kelly=True)
        raw = k.raw_fraction(0.6, 1.0, 1.0)  # 0.20
        adj = k.adjusted_fraction(0.6, 1.0, 1.0)
        assert adj == pytest.approx(raw / 2, abs=1e-6)

    def test_full_kelly_no_division(self):
        k = KellyCriterion(max_fraction=1.0, half_kelly=False)
        raw = k.raw_fraction(0.6, 1.0, 1.0)
        adj = k.adjusted_fraction(0.6, 1.0, 1.0)
        assert adj == pytest.approx(raw, abs=1e-6)

    def test_clamp_respects_max_fraction(self):
        """Kelly brut > max_fraction → clamp."""
        k = KellyCriterion(max_fraction=0.05, half_kelly=False)
        # win_rate=0.9, payoff=10 → Kelly très élevé
        adj = k.adjusted_fraction(0.9, 0.10, 0.01)
        assert adj <= 0.05

    def test_zero_kelly_returns_zero(self):
        k = KellyCriterion()
        assert k.adjusted_fraction(0.3, 1.0, 1.0) == 0.0


# ---------------------------------------------------------------------------
# Tests KellyCriterion — compute_size avec fallback
# ---------------------------------------------------------------------------


class TestKellyComputeSize:
    def test_positive_kelly_uses_kelly(self):
        k = KellyCriterion(max_fraction=0.25, half_kelly=True)
        size = k.compute_size(win_rate=0.6, avg_win=0.03, avg_loss=0.015, fallback=0.02)
        assert size > 0.0
        assert size <= 0.25

    def test_negative_kelly_uses_fallback(self):
        k = KellyCriterion(max_fraction=0.25, half_kelly=True)
        size = k.compute_size(win_rate=0.2, avg_win=0.01, avg_loss=0.05, fallback=0.02)
        assert size == pytest.approx(0.02, abs=1e-9)

    def test_fallback_clamped_by_max_fraction(self):
        """fallback > max_fraction → retourne max_fraction."""
        k = KellyCriterion(max_fraction=0.05, half_kelly=True)
        size = k.compute_size(win_rate=0.2, avg_win=0.01, avg_loss=0.05, fallback=0.99)
        assert size <= 0.05

    def test_size_respects_max_fraction(self):
        k = KellyCriterion(max_fraction=0.10, half_kelly=False)
        for wr in [0.5, 0.6, 0.7, 0.8]:
            size = k.compute_size(wr, avg_win=0.05, avg_loss=0.01)
            assert size <= 0.10, f"size={size} > max_fraction=0.10 pour win_rate={wr}"


# ---------------------------------------------------------------------------
# Tests KellyCriterion — validation init
# ---------------------------------------------------------------------------


class TestKellyInit:
    def test_max_fraction_zero_raises(self):
        with pytest.raises(ValueError):
            KellyCriterion(max_fraction=0.0)

    def test_max_fraction_above_one_raises(self):
        with pytest.raises(ValueError):
            KellyCriterion(max_fraction=1.1)

    def test_valid_init(self):
        k = KellyCriterion(max_fraction=0.5, half_kelly=False)
        assert k.max_fraction == 0.5
        assert k.half_kelly is False


# ---------------------------------------------------------------------------
# Tests compute_avg_win_loss
# ---------------------------------------------------------------------------


class TestComputeAvgWinLoss:
    def test_mixed_returns(self):
        returns = [0.05, -0.02, 0.03, -0.01, 0.04]
        avg_win, avg_loss = compute_avg_win_loss(returns)
        assert avg_win == pytest.approx((0.05 + 0.03 + 0.04) / 3, abs=1e-9)
        assert avg_loss == pytest.approx((0.02 + 0.01) / 2, abs=1e-9)

    def test_all_wins(self):
        avg_win, avg_loss = compute_avg_win_loss([0.01, 0.02, 0.03])
        assert avg_win > 0
        assert avg_loss == 0.0

    def test_all_losses(self):
        avg_win, avg_loss = compute_avg_win_loss([-0.01, -0.02])
        assert avg_win == 0.0
        assert avg_loss > 0

    def test_empty_returns(self):
        avg_win, avg_loss = compute_avg_win_loss([])
        assert avg_win == 0.0
        assert avg_loss == 0.0

    def test_single_gain(self):
        avg_win, avg_loss = compute_avg_win_loss([0.05])
        assert avg_win == pytest.approx(0.05)
        assert avg_loss == 0.0


# ---------------------------------------------------------------------------
# Tests runtime_config (V9_KELLY_*)
# ---------------------------------------------------------------------------


class TestRuntimeConfigKelly:
    def test_defaults(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.kelly_max_fraction == pytest.approx(0.25)
        assert cfg.kelly_half is True

    def test_env_kelly_max_fraction(self):
        import os
        from unittest.mock import patch
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_KELLY_MAX_FRACTION": "0.10"}):
            cfg = load_runtime_config_from_env()
        assert cfg.kelly_max_fraction == pytest.approx(0.10)

    def test_env_kelly_half_false(self):
        import os
        from unittest.mock import patch
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_KELLY_HALF": "false"}):
            cfg = load_runtime_config_from_env()
        assert cfg.kelly_half is False

    def test_as_dict_contains_kelly_fields(self):
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "kelly_max_fraction" in d
        assert "kelly_half" in d
