"""Risk management utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DailyRiskManager:
    max_daily_loss_fraction: float

    def __post_init__(self) -> None:
        self.day_start_equity: float | None = None
        self.circuit_breaker = False
        self.current_day: datetime | None = None

    def update(self, ts: datetime, equity: float) -> None:
        ts_day = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
        if self.current_day != ts_day:
            self.current_day = ts_day
            self.day_start_equity = equity
            self.circuit_breaker = False
        if self.day_start_equity and equity < self.day_start_equity * (1 - self.max_daily_loss_fraction):
            self.circuit_breaker = True

    def allow_trading(self) -> bool:
        return not self.circuit_breaker


__all__ = ["DailyRiskManager"]
