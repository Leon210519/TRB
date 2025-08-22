"""Run walk-forward optimization."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from trader.config import load_config
from trader.data.feed import fetch_ohlcv
from trader.learn.walkforward import walk_forward
from trader.logging_conf import setup_logging
from trader.storage.db import get_session
from trader.storage.models import Run, RunType, StrategyVersion


def main() -> None:
    setup_logging()
    cfg = load_config()
    data = {
        s: fetch_ohlcv(cfg.exchange, s, cfg.timeframe, cfg.data.lookback_limit)
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
