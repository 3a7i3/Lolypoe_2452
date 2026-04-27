"""Tests pour l'indicateur de source de données dans DirectorDashboard."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard.director_dashboard import DirectorDashboard, DirectorSnapshot


class TestDirectorSnapshotDataSource:
    def test_snapshot_default_data_source(self):
        s = DirectorSnapshot()
        assert s.data_source == "unknown"
        assert s.data_source_exchange == ""

    def test_snapshot_stores_data_source(self):
        s = DirectorSnapshot(data_source="binance_real", data_source_exchange="binance")
        assert s.data_source == "binance_real"
        assert s.data_source_exchange == "binance"


class TestDirectorDashboardUpdate:
    def _make_director(self) -> DirectorDashboard:
        return DirectorDashboard(starting_balance=10_000.0)

    def test_update_stores_data_source_binance(self):
        d = self._make_director()
        snap = d.update(cycle=1, data_source="binance_real")
        assert snap.data_source == "binance_real"
        assert snap.data_source_exchange == "binance"

    def test_update_stores_data_source_kraken(self):
        d = self._make_director()
        snap = d.update(cycle=1, data_source="kraken_real")
        assert snap.data_source == "kraken_real"
        assert snap.data_source_exchange == "kraken"

    def test_update_stores_data_source_okx(self):
        d = self._make_director()
        snap = d.update(cycle=1, data_source="okx_real")
        assert snap.data_source == "okx_real"
        assert snap.data_source_exchange == "okx"

    def test_update_stores_synthetic_fallback(self):
        d = self._make_director()
        snap = d.update(cycle=1, data_source="synthetic_fallback")
        assert snap.data_source == "synthetic_fallback"
        assert snap.data_source_exchange == ""

    def test_update_default_data_source_unknown(self):
        d = self._make_director()
        snap = d.update(cycle=1)
        assert snap.data_source == "unknown"
        assert snap.data_source_exchange == ""


class TestDirectorDashboardRender:
    def _render(self, data_source: str) -> str:
        d = DirectorDashboard(starting_balance=10_000.0)
        snap = d.update(cycle=5, data_source=data_source)
        return d.render(snap)

    def test_render_binance_shows_green_badge_in_header(self):
        output = self._render("binance_real")
        assert "🟢" in output
        assert "BINANCE" in output

    def test_render_kraken_shows_green_badge_in_header(self):
        output = self._render("kraken_real")
        assert "🟢" in output
        assert "KRAKEN" in output

    def test_render_okx_shows_green_badge_in_header(self):
        output = self._render("okx_real")
        assert "🟢" in output
        assert "OKX" in output

    def test_render_synthetic_shows_yellow_badge(self):
        output = self._render("synthetic_fallback")
        assert "🟡" in output
        assert "SYNTHÉTIQUE" in output

    def test_render_unknown_shows_white_badge(self):
        output = self._render("unknown")
        assert "⚪" in output

    def test_render_header_includes_cycle(self):
        d = DirectorDashboard(starting_balance=10_000.0)
        snap = d.update(cycle=42, data_source="binance_real")
        output = d.render(snap)
        assert "CYCLE 42" in output

    def test_render_data_source_section_present(self):
        output = self._render("binance_real")
        assert "SOURCE DONNÉES MARCHÉ" in output

    def test_render_exchange_name_in_data_source_section(self):
        output = self._render("kraken_real")
        assert "Kraken" in output

    def test_render_no_exchange_name_for_synthetic(self):
        output = self._render("synthetic_fallback")
        # Pas de ligne "Exchange actif" pour les données synthétiques
        assert "Exchange actif" not in output


class TestFormatDataSource:
    def test_binance_real(self):
        icon, label = DirectorDashboard._format_data_source("binance_real", "binance")
        assert icon == "🟢"
        assert "BINANCE" in label
        assert "LIVE" in label

    def test_kraken_real(self):
        icon, label = DirectorDashboard._format_data_source("kraken_real", "kraken")
        assert icon == "🟢"
        assert "KRAKEN" in label

    def test_synthetic_fallback(self):
        icon, label = DirectorDashboard._format_data_source("synthetic_fallback", "")
        assert icon == "🟡"
        assert "SYNTHÉTIQUE" in label

    def test_unknown(self):
        icon, label = DirectorDashboard._format_data_source("unknown", "")
        assert icon == "⚪"
