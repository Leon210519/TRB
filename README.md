# Paper Trading Crypto Bot

This repository implements an end-to-end paper trading system for cryptocurrencies. It supports
backtesting, walk‑forward optimization, nightly tuning and a Streamlit dashboard. All trading is
simulated – **no real orders are ever sent**.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to change exchange, symbols, strategy parameters and risk limits. All timestamps
are handled in UTC.

## Running

* Historical backtest
  ```bash
  python run_backtest.py
  ```
* Parameter tuning with Optuna
  ```bash
  python run_tune.py
  ```
* Walk‑forward optimization
  ```bash
  python run_wfo.py
  ```
* Start paper trading loop (runs until interrupted)
  ```bash
  python run_paper.py
  ```
* Dashboard
  ```bash
  streamlit run trader/webapp/app_streamlit.py
  ```

Backtest, tuning and live runs persist their results to `trader.sqlite`. The `runs/` folder contains
CSV exports for inspection.

## Strategies

Strategies are pluggable. Add a new strategy by subclassing `trader.strategies.base.Strategy` and
implementing `generate_signals`. See `sma_cross.py` or `rsi_reversion.py` for examples.

## Notes

* The broker is a paper implementation with configurable fees and slippage. Negative balances are
  allowed to mimic margin.
* The bot performs **nightly walk‑forward optimization** and never learns online during live
  trading. This avoids in‑sample bias and makes results reproducible.
* Always use public market data from ccxt. The live loop polls REST endpoints and never connects to
  private endpoints.

## Connectivity Test and Network Settings

Internet access is required to pull market data. Verify connectivity and exchange access with:

```bash
python scripts/selftest_connection.py
```

If you operate behind a proxy, set `HTTP_PROXY`/`HTTPS_PROXY` environment variables or specify
`proxies.http` and `proxies.https` in `config.yaml`. All runner scripts (`run_backtest.py`,
`run_paper.py`, `run_tune.py`, `run_wfo.py`) accept optional CLI overrides such as
`--exchange`, `--symbols`, `--timeframe`, `--timeout-ms`, `--proxies-http`, and `--proxies-https`.

The smoke test and runners use the configured timeout (default 20s) and retry with exponential
backoff. If the dashboard shows a connectivity warning, run the self-test or adjust the network
settings.
