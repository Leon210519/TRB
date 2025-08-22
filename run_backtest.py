"""Run historical backtest."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

from trader.config import load_config
from trader.data.feed import fetch_ohlcv
from trader.core.backtest import run_backtest
from trader.core.metrics import compute_metrics
from trader.logging_conf import setup_logging
from trader.strategies.sma_cross import SMACross
from trader.strategies.rsi_reversion import RSIReversion
from trader.storage.db import get_session
from trader.storage.models import AccountSnapshot, Run, RunType, Trade, StrategyVersion

STRATS = {"sma_cross": SMACross, "rsi_reversion": RSIReversion}
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run historical backtest")
    parser.add_argument("--exchange")
    parser.add_argument("--symbols")
    parser.add_argument("--timeframe")
    parser.add_argument("--timeout-ms", type=int)
    parser.add_argument("--proxies-http")
    parser.add_argument("--proxies-https")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()
    cfg = load_config()
    updates = {}
    if args.exchange:
        updates["exchange"] = args.exchange
    if args.symbols:
        updates["symbols"] = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if args.timeframe:
        updates["timeframe"] = args.timeframe
    if updates:
        cfg = cfg.copy(update=updates)
    if args.timeout_ms:
        cfg.network.timeout_ms = args.timeout_ms
    if args.proxies_http:
        cfg.proxies.http = args.proxies_http
    if args.proxies_https:
        cfg.proxies.https = args.proxies_https

    proxies = cfg.proxies.dict(exclude_none=True)
    logger.info(
        "settings exchange=%s symbols=%s timeframe=%s timeout_ms=%s proxies=%s",
        cfg.exchange,
        cfg.symbols,
        cfg.timeframe,
        cfg.network.timeout_ms,
        proxies,
    )
    strategy_cls = STRATS[cfg.strategy.name]
    strategy = strategy_cls(**cfg.strategy.params)
    data = {
        s: fetch_ohlcv(
            cfg.exchange,
            s,
            cfg.timeframe,
            cfg.data.lookback_limit,
            timeout_ms=cfg.network.timeout_ms,
            max_retries=cfg.network.max_retries,
            backoff_base_ms=cfg.network.backoff_base_ms,
            user_agent=cfg.network.user_agent,
            proxies=proxies,
        )
        for s in cfg.symbols
    }
    equity_df, trades_df = run_backtest(data, strategy, cfg)
    metrics = compute_metrics(equity_df["equity"], trades_df, cfg.timeframe)
    print(metrics)

    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    equity_df.to_csv(runs_dir / f"backtest_{ts}_equity.csv")
    trades_df.to_csv(runs_dir / f"backtest_{ts}_trades.csv", index=False)
    pd.Series(metrics).to_csv(runs_dir / f"backtest_{ts}_metrics.csv")

    with get_session() as session:
        run = Run(type=RunType.BACKTEST)
        session.add(run)
        session.flush()
        session.add(
            StrategyVersion(
                name=strategy.name(),
                params_json=json.dumps(strategy.params()),
                run_id=run.id,
            )
        )
        for _, row in equity_df.reset_index().iterrows():
            session.add(
                AccountSnapshot(
                    ts=row["ts"],
                    equity=row["equity"],
                    cash=row.get("cash", 0),
                    positions_value=row.get("positions_value", row["equity"] - row.get("cash", 0)),
                    run_id=run.id,
                )
            )
        for _, row in trades_df.iterrows():
            session.add(
                Trade(
                    ts=row["ts"],
                    symbol=row["symbol"],
                    side=row["side"],
                    qty=row["qty"],
                    price=row["price"],
                    fee=row["fee"],
                    run_id=run.id,
                )
            )
        session.commit()


if __name__ == "__main__":
    main()
