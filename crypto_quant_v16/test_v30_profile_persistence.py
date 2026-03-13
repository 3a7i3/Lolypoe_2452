from __future__ import annotations

import os
import tempfile

from v26.runtime_profile import (
    CUSTOM_PROFILE_NAME,
    load_saved_profile_name,
    load_saved_snapshot_schema_only,
    load_saved_snapshot_tag_filter,
    profile_for_dashboard,
    save_custom_profile,
    save_profile_name,
    save_snapshot_schema_only,
    save_snapshot_tag_filter,
)


def main() -> None:
    prev_alert = os.getenv("ALERT_PROFILE")
    prev_v30 = os.getenv("V30_PROFILE")

    try:
        os.environ.pop("ALERT_PROFILE", None)
        os.environ.pop("V30_PROFILE", None)

        with tempfile.TemporaryDirectory() as td:
            assert load_saved_profile_name(td) is None

            saved = save_profile_name("aggressive", td)
            assert saved == "aggressive"
            assert load_saved_profile_name(td) == "aggressive"

            assert load_saved_snapshot_tag_filter(td) is None
            saved_filter = save_snapshot_tag_filter("Scalping-Asia", td)
            assert saved_filter == "scalping-asia"
            assert load_saved_snapshot_tag_filter(td) == "scalping-asia"
            assert load_saved_snapshot_schema_only(td) is False
            assert save_snapshot_schema_only(True, td) is True
            assert load_saved_snapshot_schema_only(td) is True

            profile = profile_for_dashboard(default="balanced", root_dir=td)
            assert str(profile["name"]) == "aggressive"

            os.environ["ALERT_PROFILE"] = "conservative"
            profile_env = profile_for_dashboard(default="balanced", root_dir=td)
            assert str(profile_env["name"]) == "conservative"

            os.environ.pop("ALERT_PROFILE", None)
            custom = save_custom_profile(
                {
                    "sl_pct": 0.011,
                    "tp_pct": 0.055,
                    "alert_min_conf": 0.81,
                    "alert_min_imbalance": 0.31,
                    "ticket_min_rr": 2.4,
                    "ticket_max_stop_pct": 1.5,
                    "poll_seconds": 22,
                    "min_regime_conf": 0.79,
                },
                root_dir=td,
            )
            assert str(custom["name"]) == CUSTOM_PROFILE_NAME
            assert load_saved_profile_name(td) == CUSTOM_PROFILE_NAME

            profile_custom = profile_for_dashboard(default="balanced", root_dir=td)
            assert str(profile_custom["name"]) == CUSTOM_PROFILE_NAME
            assert abs(float(profile_custom["tp_pct"]) - 0.055) < 1e-9

            os.environ["V30_PROFILE"] = "balanced"
            profile_env_override = profile_for_dashboard(default="conservative", root_dir=td)
            assert str(profile_env_override["name"]) == "balanced"
            assert load_saved_snapshot_tag_filter(td) == "scalping-asia"
            assert load_saved_snapshot_schema_only(td) is True

        print("[OK] test_v30_profile_persistence passed")
    finally:
        if prev_alert is None:
            os.environ.pop("ALERT_PROFILE", None)
        else:
            os.environ["ALERT_PROFILE"] = prev_alert

        if prev_v30 is None:
            os.environ.pop("V30_PROFILE", None)
        else:
            os.environ["V30_PROFILE"] = prev_v30


if __name__ == "__main__":
    main()
