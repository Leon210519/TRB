"""Streamlit dashboard for the trading bot."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ..config import load_config
from ..core.backtest import run_backtest
from ..core.metrics import compute_metrics
from ..data.feed import fetch_ohlcv
from ..strategies.sma_cross import SMACross
from ..strategies.rsi_reversion import RSIReversion
from ..storage.db import get_session
from ..storage.models import AccountSnapshot, Run, RunType, Trade

STRATS = {
    "sma_cross": SMACross,
    "rsi_reversion": RSIReversion,
}


cfg = load_config()
net = cfg.network
proxies = cfg.proxies.dict(exclude_none=True)
st.set_page_config(page_title="Trader Dashboard", layout="wide")
st.title("Paper Trading Dashboard")
try:
    fetch_ohlcv(
        cfg.exchange,
        cfg.symbols[0],
        cfg.timeframe,
        1,
        timeout_ms=net.timeout_ms,
        max_retries=net.max_retries,
        backoff_base_ms=net.backoff_base_ms,
        user_agent=net.user_agent,
        proxies=proxies,
    )
except Exception:  # pragma: no cover - network failure
    st.warning(
        "Initial market data fetch failed. Run python scripts/selftest_connection.py or configure proxies/timeouts."
    )

# sidebar -------------------------------------------------------
with st.sidebar:
    st.header("Parameters")
    st.write(f"Exchange: {cfg.exchange}")
    st.write(f"Timeframe: {cfg.timeframe}")
    st.write(f"Timeout (ms): {net.timeout_ms}")
    strategy_name = st.selectbox("Strategy", list(STRATS.keys()), index=0)
    if st.checkbox("Use last tuned params") and Path("config.last_params.json").exists():
        params = json.loads(Path("config.last_params.json").read_text())
    else:
        if strategy_name == "sma_cross":
            fast = st.number_input("fast", 5, 200, 20)
            slow = st.number_input("slow", fast + 1, 400, 50)
            params = {"fast": fast, "slow": slow}
        else:
            period = st.number_input("period", 5, 50, 14)
            buy_th = st.number_input("buy_th", 10, 40, 30)
            sell_th = st.number_input("sell_th", 60, 90, 70)
            params = {"period": period, "buy_th": buy_th, "sell_th": sell_th}
    symbols = st.multiselect("Symbols", cfg.symbols, default=cfg.symbols)
    run_bt = st.button("Run backtest")

# database view -------------------------------------------------
with get_session() as session:
    run = (
        session.query(Run)
        .filter(Run.type == RunType.PAPER)
        .order_by(Run.started_at.desc())
        .first()
    )
    if run:
        snaps = pd.read_sql(session.query(AccountSnapshot).filter(AccountSnapshot.run_id == run.id).statement, session.bind)
        trades = pd.read_sql(session.query(Trade).filter(Trade.run_id == run.id).statement, session.bind)
    else:
        snaps = pd.DataFrame()
        trades = pd.DataFrame()

if not snaps.empty:
    st.subheader("Equity Curve")
    fig = px.line(snaps, x="ts", y="equity")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No live data yet")

if run_bt:
    strat = STRATS[strategy_name](**params)
    data = {
        s: fetch_ohlcv(
            cfg.exchange,
            s,
            cfg.timeframe,
            cfg.data.lookback_limit,
            timeout_ms=net.timeout_ms,
            max_retries=net.max_retries,
            backoff_base_ms=net.backoff_base_ms,
            user_agent=net.user_agent,
            proxies=proxies,
        )
        for s in symbols
    }
    equity_df, trades_df = run_backtest(data, strat, cfg)
    metrics = compute_metrics(equity_df["equity"], trades_df, cfg.timeframe)
    st.subheader("Backtest Metrics")
    st.write(metrics)
    fig = px.line(equity_df, y="equity")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Trades")
    st.write(trades_df.tail(100))

st.subheader("Recent Trades (Live)")
if not trades.empty:
    st.write(trades.tail(100))
else:
    st.write("No trades yet")
