"""RSI mean reversion strategy."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .base import Strategy


def rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, adjust=False).mean()
    ma_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))


@dataclass
class RSIReversion(Strategy):
    period: int
    buy_th: int
    sell_th: int

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        r = rsi(df["close"], self.period)
        regime = pd.Series(0, index=df.index)
        long = r < self.buy_th
        flat = r > self.sell_th
        regime[long] = 1
        regime[flat] = 0
        regime = regime.replace(to_replace=0, method="ffill").fillna(0)
        return regime

    def name(self) -> str:
        return "rsi_reversion"

    def params(self) -> dict:
        return {"period": self.period, "buy_th": self.buy_th, "sell_th": self.sell_th}


__all__ = ["RSIReversion"]
