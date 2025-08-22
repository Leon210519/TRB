"""Run walk-forward optimization."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from trader.config import load_config
from trader.data.feed import fetch_ohlcv
from trader.learn.walkforward import walk_forward
from trader.logging_conf import setup_logging
from trader.storage.db import get_session
from trader.storage.models import Run, RunType, StrategyVersion


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
    logger = logging.getLogger(__name__)
    logger.info(
        "Settings: exchange=%s symbols=%s timeframe=%s timeout_ms=%s proxies=%s",
        cfg.exchange,
        cfg.symbols,
        cfg.timeframe,
        cfg.network.timeout_ms,
        {k: v for k, v in {"http": cfg.proxies.http, "https": cfg.proxies.https}.items() if v},
    )
    data = {
        s: fetch_ohlcv(cfg.exchange, s, cfg.timeframe, cfg.data.lookback_limit, cfg)
        for s in cfg.symbols
    }
    equity, params = walk_forward(data, cfg.strategy.name, cfg)
    print("Suggested params", params)
    Path("config.last_params.json").write_text(json.dumps(params))
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    equity.to_csv(runs_dir / f"wfo_{ts}_equity.csv")
    with get_session() as session:
        run = Run(type=RunType.WFO)
        session.add(run)
        session.flush()
        session.add(
            StrategyVersion(name=cfg.strategy.name, params_json=json.dumps(params), run_id=run.id)
        )
        session.commit()


if __name__ == "__main__":
    main()
