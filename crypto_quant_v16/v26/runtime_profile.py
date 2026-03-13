from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any


PROFILE_PRESETS: dict[str, dict[str, Any]] = {
    "conservative": {
        "sl_pct": 0.015,
        "tp_pct": 0.028,
        "alert_min_conf": 0.78,
        "alert_min_imbalance": 0.35,
        "ticket_min_rr": 2.0,
        "ticket_max_stop_pct": 1.8,
        "poll_seconds": 60,
        "min_regime_conf": 0.72,
    },
    "balanced": {
        "sl_pct": 0.020,
        "tp_pct": 0.040,
        "alert_min_conf": 0.70,
        "alert_min_imbalance": 0.25,
        "ticket_min_rr": 1.5,
        "ticket_max_stop_pct": 3.0,
        "poll_seconds": 45,
        "min_regime_conf": 0.65,
    },
    "aggressive": {
        "sl_pct": 0.030,
        "tp_pct": 0.060,
        "alert_min_conf": 0.60,
        "alert_min_imbalance": 0.18,
        "ticket_min_rr": 1.2,
        "ticket_max_stop_pct": 5.0,
        "poll_seconds": 30,
        "min_regime_conf": 0.55,
    },
}

CUSTOM_PROFILE_NAME = "custom"

PROFILE_RANGES: dict[str, tuple[float, float]] = {
    "sl_pct": (0.001, 0.200),
    "tp_pct": (0.002, 0.500),
    "alert_min_conf": (0.50, 0.99),
    "alert_min_imbalance": (0.05, 0.95),
    "ticket_min_rr": (0.50, 10.0),
    "ticket_max_stop_pct": (0.20, 25.0),
    "poll_seconds": (5.0, 600.0),
    "min_regime_conf": (0.30, 0.99),
}


def normalize_profile_name(name: str | None) -> str:
    raw = (name or "").strip().lower()
    if raw in PROFILE_PRESETS or raw == CUSTOM_PROFILE_NAME:
        return raw
    return "balanced"


def resolve_profile(name: str | None) -> dict[str, Any]:
    normalized = normalize_profile_name(name)
    if normalized == CUSTOM_PROFILE_NAME:
        # `resolve_custom_profile` keeps the same return shape as a preset profile.
        return resolve_custom_profile(None)
    base = PROFILE_PRESETS[normalized].copy()
    base["name"] = normalized
    return base


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def normalize_custom_profile(values: dict[str, Any] | None, fallback_profile: str = "balanced") -> dict[str, Any]:
    base_name = normalize_profile_name(fallback_profile)
    if base_name == CUSTOM_PROFILE_NAME:
        base_name = "balanced"
    base = PROFILE_PRESETS[base_name].copy()

    incoming = values or {}
    normalized: dict[str, Any] = {}
    for key, (low, high) in PROFILE_RANGES.items():
        default_value = _to_float(base.get(key), low)
        source_value = _to_float(incoming.get(key), default_value)
        normalized[key] = _clamp(source_value, low, high)

    normalized["poll_seconds"] = int(round(float(normalized["poll_seconds"])))
    normalized["name"] = CUSTOM_PROFILE_NAME
    return normalized


def resolve_custom_profile(values: dict[str, Any] | None, fallback_profile: str = "balanced") -> dict[str, Any]:
    return normalize_custom_profile(values, fallback_profile=fallback_profile)


def profile_from_env(default: str = "balanced") -> dict[str, Any]:
    env_name = (
        os.getenv("ALERT_PROFILE")
        or os.getenv("V30_PROFILE")
        or default
    )
    return resolve_profile(env_name)


def _profile_state_path(root_dir: str | None = None) -> str:
    env_path = os.getenv("V30_PROFILE_STATE_FILE", "").strip()
    if env_path:
        return env_path
    base_dir = root_dir or os.getcwd()
    return os.path.join(base_dir, ".v30_profile_state.json")


def load_profile_state(root_dir: str | None = None) -> dict[str, Any] | None:
    path = _profile_state_path(root_dir)
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception:
        return None


def load_saved_profile_name(root_dir: str | None = None) -> str | None:
    payload = load_profile_state(root_dir)
    if not isinstance(payload, dict):
        return None
    value = payload.get("profile")
    if value is None:
        return None
    return normalize_profile_name(str(value))


def load_saved_custom_profile(root_dir: str | None = None) -> dict[str, Any] | None:
    payload = load_profile_state(root_dir)
    if not isinstance(payload, dict):
        return None

    value = payload.get("custom")
    if not isinstance(value, dict):
        return None

    return resolve_custom_profile(value)


def load_saved_custom_updated_at(root_dir: str | None = None) -> str | None:
    payload = load_profile_state(root_dir)
    if not isinstance(payload, dict):
        return None

    custom_ts = payload.get("custom_updated_at_utc")
    if isinstance(custom_ts, str) and custom_ts.strip():
        return custom_ts.strip()

    # Backward compatibility for old state files: if profile is custom,
    # reuse global timestamp as best-effort custom save time.
    if normalize_profile_name(str(payload.get("profile"))) == CUSTOM_PROFILE_NAME:
        updated = payload.get("updated_at_utc")
        if isinstance(updated, str) and updated.strip():
            return updated.strip()
    return None


def load_saved_snapshot_tag_filter(root_dir: str | None = None) -> str | None:
    payload = load_profile_state(root_dir)
    if not isinstance(payload, dict):
        return None
    value = payload.get("snapshot_tag_filter")
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    return normalized


def save_snapshot_tag_filter(tag_filter: str | None, root_dir: str | None = None) -> str:
    normalized = (tag_filter or "").strip().lower() or "all"
    previous = load_profile_state(root_dir) or {}
    payload: dict[str, Any] = previous.copy() if isinstance(previous, dict) else {}
    payload["snapshot_tag_filter"] = normalized
    payload["updated_at_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    path = _profile_state_path(root_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=True, indent=2)
    return normalized


def load_saved_snapshot_schema_only(root_dir: str | None = None) -> bool:
    payload = load_profile_state(root_dir)
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("snapshot_schema_only", False))


def save_snapshot_schema_only(enabled: bool, root_dir: str | None = None) -> bool:
    previous = load_profile_state(root_dir) or {}
    payload: dict[str, Any] = previous.copy() if isinstance(previous, dict) else {}
    payload["snapshot_schema_only"] = bool(enabled)
    payload["updated_at_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    path = _profile_state_path(root_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=True, indent=2)
    return bool(payload["snapshot_schema_only"])


def save_profile_name(name: str | None, root_dir: str | None = None) -> str:
    normalized = normalize_profile_name(name)
    previous = load_profile_state(root_dir) or {}
    payload: dict[str, Any] = previous.copy() if isinstance(previous, dict) else {}
    payload["profile"] = normalized
    payload["updated_at_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    existing_custom = previous.get("custom")
    if isinstance(existing_custom, dict):
        payload["custom"] = resolve_custom_profile(existing_custom)

    existing_custom_ts = previous.get("custom_updated_at_utc")
    if isinstance(existing_custom_ts, str) and existing_custom_ts.strip():
        payload["custom_updated_at_utc"] = existing_custom_ts.strip()

    path = _profile_state_path(root_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=True, indent=2)
    return normalized


def save_custom_profile(
    values: dict[str, Any],
    root_dir: str | None = None,
    selected_profile: str | None = CUSTOM_PROFILE_NAME,
) -> dict[str, Any]:
    custom = resolve_custom_profile(values)
    selected = normalize_profile_name(selected_profile)
    if selected != CUSTOM_PROFILE_NAME:
        selected = CUSTOM_PROFILE_NAME
    updated_at_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    previous = load_profile_state(root_dir) or {}
    payload: dict[str, Any] = previous.copy() if isinstance(previous, dict) else {}
    payload["profile"] = selected
    payload["custom"] = custom
    payload["updated_at_utc"] = updated_at_utc
    payload["custom_updated_at_utc"] = updated_at_utc
    path = _profile_state_path(root_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=True, indent=2)
    return custom


def profile_for_dashboard(default: str = "balanced", root_dir: str | None = None) -> dict[str, Any]:
    env_name = os.getenv("ALERT_PROFILE") or os.getenv("V30_PROFILE")
    if env_name:
        return resolve_profile(env_name)

    saved = load_saved_profile_name(root_dir)
    if saved == CUSTOM_PROFILE_NAME:
        custom = load_saved_custom_profile(root_dir)
        if custom is not None:
            return custom
    if saved is not None:
        return resolve_profile(saved)

    return resolve_profile(default)