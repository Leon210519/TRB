"""Walk-forward optimization."""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

import pandas as pd

from .tuner import tune, STRATEGIES
from ..core.backtest import run_backtest


TRAIN_DAYS = 180
TEST_DAYS = 30


def walk_forward(df_by_symbol, strategy_name: str, cfg):
    """Run walk-forward optimization."""
    StrategyCls = STRATEGIES[strategy_name]
    start = max(df.index[0] for df in df_by_symbol.values())
    end = min(df.index[-1] for df in df_by_symbol.values())
    equity_curves: List[pd.Series] = []
    current_equity = cfg.paper.starting_balance_eur
    best_params = None

    window_start = start
    while True:
        train_end = window_start + timedelta(days=TRAIN_DAYS)
        test_end = train_end + timedelta(days=TEST_DAYS)
        if test_end > end:
            break
        train_data = {s: df[(df.index >= window_start) & (df.index < train_end)] for s, df in df_by_symbol.items()}
        test_data = {s: df[(df.index >= train_end) & (df.index < test_end)] for s, df in df_by_symbol.items()}
        best_params = tune(train_data, strategy_name, cfg)
        strat = StrategyCls(**best_params)
        equity_df, _ = run_backtest(test_data, strat, cfg)
        rel = equity_df["equity"] / equity_df["equity"].iloc[0]
        scaled = rel * current_equity
        current_equity = scaled.iloc[-1]
        equity_curves.append(scaled)
        window_start = train_end

    oos_equity = pd.concat(equity_curves)
    return oos_equity.to_frame("equity"), best_params


__all__ = ["walk_forward"]
