"""Market data helpers using ccxt."""
from __future__ import annotations

import logging
import random
import time
from typing import Callable, Dict

import ccxt
import pandas as pd

from ..config import Config, NetworkConfig, ProxiesConfig

logger = logging.getLogger(__name__)


def make_exchange(name: str, cfg: Config | None = None) -> ccxt.Exchange:
    """Instantiate a ccxt exchange with network settings."""
    network = cfg.network if cfg else NetworkConfig()
    proxies = cfg.proxies if cfg else ProxiesConfig()
    params: Dict[str, object] = {
        "enableRateLimit": True,
        "timeout": network.timeout_ms,
        "userAgent": network.user_agent,
    }
    proxy_map = {k: v for k, v in {"http": proxies.http, "https": proxies.https}.items() if v}
    if proxy_map:
        params["proxies"] = proxy_map
    cls = getattr(ccxt, name)
    return cls(params)


def call_with_retries(fn: Callable[[], any], network: NetworkConfig, desc: str) -> any:
    """Execute ``fn`` with exponential backoff and jitter."""
    for attempt in range(network.max_retries):
        try:
            return fn()
        except ccxt.NetworkError as exc:  # pragma: no cover - network dependent
            if attempt == network.max_retries - 1:
                raise RuntimeError(f"{desc} failed after {network.max_retries} attempts: {exc}") from exc
            delay = (network.backoff_base_ms / 1000) * (2**attempt)
            delay += random.uniform(0, network.backoff_base_ms) / 1000
            time.sleep(delay)


def fetch_ohlcv(
    exchange_name: str,
    symbol: str,
    timeframe: str,
    limit: int,
    cfg: Config | None = None,
) -> pd.DataFrame:
    """Fetch OHLCV data and return DataFrame with UTC index."""
    ex = make_exchange(exchange_name, cfg)
    network = cfg.network if cfg else NetworkConfig()
    raw = call_with_retries(
        lambda: ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit), network, "fetch_ohlcv"
    )
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts")
    return df


def poll_latest(
    exchange_name: str, symbol: str, timeframe: str, cfg: Config | None = None
) -> pd.DataFrame:
    """Poll the latest bar for a symbol."""
    return fetch_ohlcv(exchange_name, symbol, timeframe, limit=1, cfg=cfg)


__all__ = ["fetch_ohlcv", "poll_latest", "make_exchange", "call_with_retries"]
