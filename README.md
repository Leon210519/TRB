# Crypto Paper Trading Bot

This project is a Python-based crypto trading bot designed for **paper trading** only.  
It uses live and historical data from cryptocurrency exchanges via the `ccxt` library,  
runs backtests, simulates trades with a virtual balance, and provides a web dashboard  
using Streamlit to visualize results.

## Features (planned)
- Fetch historical and live OHLCV data from exchanges  
- Multiple strategies (SMA crossover, RSI reversion, and more)  
- Backtesting with transaction costs and slippage  
- Paper trading with a starting balance of 10,000 EUR (balance can go negative)  
- Risk management rules such as max position size and drawdown limits  
- Walk-forward optimization and offline learning using Optuna  
- Streamlit dashboard with equity curves, trades, and performance metrics  
- SQLite database for persisting runs, trades, and strategy parameters  
