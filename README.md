# 🤖 MetaTrader 5 SMC/PA Algorithmic Trading Bot & Backtest Suite

A professional, multi-threaded algorithmic trading bot and backtesting engine developed in Python for **MetaTrader 5 (MT5)**. The system relies on **Smart Money Concepts (SMC)** and **Price Action (PA)** principles combined with **Exponential Moving Average (EMA)** trend filtering, dynamic ATR risk management, high-impact news protection, and real-time Telegram alerts.

---

## 🎯 Project Purpose

To develop an automated trading architecture that:
- Executes multi-pair trend and pattern analysis in real time
- Applies strict capital preservation and dynamic position sizing rules
- Filters high-impact macroeconomic news risks automatically
- Validates strategies through multi-pair backtests over historical market data

---

## 🚀 Features

- **Multi-Currency Architecture:** Concurrent scanning across `EURUSD`, `GBPUSD`, `USDJPY`, and `AUDUSD`[cite: 2, 6].
- **Trend & Pattern Confluence:**
  - Higher Timeframe (`H4`) EMA 50 / 200 trend filtering for directional alignment[cite: 1, 6, 10].
  - Lower Timeframe (`M15`) Engulfing patterns and Liquidity Sweep / Wick Trap validation[cite: 1, 6, 10].
- **Dynamic Risk & Capital Management:**
  - Automated lot sizing calculated directly from account equity risk percentage[cite: 9].
  - Real-time Free Margin verification to prevent margin calls[cite: 9].
  - Configurable Risk-to-Reward ratio (Default 1:3 R:R).
  - Automated Break-Even adjustment once price reaches 1.2 R:R profit[cite: 1, 4, 6].
- **High-Momentum Early Entry:** Live candle momentum evaluation for early execution on high-conviction moves[cite: 2, 10].
- **Economic News Guard:** Automated news filter blocking positions during high-impact events (NFP, CPI, FOMC).
- **Telegram Integration:** Instant HTML notifications upon order placement and position modification[cite: 2, 5, 8].
- **Backtesting Suite:** Quantitative simulation engine evaluating performance metrics over 5,000+ historical candles per pair[cite: 1, 6].

---

## 📋 Requirements

Python 3.10+ and MetaTrader 5 terminal are required. Required libraries:
MetaTrader5>=5.0.45
pandas>=1.5.0
pandas_ta>=0.3.14b
requests>=2.28.0
---

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME

Install required libraries:
pip install -r requirements.txt

Configure API keys and risk parameters:
Edit config.py with your Telegram credentials and strategy parameters.

💻 Usage
To run multi-pair backtest comparison:
python multi_backtest.py

To run single-pair backtest:
python backtest.py

To launch live algorithmic trading:
Ensure MT5 terminal is open with Algo Trading enabled, then run:
python main.py

📁 Project Structure
.
├── config.py           # Core configuration, pair list, risk parameters, and API keys
├── connector.py        # MT5 terminal connection, rate fetching, and account metrics
├── strategy.py         # Strategy logic: H4 trend, Engulfing patterns, and Wick Traps
├── risk_manager.py     # Position sizing, Free Margin check, and ATR SL/TP calculation
├── executor.py         # Order execution, filling mode selection, and Break-Even management
├── news_filter.py      # Macroeconomic event guard using external calendar APIs
├── notifier.py         # Telegram notification handler
├── main.py             # Live trading execution loop
├── backtest.py         # Single-pair backtesting module
└── multi_backtest.py   # Multi-pair comparative backtest suite

📊 Backtest Output Metrics
The backtest suite generates detailed summary tables including:
Total Trades Executed
Win / Loss / Break-Even Breakdown
Win Rate Percentage (%)
Net Profit / Loss ($)
Final Account Balance ($)

⚠️ Important Notes
MetaTrader 5 terminal must be active and logged into your broker account for live trading.
High-impact news filtering relies on external economic calendar endpoints.
Always test automated algorithms on demo accounts prior to live capital deployment.

🐛 Known Issues
Broker filling modes (FOK, IOC, RETURN) may vary across instruments; handled dynamically in executor.py.
MetaTrader 5 connection drops will pause the cycle until reconnection occurs.

🤝 Contributing
Suggestions, feature requests, and pull requests are welcome. Feel free to open an issue.

📞 Contact
For questions or feedback regarding the project, feel free to reach out via GitHub.

This project was developed for educational and research purposes only. Algorithmic trading involves financial risk.