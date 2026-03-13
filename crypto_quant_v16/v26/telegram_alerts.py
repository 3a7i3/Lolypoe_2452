"""V27.4 – Telegram alert channel + command loop for the V27 dashboard.

Supports two paths:
- Push alerts from dashboard events via ``send_alert()``
- Telegram chat commands via long polling (``getUpdates``)

Commands:
- /join (quick subscribe with default levels)
- /subscribe [levels]  (e.g. /subscribe warning,error or /subscribe all)
- /alerts [levels]     (alias of /subscribe)
- /set_account <id_or_name>
- /status
- /mute
- /help
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
TELEGRAM_API_SEND = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_API_UPDATES = "https://api.telegram.org/bot{token}/getUpdates"
ALL_LEVELS: Set[str] = {"info", "warning", "error"}
DEFAULT_LEVELS: List[str] = ["warning", "error"]

# ── Runtime state ─────────────────────────────────────────────────────────────
_token: Optional[str] = None
_chats: Dict[str, Set[str]] = {}
_chat_meta: Dict[str, Dict[str, str]] = {}
_lock = threading.Lock()

_poll_thread: Optional[threading.Thread] = None
_poll_running = False
_update_offset = 0


def _state_file() -> str:
    custom = os.environ.get("V26_TELEGRAM_STATE_FILE", "").strip()
    if custom:
        return custom
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "telegram_users.json")


def _load_state() -> None:
    path = _state_file()
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return
    chats = payload.get("chats", {}) if isinstance(payload, dict) else {}
    meta = payload.get("meta", {}) if isinstance(payload, dict) else {}

    if isinstance(chats, dict):
        for cid, lvls in chats.items():
            if isinstance(cid, str) and isinstance(lvls, list):
                parsed = {str(x).strip().lower() for x in lvls if str(x).strip().lower() in ALL_LEVELS}
                _chats[cid] = parsed if parsed else set(DEFAULT_LEVELS)

    if isinstance(meta, dict):
        for cid, row in meta.items():
            if isinstance(cid, str) and isinstance(row, dict):
                acct = str(row.get("trading_account", "")).strip()
                _chat_meta[cid] = {"trading_account": acct}


def _save_state() -> None:
    path = _state_file()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "chats": {cid: sorted(lvls) for cid, lvls in _chats.items()},
            "meta": _chat_meta,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True, indent=2)
    except Exception as exc:
        logger.debug("Telegram state save failed: %s", exc)


# ── Level icons ───────────────────────────────────────────────────────────────
_ICONS: Dict[str, str] = {
    "info": "ℹ️",
    "warning": "⚠️",
    "error": "🚨",
}


# ── Initialisation ────────────────────────────────────────────────────────────

def _load_from_env() -> None:
    """Auto-configure from environment variables and/or V26 config."""
    global _token
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not tok:
        try:
            from v26.config import V26_CONFIG  # noqa: PLC0415
            tg = V26_CONFIG.get("telegram", {})
            tok = str(tg.get("bot_token", "")).strip()
        except Exception:
            pass
    if tok:
        _token = tok

    raw_ids = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not raw_ids:
        try:
            from v26.config import V26_CONFIG  # noqa: PLC0415
            tg = V26_CONFIG.get("telegram", {})
            raw_ids = str(tg.get("chat_ids", "")).strip()
        except Exception:
            pass
    if raw_ids:
        for cid in raw_ids.split(","):
            cid = cid.strip()
            if cid and cid not in _chats:
                _chats[cid] = set(DEFAULT_LEVELS)

    _load_state()


def has_token() -> bool:
    """Return True when a bot token exists (chats may still be empty)."""
    with _lock:
        if _token is None:
            _load_from_env()
        return bool(_token)


def is_configured() -> bool:
    """Return True when token + at least one subscribed chat are configured."""
    with _lock:
        if _token is None and not _chats:
            _load_from_env()
        return bool(_token) and bool(_chats)


# ── Chat management ───────────────────────────────────────────────────────────

def register_chat(chat_id: str, levels: Optional[List[str]] = None) -> None:
    """Register a chat ID (or update its subscribed levels)."""
    lvl_set = set(levels) & ALL_LEVELS if levels else set(DEFAULT_LEVELS)
    with _lock:
        _load_from_env()
        _chats[str(chat_id)] = lvl_set
        if str(chat_id) not in _chat_meta:
            _chat_meta[str(chat_id)] = {"trading_account": ""}
        _save_state()
    logger.info("Telegram: registered chat %s -> levels %s", chat_id, sorted(lvl_set))


def set_chat_levels(chat_id: str, levels: List[str]) -> None:
    """Update subscribed levels for an existing chat."""
    with _lock:
        if str(chat_id) in _chats:
            _chats[str(chat_id)] = set(levels) & ALL_LEVELS
            _save_state()


def set_trading_account(chat_id: str, account: str) -> None:
    with _lock:
        _load_from_env()
        cid = str(chat_id)
        if cid not in _chats:
            _chats[cid] = set(DEFAULT_LEVELS)
        _chat_meta[cid] = {"trading_account": str(account).strip()}
        _save_state()


def mute_chat(chat_id: str) -> None:
    """Remove a chat from subscription registry."""
    with _lock:
        _chats.pop(str(chat_id), None)
        _chat_meta.pop(str(chat_id), None)
        _save_state()
    logger.info("Telegram: muted chat %s", chat_id)


def get_registered_chats() -> Dict[str, List[str]]:
    """Return snapshot of chat -> sorted levels."""
    with _lock:
        return {cid: sorted(lvls) for cid, lvls in _chats.items()}


# ── Bot API helpers ───────────────────────────────────────────────────────────

def _send_one(token: str, chat_id: str, text: str) -> None:
    """POST a single message to one chat."""
    import requests  # noqa: PLC0415
    try:
        resp = requests.post(
            TELEGRAM_API_SEND.format(token=token),
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=8,
        )
        if resp.status_code != 200:
            logger.warning("Telegram sendMessage failed [%s]: %s", chat_id, resp.text[:200])
    except Exception as exc:
        logger.debug("Telegram request error [%s]: %s", chat_id, exc)


def _get_updates(token: str, offset: int) -> List[dict]:
    """Long-poll Telegram updates and return message updates only."""
    import requests  # noqa: PLC0415
    try:
        resp = requests.post(
            TELEGRAM_API_UPDATES.format(token=token),
            json={"offset": offset, "timeout": 25, "allowed_updates": ["message"]},
            timeout=35,
        )
        if resp.status_code != 200:
            logger.debug("Telegram getUpdates non-200: %s", resp.status_code)
            return []
        payload = resp.json()
        if not payload.get("ok"):
            return []
        result = payload.get("result")
        return result if isinstance(result, list) else []
    except Exception as exc:
        logger.debug("Telegram getUpdates error: %s", exc)
        return []


def _dispatch(token: str, targets: List[str], text: str) -> None:
    for cid in targets:
        _send_one(token, cid, text)


# ── Alert sending ─────────────────────────────────────────────────────────────

def send_alert(level: str, key: str, message: str) -> None:
    """Send one dashboard alert to subscribed chats (non-blocking)."""
    with _lock:
        if not _chats:
            _load_from_env()
        if not _token or not _chats:
            return
        token = _token
        targets = [cid for cid, lvls in _chats.items() if level in lvls]

    if not targets:
        return

    icon = _ICONS.get(level, "🔔")
    text = f"{icon} <b>V27 Alert</b> [{level.upper()}]\n<code>{key}</code>\n{message}"
    t = threading.Thread(target=_dispatch, args=(token, targets, text), daemon=True, name=f"tg_alert_{key}")
    t.start()


# ── Command parsing (/subscribe /alerts /status /mute /help) ─────────────────

def _parse_levels(arg_tokens: List[str]) -> List[str]:
    """Parse levels from command args; defaults to warning+error."""
    if not arg_tokens:
        return list(DEFAULT_LEVELS)

    raw: List[str] = []
    for tok in arg_tokens:
        raw.extend([x.strip().lower() for x in tok.split(",") if x.strip()])

    if "all" in raw:
        return ["info", "warning", "error"]
    if "none" in raw:
        return []

    levels = [lvl for lvl in ["info", "warning", "error"] if lvl in raw]
    return levels if levels else list(DEFAULT_LEVELS)


def _help_text() -> str:
    return (
        "<b>V27 Telegram Commands</b>\n"
        "/join - quick subscribe with default levels\n"
        "/subscribe [info,warning,error|all] - set alert levels\n"
        "/alerts [levels] - alias of /subscribe\n"
        "/set_account &lt;id_or_name&gt; - attach trading account metadata\n"
        "/status - show your subscriptions\n"
        "/mute - unsubscribe this chat\n"
        "/help - show this help"
    )


def _handle_command(chat_id: str, text: str) -> str:
    parts = [p for p in str(text or "").strip().split() if p]
    if not parts:
        return ""
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in {"/start", "/help"}:
        return _help_text()

    if cmd == "/join":
        register_chat(chat_id, list(DEFAULT_LEVELS))
        return "Joined. Alerts enabled with levels: <b>warning, error</b>"

    if cmd in {"/subscribe", "/alerts"}:
        levels = _parse_levels(args)
        if levels:
            register_chat(chat_id, levels)
            return f"Subscribed with levels: <b>{', '.join(levels)}</b>"
        mute_chat(chat_id)
        return "Muted. Use /subscribe warning,error to re-enable alerts."

    if cmd == "/set_account":
        if not args:
            return "Usage: /set_account <id_or_name>"
        account = " ".join(args).strip()
        set_trading_account(chat_id, account)
        return f"Trading account saved: <b>{account}</b>"

    if cmd == "/mute":
        mute_chat(chat_id)
        return "Alerts muted for this chat."

    if cmd == "/status":
        with _lock:
            lvls = sorted(_chats.get(chat_id, set()))
            n = len(_chats)
            account = str((_chat_meta.get(chat_id, {}) or {}).get("trading_account", "")).strip()
        if lvls:
            account_line = f"\nTrading account: <b>{account}</b>" if account else "\nTrading account: <b>not set</b>"
            return f"Your levels: <b>{', '.join(lvls)}</b>{account_line}\nTotal subscribed chats: <b>{n}</b>"
        return f"This chat is not subscribed.\nUse /subscribe warning,error\nTotal subscribed chats: <b>{n}</b>"

    return "Unknown command. Use /help"


# ── Polling loop ──────────────────────────────────────────────────────────────

def _poll_loop() -> None:
    """Telegram long-poll loop for command handling."""
    global _update_offset
    while True:
        with _lock:
            running = _poll_running
            token = _token
        if not running:
            return
        if not token:
            time.sleep(3)
            continue

        updates = _get_updates(token, _update_offset)
        if not updates:
            continue

        for upd in updates:
            try:
                uid = int(upd.get("update_id", 0))
                if uid >= _update_offset:
                    _update_offset = uid + 1

                msg = upd.get("message") or {}
                txt = str(msg.get("text") or "").strip()
                chat = msg.get("chat") or {}
                chat_id = str(chat.get("id") or "").strip()
                if not txt or not chat_id or not txt.startswith("/"):
                    continue

                reply = _handle_command(chat_id, txt)
                if reply:
                    _send_one(token, chat_id, reply)
            except Exception as exc:
                logger.debug("Telegram command parse error: %s", exc)


def start_command_loop() -> bool:
    """Start Telegram command loop (idempotent). Returns True if running."""
    global _poll_running, _poll_thread
    with _lock:
        _load_from_env()
        if not _token:
            return False
        if _poll_thread is not None and _poll_thread.is_alive():
            return True
        _poll_running = True
        _poll_thread = threading.Thread(target=_poll_loop, daemon=True, name="tg_command_loop")
        _poll_thread.start()
        return True


def stop_command_loop() -> None:
    """Signal command loop to stop (used mainly for tests/shutdown)."""
    global _poll_running
    with _lock:
        _poll_running = False


def command_loop_status() -> str:
    """Return command loop status for UI diagnostics."""
    with _lock:
        running = _poll_thread is not None and _poll_thread.is_alive() and _poll_running
    return "running" if running else "stopped"


# ── Convenience helpers ───────────────────────────────────────────────────────

def status_summary() -> str:
    """Return compact status line for Feed Quality pane."""
    if not has_token():
        return "Telegram: token missing (set TELEGRAM_BOT_TOKEN)"
    chats = get_registered_chats()
    return (
        f"Telegram: {len(chats)} chat(s) subscribed; "
        f"commands: {command_loop_status()}"
    )
