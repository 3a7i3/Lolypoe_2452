"""Tests — Option X : PortfolioRebalancer."""
from __future__ import annotations
import sys, os
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from agents.execution.portfolio_rebalancer import PortfolioRebalancer, RebalanceOrder


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestInit:
    def test_defaults(self):
        r = PortfolioRebalancer()
        assert r.drift_threshold == 0.05
        assert r.max_orders == 5

    def test_invalid_drift_negative(self):
        with pytest.raises(ValueError, match="drift_threshold"):
            PortfolioRebalancer(drift_threshold=-0.01)

    def test_invalid_drift_ge_one(self):
        with pytest.raises(ValueError, match="drift_threshold"):
            PortfolioRebalancer(drift_threshold=1.0)

    def test_invalid_max_orders(self):
        with pytest.raises(ValueError, match="max_orders"):
            PortfolioRebalancer(max_orders=0)


# ---------------------------------------------------------------------------
# compute_orders
# ---------------------------------------------------------------------------
class TestComputeOrders:
    def test_no_drift_returns_empty(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        current = {"BTC": 0.50, "ETH": 0.50}
        target  = {"BTC": 0.50, "ETH": 0.50}
        assert rb.compute_orders(current, target) == []

    def test_buy_when_underweight(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        current = {"BTC": 0.30}
        target  = {"BTC": 0.50}  # drift = +0.20 > threshold
        orders = rb.compute_orders(current, target)
        assert len(orders) == 1
        assert orders[0].action == "BUY"
        assert orders[0].symbol == "BTC"

    def test_sell_when_overweight(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        current = {"BTC": 0.70}
        target  = {"BTC": 0.50}  # drift = -0.20
        orders = rb.compute_orders(current, target)
        assert len(orders) == 1
        assert orders[0].action == "SELL"

    def test_below_threshold_skipped(self):
        rb = PortfolioRebalancer(drift_threshold=0.10)
        current = {"BTC": 0.50}
        target  = {"BTC": 0.54}  # drift = 0.04 < 0.10
        orders = rb.compute_orders(current, target)
        assert orders == []

    def test_max_orders_respected(self):
        rb = PortfolioRebalancer(drift_threshold=0.01, max_orders=2)
        current = {"A": 0.10, "B": 0.10, "C": 0.10, "D": 0.10}
        target  = {"A": 0.30, "B": 0.30, "C": 0.30, "D": 0.30}
        orders = rb.compute_orders(current, target)
        assert len(orders) <= 2

    def test_delta_value_computed(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        current = {"BTC": 0.30}
        target  = {"BTC": 0.50}
        orders = rb.compute_orders(current, target, equity=10_000.0)
        assert orders[0].delta_value == pytest.approx(2_000.0, rel=1e-4)

    def test_new_symbol_in_target(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        current = {}
        target  = {"ETH": 0.50}
        orders = rb.compute_orders(current, target)
        assert len(orders) == 1
        assert orders[0].action == "BUY"

    def test_removed_symbol_gets_sell(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        current = {"BTC": 0.50}
        target  = {}  # BTC n'est plus dans la cible
        orders = rb.compute_orders(current, target)
        assert len(orders) == 1
        assert orders[0].action == "SELL"

    def test_sorted_by_drift_descending(self):
        rb = PortfolioRebalancer(drift_threshold=0.01)
        current = {"A": 0.0, "B": 0.0}
        target  = {"A": 0.40, "B": 0.20}  # A a plus de drift
        orders = rb.compute_orders(current, target)
        assert orders[0].symbol == "A"


# ---------------------------------------------------------------------------
# needs_rebalance
# ---------------------------------------------------------------------------
class TestNeedsRebalance:
    def test_true_when_drift_above_threshold(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        assert rb.needs_rebalance({"BTC": 0.30}, {"BTC": 0.50})

    def test_false_when_aligned(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        assert not rb.needs_rebalance({"BTC": 0.50}, {"BTC": 0.50})


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------
class TestStatus:
    def test_status_keys(self):
        rb = PortfolioRebalancer(drift_threshold=0.05)
        s = rb.status({"BTC": 0.30}, {"BTC": 0.50})
        assert "max_drift" in s
        assert "needs_rebalance" in s
        assert s["needs_rebalance"] is True

    def test_empty_weights(self):
        rb = PortfolioRebalancer()
        s = rb.status({}, {})
        assert s["max_drift"] == 0.0
        assert s["needs_rebalance"] is False
