"""Tests — Option V : PositionSizer (Kelly + CVaR adaptatif)."""
from __future__ import annotations
import sys, os
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from agents.risk.position_sizer import PositionSizer, SizingResult


def _sizer(**kw):
    return PositionSizer(**kw)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestInit:
    def test_defaults(self):
        s = PositionSizer()
        assert s.max_kelly_fraction == 0.25
        assert s.kelly_half is True

    def test_invalid_max_kelly(self):
        with pytest.raises(ValueError, match="max_kelly_fraction"):
            PositionSizer(max_kelly_fraction=0.0)

    def test_invalid_max_position_size_zero(self):
        with pytest.raises(ValueError, match="max_position_size"):
            PositionSizer(max_position_size=0.0)

    def test_invalid_max_position_size_over(self):
        with pytest.raises(ValueError, match="max_position_size"):
            PositionSizer(max_position_size=1.5)

    def test_invalid_min_position_size(self):
        with pytest.raises(ValueError, match="min_position_size"):
            PositionSizer(min_position_size=-0.01)

    def test_invalid_cvar_safety(self):
        with pytest.raises(ValueError, match="cvar_safety_factor"):
            PositionSizer(cvar_safety_factor=0.0)


# ---------------------------------------------------------------------------
# _compute_kelly
# ---------------------------------------------------------------------------
class TestKelly:
    def test_positive_kelly(self):
        s = PositionSizer(kelly_half=False)
        k = s._compute_kelly(win_rate=0.6, avg_win=1.0, avg_loss=0.5)
        assert k > 0

    def test_zero_win_rate(self):
        s = PositionSizer()
        assert s._compute_kelly(0.0, 1.0, 0.5) == 0.0

    def test_zero_avg_win(self):
        s = PositionSizer()
        assert s._compute_kelly(0.6, 0.0, 0.5) == 0.0

    def test_zero_avg_loss(self):
        s = PositionSizer()
        assert s._compute_kelly(0.6, 1.0, 0.0) == 0.0

    def test_half_kelly(self):
        s_full = PositionSizer(kelly_half=False)
        s_half = PositionSizer(kelly_half=True)
        k_full = s_full._compute_kelly(0.6, 1.0, 0.5)
        k_half = s_half._compute_kelly(0.6, 1.0, 0.5)
        assert pytest.approx(k_half, rel=1e-5) == k_full / 2.0

    def test_win_rate_100_percent(self):
        s = PositionSizer()
        assert s._compute_kelly(1.0, 1.0, 0.5) == 0.0  # win_rate >= 1 → 0


# ---------------------------------------------------------------------------
# _compute_cvar_cap
# ---------------------------------------------------------------------------
class TestCVaRCap:
    def test_no_cvar_returns_one(self):
        s = PositionSizer()
        assert s._compute_cvar_cap(cvar=0.0, portfolio_value=10_000.0) == 1.0

    def test_no_portfolio_returns_one(self):
        s = PositionSizer()
        assert s._compute_cvar_cap(cvar=500.0, portfolio_value=0.0) == 1.0

    def test_cap_reduces_with_high_cvar(self):
        s = PositionSizer()
        cap = s._compute_cvar_cap(cvar=2_000.0, portfolio_value=10_000.0)  # 20% CVaR
        assert cap < 1.0
        assert cap >= 0.0

    def test_safety_factor_tightens_cap(self):
        s1 = PositionSizer(cvar_safety_factor=1.0)
        s2 = PositionSizer(cvar_safety_factor=2.0)
        cap1 = s1._compute_cvar_cap(1_000.0, 10_000.0)
        cap2 = s2._compute_cvar_cap(1_000.0, 10_000.0)
        assert cap2 <= cap1


# ---------------------------------------------------------------------------
# compute
# ---------------------------------------------------------------------------
class TestCompute:
    def test_negative_kelly_returns_zero_size(self):
        s = PositionSizer()
        r = s.compute(win_rate=0.1, avg_win=0.5, avg_loss=2.0)
        assert r.size == 0.0
        assert r.method == "min_fallback"

    def test_kelly_only_method(self):
        s = PositionSizer()
        r = s.compute(win_rate=0.65, avg_win=1.0, avg_loss=0.5)
        assert r.method == "kelly_only"
        assert r.size > 0

    def test_kelly_cvar_method(self):
        s = PositionSizer()
        r = s.compute(win_rate=0.65, avg_win=1.0, avg_loss=0.5, cvar=500.0, portfolio_value=10_000.0)
        assert r.method == "kelly_cvar"

    def test_size_capped_at_max(self):
        s = PositionSizer(max_position_size=0.10)
        r = s.compute(win_rate=0.99, avg_win=10.0, avg_loss=0.1)  # Kelly énorme
        assert r.size <= 0.10

    def test_min_size_applied(self):
        s = PositionSizer(min_position_size=0.05)
        r = s.compute(win_rate=0.52, avg_win=0.11, avg_loss=0.10)  # Kelly très petit
        if r.size > 0:
            assert r.size >= 0.05

    def test_result_has_all_keys(self):
        s = PositionSizer()
        r = s.compute(0.6, 1.0, 0.5)
        assert hasattr(r, "size")
        assert hasattr(r, "kelly_f")
        assert hasattr(r, "kelly_capped")
        assert hasattr(r, "cvar_cap")
        assert hasattr(r, "method")
        assert hasattr(r, "reason")

    def test_as_dict(self):
        s = PositionSizer()
        r = s.compute(0.6, 1.0, 0.5)
        d = s.as_dict(r)
        assert "size" in d and "method" in d
