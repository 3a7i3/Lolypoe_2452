from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from v26.ai_assistant import breakout_signal, detect_trend, generate_trade, momentum_signal, volatility_state
from v26.config import V26_CONFIG
from v26.data_simulator import generate_ohlcv, generate_orderbook, get_data_source
from v26.regime_engine import detect_regime
from v26.runtime_profile import profile_from_env, resolve_profile
from v26.smart_chart import detect_bos, detect_choch, enrich_indicators, orderbook_depth


@dataclass
class Snapshot:
    symbol: str
    timeframe: str
    source: str
    close_price: float
    trend: str
    momentum: str
    breakout: str
    volatility: str
    regime: str
    regime_conf: float
    bos: str
    choch: str
    depth_imbalance: float
    trade_type: str | None
    trade_entry: float | None
    trade_stop: float | None
    trade_take_profit: float | None
    trade_rr: float | None


class TelegramNotifier:
    def __init__(self, token: str | None, chat_id: str | None, enabled: bool = True) -> None:
        self.token = (token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self.enabled = enabled

    @property
    def ready(self) -> bool:
        return bool(self.enabled and self.token and self.chat_id)

    def send(self, message: str) -> bool:
        if not self.ready:
            print("[Notifier] Telegram disabled or missing TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID")
            return False

        base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")

        try:
            req = urllib.request.Request(base_url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                ok = 200 <= resp.status < 300
            if ok:
                print("[Notifier] Telegram alert sent")
            return ok
        except Exception as exc:
            print(f"[Notifier] Telegram send failed: {exc}")
            return False


class BinanceAlertApp:
    def __init__(
        self,
        symbol: str,
        timeframe: str,
        exchange_name: str,
        poll_seconds: int,
        notifier: TelegramNotifier,
        min_regime_conf: float = 0.65,
        sl_pct: float = 0.02,
        tp_pct: float = 0.04,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange_name = exchange_name
        self.poll_seconds = poll_seconds
        self.notifier = notifier
        self.min_regime_conf = min_regime_conf
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct
        self.last_fingerprint: str | None = None
        self.last_regime: str | None = None
        self.last_trade_type: str | None = None

    def _build_snapshot(self) -> Snapshot:
        raw = generate_ohlcv(
            symbol=self.symbol,
            timeframe=self.timeframe,
            limit=int(V26_CONFIG["history_limit"]),
            exchange_name=self.exchange_name,
        )
        df = enrich_indicators(raw)

        df["BOS"] = detect_bos(df, lookback=int(V26_CONFIG["lookback_bos"]))
        df["CHOCH"] = detect_choch(df, lookback=int(V26_CONFIG["lookback_choch"]))

        close_price = float(df["close"].iloc[-1])
        trend = detect_trend(df)
        momentum = momentum_signal(df)
        breakout = breakout_signal(df)
        volatility = volatility_state(df)

        regime_info = detect_regime(df)
        regime = str(regime_info["regime"])
        regime_conf = float(regime_info["confidence"])

        bos = str(df["BOS"].iloc[-1])
        choch = str(df["CHOCH"].iloc[-1])

        orderbook = generate_orderbook(close_price, symbol=self.symbol, exchange_name=self.exchange_name)
        depth = orderbook_depth(orderbook)

        trade = generate_trade(
            df,
            sl_pct=float(self.sl_pct),
            tp_pct=float(self.tp_pct),
        )

        source = get_data_source(self.symbol, self.timeframe, self.exchange_name)

        return Snapshot(
            symbol=self.symbol,
            timeframe=self.timeframe,
            source=source,
            close_price=close_price,
            trend=trend,
            momentum=momentum,
            breakout=breakout,
            volatility=volatility,
            regime=regime,
            regime_conf=regime_conf,
            bos=bos,
            choch=choch,
            depth_imbalance=float(depth["imbalance"]),
            trade_type=str(trade["type"]) if trade else None,
            trade_entry=float(trade["entry"]) if trade else None,
            trade_stop=float(trade["stop"]) if trade else None,
            trade_take_profit=float(trade["take_profit"]) if trade else None,
            trade_rr=float(trade["rr"]) if trade else None,
        )

    def _fingerprint(self, snap: Snapshot) -> str:
        compact = {
            "symbol": snap.symbol,
            "timeframe": snap.timeframe,
            "breakout": snap.breakout,
            "regime": snap.regime,
            "trade_type": snap.trade_type,
            "bos": snap.bos,
            "choch": snap.choch,
            "momentum": snap.momentum,
        }
        encoded = json.dumps(compact, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _should_alert(self, snap: Snapshot, fp: str) -> bool:
        breakout_event = snap.breakout in {"BREAKOUT_UP", "BREAKOUT_DOWN"}
        regime_shift = self.last_regime is not None and self.last_regime != snap.regime and snap.regime_conf >= self.min_regime_conf
        trade_event = self.last_trade_type != snap.trade_type and snap.trade_type is not None
        first_run = self.last_fingerprint is None

        # First run sends an initialization alert; then only send on meaningful changes.
        return first_run or breakout_event or regime_shift or trade_event or (fp != self.last_fingerprint)

    def _format_message(self, snap: Snapshot) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        trade_block = "<b>Trade:</b> NONE"
        if snap.trade_type is not None:
            trade_block = (
                f"<b>Trade:</b> {snap.trade_type} | "
                f"entry={snap.trade_entry:.2f} | stop={snap.trade_stop:.2f} | "
                f"tp={snap.trade_take_profit:.2f} | rr={snap.trade_rr:.2f}"
            )

        return (
            f"<b>BINANCE ALERT</b>\n"
            f"<b>Time:</b> {ts}\n"
            f"<b>Pair:</b> {snap.symbol} ({snap.timeframe})\n"
            f"<b>Data:</b> {snap.source}\n"
            f"<b>Price:</b> {snap.close_price:.2f}\n"
            f"<b>Trend:</b> {snap.trend} | <b>Momentum:</b> {snap.momentum}\n"
            f"<b>Breakout:</b> {snap.breakout} | <b>Vol:</b> {snap.volatility}\n"
            f"<b>Regime:</b> {snap.regime} ({snap.regime_conf:.0%})\n"
            f"<b>BOS:</b> {snap.bos} | <b>CHOCH:</b> {snap.choch}\n"
            f"<b>Depth imbalance:</b> {snap.depth_imbalance:+.3f}\n"
            f"{trade_block}"
        )

    def run_once(self) -> None:
        snap = self._build_snapshot()
        fp = self._fingerprint(snap)

        line = (
            f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {snap.symbol} {snap.timeframe} | "
            f"price={snap.close_price:.2f} trend={snap.trend} breakout={snap.breakout} "
            f"regime={snap.regime}({snap.regime_conf:.0%}) source={snap.source}"
        )
        print(line)

        if self._should_alert(snap, fp):
            msg = self._format_message(snap)
            self.notifier.send(msg)

        self.last_fingerprint = fp
        self.last_regime = snap.regime
        self.last_trade_type = snap.trade_type

    def run_forever(self) -> None:
        print(
            "Starting BinanceAlertApp "
            f"symbol={self.symbol} timeframe={self.timeframe} exchange={self.exchange_name} poll={self.poll_seconds}s"
        )
        while True:
            try:
                self.run_once()
            except Exception as exc:
                print(f"[ERROR] Alert cycle failed: {exc}")
            time.sleep(self.poll_seconds)


def parse_args() -> argparse.Namespace:
    env_profile = profile_from_env()
    parser = argparse.ArgumentParser(description="Binance alert app (no exchange API key required)")
    parser.add_argument("--symbol", default=os.getenv("ALERT_SYMBOL", "BTC/USDT"))
    parser.add_argument("--timeframe", default=os.getenv("ALERT_TIMEFRAME", "1h"))
    parser.add_argument("--exchange", default=os.getenv("ALERT_EXCHANGE", "binance"))
    parser.add_argument("--profile", default=str(env_profile["name"]), choices=["conservative", "balanced", "aggressive"])
    parser.add_argument("--poll", type=int, default=int(os.getenv("ALERT_POLL_SECONDS", str(env_profile["poll_seconds"]))))
    parser.add_argument("--min-regime-conf", type=float, default=None)
    parser.add_argument("--oneshot", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram sending")
    return parser.parse_args()


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def main() -> None:
    _load_env_file()
    args = parse_args()
    runtime_profile = resolve_profile(args.profile)
    min_regime_conf = (
        float(args.min_regime_conf)
        if args.min_regime_conf is not None
        else float(runtime_profile["min_regime_conf"])
    )

    notifier = TelegramNotifier(
        token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=not args.no_telegram,
    )

    app = BinanceAlertApp(
        symbol=args.symbol,
        timeframe=args.timeframe,
        exchange_name=str(args.exchange),
        poll_seconds=args.poll,
        notifier=notifier,
        min_regime_conf=min_regime_conf,
        sl_pct=float(runtime_profile["sl_pct"]),
        tp_pct=float(runtime_profile["tp_pct"]),
    )

    print(
        "[Profile] "
        f"{runtime_profile['name']} sl={runtime_profile['sl_pct']:.3f} tp={runtime_profile['tp_pct']:.3f} "
        f"min_regime_conf={min_regime_conf:.2f} poll={args.poll}s"
    )

    if args.oneshot:
        app.run_once()
        return

    try:
        app.run_forever()
    except KeyboardInterrupt:
        print("Stopped by user")


if __name__ == "__main__":
    main()
