"""Performance metrics."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from ..utils import timeframe_to_per_year_bars


def _trade_stats(trades: pd.DataFrame) -> pd.DataFrame:
    trades = trades.sort_values("ts")
    records = []
    entries: Dict[str, Dict] = {}
    for _, t in trades.iterrows():
        sym = t.symbol
        if t.side == "BUY":
            entries[sym] = t
        elif t.side == "SELL" and sym in entries:
            e = entries.pop(sym)
            pnl = (t.price - e.price) * t.qty - e.fee - t.fee
            records.append({"symbol": sym, "pnl": pnl})
    return pd.DataFrame(records)


def compute_metrics(equity: pd.Series, trades: pd.DataFrame, timeframe: str) -> Dict[str, float]:
    returns = equity.pct_change().dropna()
    per_year = timeframe_to_per_year_bars(timeframe)
    years = len(equity) / per_year
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1 if years > 0 else 0
    avg = returns.mean()
    vol = returns.std()
    sharpe = (avg / vol) * np.sqrt(per_year) if vol != 0 else 0
    neg = returns[returns < 0]
    downside = neg.std()
    sortino = (avg / downside) * np.sqrt(per_year) if downside != 0 else 0
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_dd = drawdown.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    trade_stats = _trade_stats(trades)
    hit_rate = (trade_stats.pnl > 0).mean() if not trade_stats.empty else 0
    profit_factor = (
        trade_stats.pnl[trade_stats.pnl > 0].sum()
        / -trade_stats.pnl[trade_stats.pnl < 0].sum()
        if (trade_stats.pnl < 0).any()
        else np.nan
    )
    avg_trade = trade_stats.pnl.mean() if not trade_stats.empty else 0

    metrics = {
        "CAGR": cagr,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "MaxDrawdown": max_dd,
        "Calmar": calmar,
        "HitRate": hit_rate,
        "ProfitFactor": profit_factor,
        "AvgTrade": avg_trade,
        "Volatility": vol * np.sqrt(per_year),
    }
    return metrics


__all__ = ["compute_metrics"]
