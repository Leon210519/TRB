"""Paper trading broker implementation."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from ..utils import apply_slippage
from ..storage.models import TradeSide

logger = logging.getLogger(__name__)


@dataclass
class PaperBroker:
    """Very simple paper broker."""

    starting_eur: float
    fee_bps: float
    slippage_bps: float
    cash: float = field(init=False)
    positions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    trades: List[Dict] = field(default_factory=list)
    snapshots: List[Dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cash = self.starting_eur

    # trading -------------------------------------------------
    def buy_pct(self, symbol: str, price: float, pct_of_cash: float) -> None:
        """Buy using a percentage of current cash."""
        notional = self.cash * pct_of_cash
        qty = notional / price
        exec_price = apply_slippage(price, self.slippage_bps, "BUY")
        cost = qty * exec_price
        fee = cost * self.fee_bps / 10000
        self.cash -= cost + fee
        pos = self.positions.get(symbol, {"qty": 0.0, "avg_price": 0.0})
        total_qty = pos["qty"] + qty
        if total_qty != 0:
            pos["avg_price"] = (pos["qty"] * pos["avg_price"] + qty * exec_price) / total_qty
        pos["qty"] = total_qty
        self.positions[symbol] = pos
        self.trades.append({
            "ts": pd.Timestamp.utcnow(),
            "symbol": symbol,
            "side": TradeSide.BUY.value,
            "qty": qty,
            "price": exec_price,
            "fee": fee,
        })

    def sell_all(self, symbol: str, price: float) -> None:
        pos = self.positions.get(symbol)
        if not pos or pos["qty"] <= 0:
            return
        qty = pos["qty"]
        exec_price = apply_slippage(price, self.slippage_bps, "SELL")
        proceeds = qty * exec_price
        fee = proceeds * self.fee_bps / 10000
        self.cash += proceeds - fee
        pos["qty"] = 0
        self.positions[symbol] = pos
        self.trades.append({
            "ts": pd.Timestamp.utcnow(),
            "symbol": symbol,
            "side": TradeSide.SELL.value,
            "qty": qty,
            "price": exec_price,
            "fee": fee,
        })

    # accounting ------------------------------------------------
    def mark_to_market(self, ts: pd.Timestamp, prices: Dict[str, float]) -> None:
        positions_value = sum(pos["qty"] * prices.get(sym, 0) for sym, pos in self.positions.items())
        equity = self.cash + positions_value
        self.snapshots.append({
            "ts": ts,
            "equity": equity,
            "cash": self.cash,
            "positions_value": positions_value,
        })

    def equity_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.snapshots).set_index("ts")

    def trades_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.trades)


__all__ = ["PaperBroker"]
