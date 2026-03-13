from __future__ import annotations

from v26.runtime_profile import PROFILE_PRESETS, normalize_profile_name, resolve_profile


def _assert_close(actual: float, expected: float, eps: float = 1e-9) -> None:
    if abs(actual - expected) > eps:
        raise AssertionError(f"Expected {expected}, got {actual}")


def main() -> None:
    assert normalize_profile_name("balanced") == "balanced"
    assert normalize_profile_name("AGGRESSIVE") == "aggressive"
    assert normalize_profile_name("unknown") == "balanced"

    cons = resolve_profile("conservative")
    bal = resolve_profile("balanced")
    agg = resolve_profile("aggressive")

    assert cons["name"] == "conservative"
    assert bal["name"] == "balanced"
    assert agg["name"] == "aggressive"

    _assert_close(float(cons["sl_pct"]), float(PROFILE_PRESETS["conservative"]["sl_pct"]))
    _assert_close(float(bal["tp_pct"]), float(PROFILE_PRESETS["balanced"]["tp_pct"]))
    _assert_close(float(agg["alert_min_conf"]), float(PROFILE_PRESETS["aggressive"]["alert_min_conf"]))

    assert float(cons["alert_min_conf"]) > float(agg["alert_min_conf"])
    assert float(cons["ticket_min_rr"]) > float(agg["ticket_min_rr"])
    assert float(cons["ticket_max_stop_pct"]) < float(agg["ticket_max_stop_pct"])

    print("[OK] test_v30_profile passed")


if __name__ == "__main__":
    main()