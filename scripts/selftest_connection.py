"""Connectivity smoke test for market data access."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ensure project root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader.config import load_config
from trader.data.feed import call_with_retries, fetch_ohlcv, make_exchange


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exchange")
    parser.add_argument("--timeout-ms", type=int, dest="timeout_ms")
    parser.add_argument("--proxies-http")
    parser.add_argument("--proxies-https")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config()
    if args.exchange:
        cfg.exchange = args.exchange
    if args.timeout_ms:
        cfg.network.timeout_ms = args.timeout_ms
    if args.proxies_http:
        cfg.proxies.http = args.proxies_http
    if args.proxies_https:
        cfg.proxies.https = args.proxies_https

    ok = True
    try:
        ex = make_exchange(cfg.exchange, cfg)
        call_with_retries(lambda: ex.fetch_time(), cfg.network, "fetch_time")
        print("DNS/SSL: PASS")
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"DNS/SSL: FAIL - {exc}")
        ok = False

    if ok:
        try:
            call_with_retries(lambda: ex.load_markets(), cfg.network, "load_markets")
            print("Market load: PASS")
        except Exception as exc:  # pragma: no cover - network dependent
            print(f"Market load: FAIL - {exc}")
            ok = False

    if ok:
        try:
            fetch_ohlcv(cfg.exchange, "BTC/USDT", "1h", 50, cfg)
            print("OHLCV: PASS")
        except Exception as exc:  # pragma: no cover - network dependent
            print(f"OHLCV: FAIL - {exc}")
            ok = False

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
