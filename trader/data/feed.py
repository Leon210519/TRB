"""Market data helpers using ccxt."""
from __future__ import annotations

import logging
import random
import time
from typing import Dict, Optional

import ccxt
import pandas as pd

from ..config import load_config

logger = logging.getLogger(__name__)


def _exchange(
    name: str,
    timeout_ms: int = 20000,
    user_agent: str = "TraderBot/1.0",
    proxies: Optional[Dict[str, str]] = None,
) -> ccxt.Exchange:
    cls = getattr(ccxt, name)
    params = {"enableRateLimit": True, "timeout": timeout_ms, "userAgent": user_agent}
    if proxies:
        params["proxies"] = proxies
    ex = cls(params)
    return ex


def fetch_ohlcv(
    exchange_name: str,
    symbol: str,
    timeframe: str,
    limit: int,
    *,
    timeout_ms: int | None = None,
    max_retries: int | None = None,
    backoff_base_ms: int | None = None,
    user_agent: str | None = None,
    proxies: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Fetch OHLCV data and return DataFrame with UTC index."""
    if None in (timeout_ms, max_retries, backoff_base_ms, user_agent):
        cfg = load_config()
        net = cfg.network
        timeout_ms = timeout_ms or net.timeout_ms
        max_retries = max_retries or net.max_retries
        backoff_base_ms = backoff_base_ms or net.backoff_base_ms
        user_agent = user_agent or net.user_agent
        proxies = proxies or cfg.proxies.dict(exclude_none=True)

    ex = _exchange(exchange_name, timeout_ms=timeout_ms, user_agent=user_agent, proxies=proxies)
    last_exc: Exception | None = None
    for attempt in range(1, (max_retries or 1) + 1):
        try:
            raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            break
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as exc:
            last_exc = exc
            if attempt == max_retries:
                logger.error("fetch_ohlcv failed after %s attempts: %s", attempt, exc)
                raise RuntimeError(f"fetch_ohlcv failed after {attempt} attempts: {exc}") from exc
            delay = (backoff_base_ms or 0) * (2 ** (attempt - 1)) / 1000.0
            delay += random.uniform(0, delay)
            logger.warning("fetch_ohlcv retry %s/%s: %s", attempt, max_retries, exc)
            time.sleep(delay)
        except Exception as exc:  # pragma: no cover
            logger.error("fetch_ohlcv failed: %s", exc)
            raise
    else:
        # Should not happen but keeps mypy happy
        raise RuntimeError(f"fetch_ohlcv failed: {last_exc}")

    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts")
    return df


def poll_latest(
    exchange_name: str,
    symbol: str,
    timeframe: str,
    *,
    timeout_ms: int | None = None,
    max_retries: int | None = None,
    backoff_base_ms: int | None = None,
    user_agent: str | None = None,
    proxies: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Poll the latest bar for a symbol."""
    return fetch_ohlcv(
        exchange_name,
        symbol,
        timeframe,
        limit=1,
        timeout_ms=timeout_ms,
        max_retries=max_retries,
        backoff_base_ms=backoff_base_ms,
        user_agent=user_agent,
        proxies=proxies,
    )


__all__ = ["fetch_ohlcv", "poll_latest"]
