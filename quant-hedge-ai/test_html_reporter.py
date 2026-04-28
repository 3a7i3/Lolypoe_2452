"""Tests — Option Y : HtmlReporter."""
from __future__ import annotations
import sys, os, tempfile
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from agents.reporting.html_reporter import HtmlReporter

_PAPER = {"equity": 10_500.0, "realized_pnl": 500.0, "win_rate": 0.6, "drawdown": 0.03, "total_trades": 12, "position": 0.1}
_BT    = {"strategy_count": 20, "best_pnl": 0.08, "best_sharpe": 1.2, "max_drawdown": 0.04, "data_mode": "binance"}
_WFO   = {"n_splits_used": 4, "mean_sharpe": 0.9, "stability": 0.75, "data_mode": "real"}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestInit:
    def test_defaults(self):
        r = HtmlReporter()
        assert r.keep_last_n == 10

    def test_empty_output_dir_raises(self):
        with pytest.raises(ValueError, match="output_dir"):
            HtmlReporter(output_dir="")


# ---------------------------------------------------------------------------
# generate (sans écriture disque)
# ---------------------------------------------------------------------------
class TestGenerate:
    def test_returns_html_content_when_no_write(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, _BT, _WFO, cycle=1, write_file=False)
        assert "<!DOCTYPE html>" in html
        assert "Quant Hedge AI" in html

    def test_cycle_in_html(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, cycle=42, write_file=False)
        assert "42" in html

    def test_symbol_in_html(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, symbol="ETH/USDT", cycle=1, write_file=False)
        assert "ETH/USDT" in html

    def test_equity_in_html(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, cycle=1, write_file=False)
        assert "10" in html  # 10500 apparaît

    def test_backtest_section_in_html(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, _BT, cycle=1, write_file=False)
        assert "Backtest" in html

    def test_wfo_section_in_html(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, wfo_result=_WFO, cycle=1, write_file=False)
        assert "Walk-Forward" in html

    def test_robust_badge_when_wfo_passes(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, wfo_result=_WFO, cycle=1, write_file=False)
        assert "ROBUSTE" in html

    def test_fragile_badge_when_wfo_fails(self):
        r = HtmlReporter()
        _bad_wfo = {"n_splits_used": 3, "mean_sharpe": 0.1, "stability": 0.2, "data_mode": "real"}
        html = r.generate(_PAPER, wfo_result=_bad_wfo, cycle=1, write_file=False)
        assert "FRAGILE" in html

    def test_na_badge_when_no_wfo(self):
        r = HtmlReporter()
        html = r.generate(_PAPER, wfo_result={"n_splits_used": 0, "data_mode": "insufficient"}, cycle=1, write_file=False)
        assert "N/A" in html

    def test_none_paper_fields_graceful(self):
        r = HtmlReporter()
        html = r.generate({}, cycle=0, write_file=False)  # tout vide
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# generate avec écriture disque
# ---------------------------------------------------------------------------
class TestGenerateFile:
    def test_file_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = HtmlReporter(output_dir=tmp)
            path = r.generate(_PAPER, cycle=1)
            assert os.path.exists(path)

    def test_file_contains_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = HtmlReporter(output_dir=tmp)
            path = r.generate(_PAPER, cycle=1)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "<!DOCTYPE html>" in content

    def test_multiple_cycles_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = HtmlReporter(output_dir=tmp, keep_last_n=0)
            for c in range(1, 4):
                r.generate(_PAPER, cycle=c)
            assert len(r.list_reports()) == 3

    def test_keep_last_n_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = HtmlReporter(output_dir=tmp, keep_last_n=2)
            for c in range(1, 6):
                r.generate(_PAPER, cycle=c)
            assert len(r.list_reports()) <= 2


# ---------------------------------------------------------------------------
# list_reports
# ---------------------------------------------------------------------------
class TestListReports:
    def test_empty_when_no_dir(self):
        r = HtmlReporter(output_dir="/nonexistent_dir_xyz/")
        assert r.list_reports() == []

    def test_sorted_ascending(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = HtmlReporter(output_dir=tmp, keep_last_n=0)
            r.generate(_PAPER, cycle=10)
            r.generate(_PAPER, cycle=1)
            reports = r.list_reports()
            assert "000001" in reports[0]
