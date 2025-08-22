#!/usr/bin/env python3
"""Connectivity smoke test for exchange access."""
from __future__ import annotations

import pathlib
import random
import sys
import time
import urllib.request

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from trader.config import load_config
from trader.data.feed import _exchange, fetch_ohlcv


def main() -> None:
    cfg = load_config()
    net = cfg.network
    proxies = cfg.proxies.dict(exclude_none=True)
    ex = _exchange(cfg.exchange, timeout_ms=net.timeout_ms, user_agent=net.user_agent, proxies=proxies)

    ok = True

    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
        opener.addheaders = [("User-Agent", net.user_agent)]
        opener.open(ex.urls["api"]["public"], timeout=net.timeout_ms / 1000)
        print("DNS/SSL: PASS")
    except Exception as exc:  # pragma: no cover - network failure
        print(f"DNS/SSL: FAIL {exc}")
        ok = False

    try:
        for attempt in range(1, net.max_retries + 1):
            try:
                ex.load_markets()
                print("Market load: PASS")
                break
            except Exception as exc:
                if attempt == net.max_retries:
                    raise
                delay = net.backoff_base_ms * (2 ** (attempt - 1)) / 1000.0
                delay += random.uniform(0, delay)
                time.sleep(delay)
        else:
            pass
    except Exception as exc:  # pragma: no cover - network failure
        print(f"Market load: FAIL {exc}")
        ok = False

    try:
        fetch_ohlcv(
            cfg.exchange,
            "BTC/USDT",
            "1h",
            50,
            timeout_ms=net.timeout_ms,
            max_retries=net.max_retries,
            backoff_base_ms=net.backoff_base_ms,
            user_agent=net.user_agent,
            proxies=proxies,
        )
        print("OHLCV: PASS")
    except Exception as exc:  # pragma: no cover - network failure
        print(f"OHLCV: FAIL {exc}")
        ok = False

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
