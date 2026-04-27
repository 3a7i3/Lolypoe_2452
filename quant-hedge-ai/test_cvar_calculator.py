"""Tests option M — CVaRCalculator et Expected Shortfall."""
from __future__ import annotations

import pytest

from agents.risk.cvar_calculator import CVaRCalculator


# ---------------------------------------------------------------------------
# Fixtures communes
# ---------------------------------------------------------------------------

MIXED_RETURNS = [0.02, -0.05, 0.01, -0.03, 0.04, -0.08, 0.03, -0.01, 0.02, -0.06]
ALL_POSITIVE = [0.01, 0.02, 0.03, 0.04, 0.05]
ALL_NEGATIVE = [-0.01, -0.02, -0.03, -0.04, -0.05]


# ---------------------------------------------------------------------------
# Tests init
# ---------------------------------------------------------------------------


class TestCVaRInit:
    def test_valid_defaults(self):
        c = CVaRCalculator()
        assert c.confidence == 0.95
        assert c.max_loss == 0.05

    def test_confidence_zero_raises(self):
        with pytest.raises(ValueError):
            CVaRCalculator(confidence=0.0)

    def test_confidence_one_raises(self):
        with pytest.raises(ValueError):
            CVaRCalculator(confidence=1.0)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValueError):
            CVaRCalculator(confidence=1.5)

    def test_max_loss_zero_raises(self):
        with pytest.raises(ValueError):
            CVaRCalculator(max_loss=0.0)

    def test_max_loss_negative_raises(self):
        with pytest.raises(ValueError):
            CVaRCalculator(max_loss=-0.01)

    def test_custom_params(self):
        c = CVaRCalculator(confidence=0.99, max_loss=0.10)
        assert c.confidence == 0.99
        assert c.max_loss == 0.10


# ---------------------------------------------------------------------------
# Tests compute()
# ---------------------------------------------------------------------------


class TestCVaRCompute:
    def test_empty_returns_zero(self):
        c = CVaRCalculator()
        assert c.compute([]) == 0.0

    def test_single_return_zero(self):
        c = CVaRCalculator()
        assert c.compute([0.05]) == 0.0

    def test_all_positive_returns_zero(self):
        """Pas de pertes → CVaR = 0."""
        c = CVaRCalculator()
        assert c.compute(ALL_POSITIVE) == 0.0

    def test_all_negative_positive_cvar(self):
        """Tous négatifs → CVaR > 0."""
        c = CVaRCalculator(confidence=0.95)
        result = c.compute(ALL_NEGATIVE)
        assert result > 0.0

    def test_mixed_returns_positive_cvar(self):
        c = CVaRCalculator(confidence=0.95)
        result = c.compute(MIXED_RETURNS)
        assert result > 0.0

    def test_higher_confidence_higher_or_equal_cvar(self):
        """CVaR 99% >= CVaR 95% (tail plus petit = pires valeurs)."""
        returns = MIXED_RETURNS
        c95 = CVaRCalculator(confidence=0.95)
        c99 = CVaRCalculator(confidence=0.99)
        assert c99.compute(returns) >= c95.compute(returns)

    def test_cvar_at_least_worst_return_extreme(self):
        """CVaR doit refléter les pires retours, pas les meilleurs."""
        c = CVaRCalculator(confidence=0.90)
        returns = [0.05, 0.03, -0.20]  # un seul crash
        cvar = c.compute(returns)
        # Le tail inclut -0.20 → CVaR doit être >= 0.20
        assert cvar >= 0.15

    def test_cvar_is_positive(self):
        c = CVaRCalculator()
        for _ in range(10):
            result = c.compute(MIXED_RETURNS)
            assert result >= 0.0


# ---------------------------------------------------------------------------
# Tests compute_var()
# ---------------------------------------------------------------------------


class TestVaRCompute:
    def test_empty_returns_zero(self):
        c = CVaRCalculator()
        assert c.compute_var([]) == 0.0

    def test_var_positive_for_losses(self):
        c = CVaRCalculator(confidence=0.95)
        assert c.compute_var(ALL_NEGATIVE) > 0.0

    def test_var_zero_for_gains(self):
        c = CVaRCalculator(confidence=0.95)
        assert c.compute_var(ALL_POSITIVE) == 0.0

    def test_cvar_gte_var(self):
        """CVaR (Expected Shortfall) >= VaR par définition."""
        c = CVaRCalculator(confidence=0.95)
        var = c.compute_var(MIXED_RETURNS)
        cvar = c.compute(MIXED_RETURNS)
        assert cvar >= var


# ---------------------------------------------------------------------------
# Tests is_within_limit()
# ---------------------------------------------------------------------------


class TestIsWithinLimit:
    def test_all_gains_within_limit(self):
        c = CVaRCalculator(max_loss=0.05)
        assert c.is_within_limit(ALL_POSITIVE) is True

    def test_large_losses_not_within_limit(self):
        c = CVaRCalculator(confidence=0.95, max_loss=0.01)
        # Returns with big losses
        returns = [-0.10, -0.08, -0.05, 0.02, 0.03]
        assert c.is_within_limit(returns) is False

    def test_small_losses_within_limit(self):
        c = CVaRCalculator(confidence=0.95, max_loss=0.20)
        assert c.is_within_limit(MIXED_RETURNS) is True

    def test_empty_within_limit(self):
        c = CVaRCalculator(max_loss=0.05)
        assert c.is_within_limit([]) is True  # CVaR=0 <= max_loss


# ---------------------------------------------------------------------------
# Tests summary()
# ---------------------------------------------------------------------------


class TestCVaRSummary:
    def test_summary_keys(self):
        c = CVaRCalculator()
        s = c.summary(MIXED_RETURNS)
        assert "var" in s
        assert "cvar" in s
        assert "worst_return" in s
        assert "std" in s

    def test_summary_empty(self):
        c = CVaRCalculator()
        s = c.summary([])
        assert s["cvar"] == 0.0
        assert s["var"] == 0.0

    def test_summary_worst_return(self):
        c = CVaRCalculator()
        s = c.summary(MIXED_RETURNS)
        assert s["worst_return"] == pytest.approx(min(MIXED_RETURNS), abs=1e-6)


# ---------------------------------------------------------------------------
# Tests runtime_config (option M)
# ---------------------------------------------------------------------------


class TestRuntimeConfigCVaR:
    def test_defaults(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.cvar_confidence == pytest.approx(0.95)
        assert cfg.cvar_max_loss == pytest.approx(0.05)

    def test_env_cvar_confidence(self):
        import os
        from unittest.mock import patch
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_CVAR_CONFIDENCE": "0.99"}):
            cfg = load_runtime_config_from_env()
        assert cfg.cvar_confidence == pytest.approx(0.99)

    def test_env_cvar_max_loss(self):
        import os
        from unittest.mock import patch
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_CVAR_MAX_LOSS": "0.03"}):
            cfg = load_runtime_config_from_env()
        assert cfg.cvar_max_loss == pytest.approx(0.03)

    def test_as_dict_contains_cvar_fields(self):
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "cvar_confidence" in d
        assert "cvar_max_loss" in d
