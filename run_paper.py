"""Run live paper trading loop."""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import pandas as pd

from trader.config import load_config
from trader.core.backtest import run_backtest
from trader.core.broker import PaperBroker
from trader.core.portfolio import equal_weight_targets
from trader.core.risk import DailyRiskManager
from trader.data.feed import fetch_ohlcv, poll_latest
from trader.logging_conf import setup_logging
from trader.strategies.sma_cross import SMACross
from trader.strategies.rsi_reversion import RSIReversion
from trader.storage.db import get_session
from trader.storage.models import AccountSnapshot, Run, RunType, Trade, StrategyVersion
from trader.utils import timeframe_to_seconds

STRATS = {"sma_cross": SMACross, "rsi_reversion": RSIReversion}

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exchange")
    parser.add_argument("--symbols")
    parser.add_argument("--timeframe")
    parser.add_argument("--timeout-ms", type=int, dest="timeout_ms")
    parser.add_argument("--proxies-http")
    parser.add_argument("--proxies-https")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()
    cfg = load_config()
    if args.exchange:
        cfg.exchange = args.exchange
    if args.symbols:
        cfg.symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if args.timeframe:
        cfg.timeframe = args.timeframe
    if args.timeout_ms:
        cfg.network.timeout_ms = args.timeout_ms
    if args.proxies_http:
        cfg.proxies.http = args.proxies_http
    if args.proxies_https:
        cfg.proxies.https = args.proxies_https
    logger.info(
        "Settings: exchange=%s symbols=%s timeframe=%s timeout_ms=%s proxies=%s",
        cfg.exchange,
        cfg.symbols,
        cfg.timeframe,
        cfg.network.timeout_ms,
        {k: v for k, v in {"http": cfg.proxies.http, "https": cfg.proxies.https}.items() if v},
    )
    params = cfg.strategy.params
    if Path("config.last_params.json").exists():
        params = json.loads(Path("config.last_params.json").read_text())
    strategy_cls = STRATS[cfg.strategy.name]
    strategy = strategy_cls(**params)

    data = {
        s: fetch_ohlcv(cfg.exchange, s, cfg.timeframe, cfg.data.lookback_limit, cfg)
        for s in cfg.symbols
    }
    signals = {s: strategy.generate_signals(df) for s, df in data.items()}
    last_ts = {s: df.index[-1] for s, df in data.items()}
    prev_sig = {s: int(signals[s].iloc[-1]) for s in data}

    broker = PaperBroker(
        starting_eur=cfg.paper.starting_balance_eur,
        fee_bps=cfg.paper.fee_bps,
        slippage_bps=cfg.paper.slippage_bps,
    )
    risk_mgr = DailyRiskManager(cfg.risk.max_daily_loss_fraction)

    with get_session() as session:
        run = Run(type=RunType.PAPER)
        session.add(run)
        session.flush()
        session.add(StrategyVersion(name=strategy.name(), params_json=json.dumps(params), run_id=run.id))
        session.commit()
        run_id = run.id

    poll_interval = 60
    tf_seconds = timeframe_to_seconds(cfg.timeframe)
    logger.info("Starting paper trading loop")
    while True:
        try:
            prices = {}
            for sym in cfg.symbols:
                latest = poll_latest(cfg.exchange, sym, cfg.timeframe, cfg)
                ts = latest.index[-1]
                price = latest["close"].iloc[-1]
                if ts > last_ts[sym]:
                    df = data[sym].append(latest).drop_duplicates()
                    data[sym] = df
                    signals[sym] = strategy.generate_signals(df)
                    last_ts[sym] = ts
                prices[sym] = price
                sig = int(signals[sym].iloc[-1])
                if prev_sig[sym] == 0 and sig == 1 and risk_mgr.allow_trading():
                    targets = equal_weight_targets({s: int(signals[s].iloc[-1]) for s in cfg.symbols}, cfg.risk.max_position_fraction)
                    broker.buy_pct(sym, price, targets[sym])
                elif prev_sig[sym] == 1 and sig == 0:
                    broker.sell_all(sym, price)
                prev_sig[sym] = sig
            ts = pd.Timestamp.utcnow()
            broker.mark_to_market(ts, prices)
            equity = broker.snapshots[-1]["equity"]
            risk_mgr.update(ts.to_pydatetime(), equity)
            with get_session() as session:
                snap = broker.snapshots[-1]
                session.add(AccountSnapshot(ts=snap["ts"], equity=snap["equity"], cash=snap["cash"], positions_value=snap["positions_value"], run_id=run_id))
                for t in broker.trades:
                    if "saved" in t:
                        continue
                    session.add(Trade(ts=t["ts"], symbol=t["symbol"], side=t["side"], qty=t["qty"], price=t["price"], fee=t["fee"], run_id=run_id))
                    t["saved"] = True
                session.commit()
            logger.info("Heartbeat equity=%.2f", equity)
            time.sleep(poll_interval)
        except Exception as exc:
            logger.exception("Error in live loop: %s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
