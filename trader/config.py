"""Configuration loading using Pydantic."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import os

import yaml
from pydantic import BaseModel, Field, validator


class PaperConfig(BaseModel):
    starting_balance_eur: float
    fee_bps: int = Field(ge=0)
    slippage_bps: int = Field(ge=0)


class RiskConfig(BaseModel):
    max_position_fraction: float
    max_daily_loss_fraction: float
    circuit_breaker_drawdown: float


class StrategyConfig(BaseModel):
    name: str
    params: Dict[str, Any]


class DataConfig(BaseModel):
    lookback_limit: int
    cache_minutes: int = 0


class TuningConfig(BaseModel):
    n_trials: int = 50
    direction: str = "maximize"


class ScheduleConfig(BaseModel):
    retrain_hour_utc: int = Field(ge=0, le=23)


class NetworkConfig(BaseModel):
    timeout_ms: int = 20000
    max_retries: int = 5
    backoff_base_ms: int = 500
    user_agent: str = "TraderBot/1.0"


class ProxiesConfig(BaseModel):
    http: Optional[str] = None
    https: Optional[str] = None


class Config(BaseModel):
    exchange: str
    symbols: List[str]
    timeframe: str
    paper: PaperConfig
    risk: RiskConfig
    strategy: StrategyConfig
    data: DataConfig
    tuning: TuningConfig
    schedule: ScheduleConfig
    network: NetworkConfig = NetworkConfig()
    proxies: ProxiesConfig = ProxiesConfig()


def load_config(path: str | Path = "config.yaml") -> Config:
    """Load configuration from YAML file."""
    with open(path, "r", encoding="utf8") as fh:
        raw = yaml.safe_load(fh)
    cfg = Config(**raw)
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    if http_proxy:
        cfg.proxies.http = http_proxy
    if https_proxy:
        cfg.proxies.https = https_proxy
    return cfg


__all__ = ["Config", "load_config"]
