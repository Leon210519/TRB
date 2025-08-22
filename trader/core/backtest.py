"""Backtesting utilities."""
from __future__ import annotations

from typing import Dict

import pandas as pd

from .broker import PaperBroker
from .portfolio import equal_weight_targets


def run_backtest(
    df_by_symbol: Dict[str, pd.DataFrame],
    strategy,
    cfg,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run backtest and return equity and trades DataFrames."""
    broker = PaperBroker(
        starting_eur=cfg.paper.starting_balance_eur,
        fee_bps=cfg.paper.fee_bps,
        slippage_bps=cfg.paper.slippage_bps,
    )

    signals = {sym: strategy.generate_signals(df) for sym, df in df_by_symbol.items()}
    union_index = sorted(set().union(*[df.index for df in df_by_symbol.values()]))
    prev_sig = {sym: 0 for sym in df_by_symbol}

    for ts in union_index:
        prices = {}
        current_signals = {}
        for sym, df in df_by_symbol.items():
            if ts not in df.index:
                continue
            price = df.at[ts, "close"]
            prices[sym] = price
            sig = int(signals[sym].get(ts, prev_sig[sym]))
            current_signals[sym] = sig
            if prev_sig[sym] == 0 and sig == 1:
                targets = equal_weight_targets(current_signals, cfg.risk.max_position_fraction)
                broker.buy_pct(sym, price, targets[sym])
            elif prev_sig[sym] == 1 and sig == 0:
                broker.sell_all(sym, price)
            prev_sig[sym] = sig
        broker.mark_to_market(ts, prices)

    return broker.equity_df(), broker.trades_df()


__all__ = ["run_backtest"]
