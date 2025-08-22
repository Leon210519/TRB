"""SQLAlchemy ORM models for the trading bot."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

from .db import engine

Base = declarative_base()


class RunType(str, Enum):
    BACKTEST = "backtest"
    PAPER = "paper"
    TUNING = "tuning"
    WFO = "wfo"


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    type = Column(SqlEnum(RunType))
    notes = Column(Text)

    snapshots = relationship("AccountSnapshot", back_populates="run")
    trades = relationship("Trade", back_populates="run")


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, index=True)
    equity = Column(Float)
    cash = Column(Float)
    positions_value = Column(Float)
    run_id = Column(Integer, ForeignKey("runs.id"))

    run = relationship("Run", back_populates="snapshots")


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, index=True)
    symbol = Column(String, index=True)
    side = Column(SqlEnum(TradeSide))
    qty = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    run_id = Column(Integer, ForeignKey("runs.id"))

    run = relationship("Run", back_populates="trades")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    qty = Column(Float)
    avg_price = Column(Float)
    run_id = Column(Integer, ForeignKey("runs.id"))


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    params_json = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    run_id = Column(Integer, ForeignKey("runs.id"))


# create tables
Base.metadata.create_all(engine)


__all__ = [
    "Run",
    "AccountSnapshot",
    "Trade",
    "Position",
    "StrategyVersion",
    "RunType",
    "TradeSide",
    "Base",
]
