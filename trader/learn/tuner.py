"""Parameter tuning using Optuna."""
from __future__ import annotations

import json
from typing import Dict

import optuna

from ..core.backtest import run_backtest
from ..core.metrics import compute_metrics
from ..strategies.sma_cross import SMACross
from ..strategies.rsi_reversion import RSIReversion

STRATEGIES = {
    "sma_cross": SMACross,
    "rsi_reversion": RSIReversion,
}


def tune(df_by_symbol, strategy_name: str, cfg) -> Dict[str, float]:
    StrategyCls = STRATEGIES[strategy_name]

    def objective(trial: optuna.Trial) -> float:
        if strategy_name == "sma_cross":
            fast = trial.suggest_int("fast", 5, 50)
            slow = trial.suggest_int("slow", fast + 10, 200)
            strat = StrategyCls(fast=fast, slow=slow)
        else:
            period = trial.suggest_int("period", 5, 50)
            buy_th = trial.suggest_int("buy_th", 10, 40)
            sell_th = trial.suggest_int("sell_th", 60, 90)
            strat = StrategyCls(period=period, buy_th=buy_th, sell_th=sell_th)
        equity, trades = run_backtest(df_by_symbol, strat, cfg)
        metrics = compute_metrics(equity["equity"], trades, cfg.timeframe)
        objective_value = metrics["CAGR"] + metrics["MaxDrawdown"]
        return objective_value

    study = optuna.create_study(direction=cfg.tuning.direction)
    study.optimize(objective, n_trials=cfg.tuning.n_trials)
    return study.best_params


__all__ = ["tune"]
