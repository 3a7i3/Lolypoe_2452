# 🚀 Crypto Quant AI Lab V16

**Multi-Exchange & AI Multi-Agent Autonomous Trading Platform**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CCXT](https://img.shields.io/badge/CCXT-4.5+-green.svg)](https://github.com/ccxt/ccxt)
[![Panel](https://img.shields.io/badge/Panel-1.3+-orange.svg)](https://panel.holoviz.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What is V16?

V16 is a **fully autonomous cryptocurrency trading platform** with:

- 🌐 **Multi-Exchange Integration** – Binance, Bybit, Kraken (via CCXT)
- 🐦 **Market Scanner** – Monitor 300+ cryptos in real-time
- 🧠 **AI Multi-Agent System** – 4 specialized agents for market analysis and trading
- 🧬 **Genetic Strategy Optimizer** – Automatically evolves trading strategies
- 📈 **Advanced Backtesting** – Walk-forward, Monte Carlo, realistic slippage/fees
- ⚠️ **Risk Management** – Kill-switch, drawdown limits, position sizing
- 🎛️ **Interactive Dashboard** – Panel + Plotly real-time monitoring
- 📊 **Portfolio Optimization** – Kelly Criterion, efficient frontier
- 🤖 **Reinforcement Learning** – Q-learning trader agent

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         CRYPTO QUANT AI LAB V16 - SYSTEM ARCHITECTURE       │
└─────────────────────────────────────────────────────────────┘

DATA LAYER
├── Exchange APIs (Binance/Bybit/Kraken)
├── Market data streams
└── On-chain data feeds

CORE INFRASTRUCTURE
├── Exchange Manager (unified multi-exchange)
├── Market Scanner (300+ cryptos, anomaly detection)
├── Portfolio Manager (Kelly allocation, rebalancing)
├── Risk Engine (max drawdown, VaR, kill-switch)
└── Execution Engine (paper + live trading)

AI AGENTS (Multi-Agent System)
├── 🔍 MarketObserver – Analyzes trends & anomalies
├── 🧬 StrategyGenerator – Creates & evolves strategies
├── 🤖 RLTrader – Q-learning agent for optimal actions
└── ⚠️ RiskEnforcer – Enforces risk policies

QUANT RESEARCH
├── Backtester (walk-forward, Monte Carlo)
└── Optimizer (Sharpe ratio, Kelly allocation)

EXECUTION
├── Paper Trading (simulation)
└── Live Trading (real orders)

VISUALIZATION
└── Dashboard V16 (Panel + Plotly, port 5011)
```

---

## 📁 Project Structure

```
crypto_quant_v16/
│
├── ai/                              # AI agents
│   ├── market_observer.py          # Market analysis agent
│   ├── strategy_generator.py        # Genetic strategy evolution
│   ├── reinforcement_trader.py      # RL trading agent
│   └── risk_enforcer.py            # Risk management agent
│
├── core/                            # Core infrastructure
│   ├── exchange_manager.py         # Multi-exchange wrapper
│   ├── market_scanner.py           # Crypto scanner + indicators
│   ├── portfolio_manager.py        # Portfolio allocation
│   ├── risk_engine.py              # Drawdown, VaR, kill-switch
│   └── execution_engine.py         # Order execution (paper/live)
│
├── quant/                           # Backtesting & optimization
│   ├── backtester.py               # Walk-forward, Monte Carlo
│   └── optimizer.py                # Portfolio optimization
│
├── ui/                              # Dashboard
│   ├── components.py               # Reusable chart/table widgets
│   └── quant_dashboard.py          # Main Panel dashboard
│
├── data/                            # Data storage
│   └── __init__.py
│
├── config.py                        # Global configuration
├── main_v16.py                      # Main orchestrator
├── launch_v16_dashboard.bat         # Windows launcher
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/crypto_quant_v16.git
cd crypto_quant_v16

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config.py` with your settings:

```python
TRADING_MODE = 'paper'  # Start with paper trading
INITIAL_CAPITAL = 10000.0
PRIMARY_EXCHANGE = 'binance'

# Add API keys (or use environment variables)
EXCHANGES = {
    'binance': {
        'apiKey': 'your-api-key',
        'secret': 'your-api-secret',
    }
}
```

### 3. Run Dashboard

**Windows:**
```bash
launch_v16_dashboard.bat
```

**Linux/Mac:**
```bash
panel serve ui/quant_dashboard.py --port 5011 --show
```

Dashboard opens at: **http://localhost:5011/quant_dashboard**

### 3b. Run Smart Dashboard V26 (with Bot Doctor)

```bash
panel serve ui/quant_dashboard_v26.py --port 5010 --show
```

This version includes:
- Smart chart overlays (BOS/CHoCH, order blocks, FVG, RSI/MACD/ATR)
- Paper trading ticket + trade journal
- Telegram alert channel (`/subscribe`, `/status`, `/mute`)
- Bot Doctor tab: automatic system audit and recommendations per refresh cycle

### 3c. Launch V30 Full Suite (Dashboard + Alerts)

1. Create env file from template:

```bash
copy .env.example .env
```

2. Fill Telegram and alert settings in `.env` (optional for Telegram).

Runtime personalization profiles:
- `conservative`
- `balanced` (default)
- `aggressive`
- `custom` (editable in dashboard)

In V26 dashboard, use **Apply Profile** to load parameters instantly, then **Save Default Profile** to persist your preferred profile across restarts.
For `custom`, edit values in the **Custom Profile** row (SL/TP, alert thresholds, RR, max stop, poll interval, regime confidence), then apply/save.
Custom mode now includes live validation status (VALID/INVALID) and blocks Apply/Save while values are out of allowed ranges.
Custom mode also displays per-field guidance with current value vs allowed range for faster tuning.
Use Reset Custom to Balanced to restore safe baseline values before fine tuning.
Use Clone Preset to Custom to start from conservative, balanced, or aggressive presets before manual edits.
Custom mode shows save state (SAVED or UNSAVED CHANGES) so you can see when edits are not persisted yet.
Use Save + Apply Custom to persist and activate custom parameters in one click.
Save + Apply Custom is enabled only when profile is `custom` and validation status is `VALID`.
Validation and save-state statuses are color-coded (green/amber/red/gray) for quicker readability.
Custom save-state panel now shows Last saved (UTC) after custom profile persistence.
Custom save-state panel also shows Last saved (Local) for operator-friendly time reading.
A Copy Timestamps button is available to copy UTC/local save timestamps (with field fallback if clipboard is blocked).
An Export Profile Snapshot button writes a JSON snapshot of current profile state, validation, and save metadata.
An Import Snapshot action can reload custom values from a snapshot JSON (uses latest local snapshot if file path is left empty).
Snapshots include `schema_version`; import accepts backward-compatible files and rejects newer unsupported schema versions.
A Snapshot Notes field can be attached to exports and is restored automatically on import.
Snapshot Notes are normalized to a compact single line and capped in length to keep snapshot files lightweight and consistent.
A Snapshot Tag field is also available for classification; it is normalized to lowercase alphanumeric plus `-`/`_`.
A Recent Snapshots list now shows local exports (with tag/date when available) and supports one-click import of the selected entry.
A Filter Tag dropdown is auto-populated from detected snapshot tags and includes `all` plus `untagged` (when available).
A detected tag list is ordered by usage frequency (most common first) for faster filtering.
A count is displayed for each filter option (for example `scalping (12)`).
A Valid schema only toggle limits the recent list to snapshots that pass schema/required-field checks.
A Snapshot Filter Info panel reports how many files were excluded by schema validation or unreadable JSON when this toggle is enabled.
A Show Excluded Files button opens a table listing excluded snapshot filenames and their primary rejection reason.
An Export Excluded CSV button writes this excluded-files table to a timestamped CSV for audit/share.
A snapshot without tag is labeled with `[untagged]` in the recent list for faster visual scanning.
A Clear button resets the filter to `all` and restores the full recent snapshot list.
A live counter in the Recent Snapshots label shows displayed/total matches after filtering.
The selected tag filter is persisted in local V30 profile state and restored on next dashboard start.
Recent Snapshot entries are displayed with local-readable datetime and sorted by exported timestamp when available.
A Snapshot Preview panel shows key metadata (tag, UTC/local export time, selected profile, validation status) before import.
A Validate Selected action checks snapshot schema and required fields without importing values.
A Dry-run Import action previews per-field custom value changes without applying them.
Apply Dry-run Result becomes available after a successful dry-run to import that exact validated snapshot in one click.
When dry-run detects more than 4 changed fields, Apply Dry-run Result requires an explicit confirmation click.
The confirmation warning includes a compact preview of changed field names.
A dry-run table lists changed fields with current/incoming values and deltas for quick review.
Dry-run deltas are color-coded in the table to highlight increases vs decreases at a glance.
Dry-run rows are ordered by absolute delta (highest impact first).
A dedicated Export Dry-run CSV action saves the current dry-run diff table for audit/review.
Saved profile file: `.v30_profile_state.json` (overridable via `V30_PROFILE_STATE_FILE`).
If `ALERT_PROFILE` or `V30_PROFILE` is set in environment, env value still has priority.

Set profile in `.env`:

```bash
ALERT_PROFILE=balanced
```

3. Launch both processes:

```bash
launch_v30_full.bat
```

PowerShell alternative:

```powershell
.\launch_v30_full.ps1
```

Direct Python launcher (recommended for logs/control):

```bash
python launch_v30_full.py
```

This runs a pre-launch healthcheck automatically.

Healthcheck only:

```bash
python launch_v30_full.py --healthcheck-only
```

Skip pre-check (not recommended):

```bash
python launch_v30_full.py --skip-healthcheck
```

Standalone healthcheck:

```bash
healthcheck_v30.bat
```

or

```powershell
.\healthcheck_v30.ps1
```

Detached mode:

```bash
python launch_v30_full.py --detached
```

This starts:
- Panel dashboard (`ui/quant_dashboard_v26.py`)
- Alert engine (`binance_alert_app.py`) with symbol/timeframe/exchange/profile from env vars

Override profile from CLI:

```bash
python launch_v30_full.py --profile conservative
python launch_v30_full.py --profile aggressive
```

V26 now includes an **Admin/Ops** tab with:
- Live process/port status
- Start/Stop controls for alert engine
- Restart Alerts one-click action
- Color health badge (HEALTHY/DEGRADED/CRITICAL) powered by `healthcheck_v30.py`
- Rolling health timeline (last 20 checks)
- One-click diagnostic JSON export
- Optional auto-refresh for Ops status
- One-click health timeline CSV export
- Transition alerts on health state changes

Monitor only (dashboard without alert engine):

```bash
monitor_v30.bat
```

or

```powershell
.\monitor_v30.ps1
```

Stop suite:

```bash
stop_v30_full.bat
```

or

```powershell
.\stop_v30_full.ps1
```

### 4. Run Autonomous Trading Loop

```bash
python main_v16.py
```

This runs the full cycle:
1. 📊 Market scan (300+ cryptos)
2. 🧬 Strategy generation & evolution
3. 📈 Portfolio optimization
4. 🎯 Trade execution (paper mode)
5. ⚠️ Risk validation

---

## 🎮 Dashboard Features

### Market Tab
- 🌐 Live crypto scanner (50+ symbols)
- 📊 Volume, volatility, 24h % change
- 🎯 Composite scoring system

### Charts Tab
- 📈 Candlestick + EMA (20/50)
- 📊 RSI(14) indicator
- 📉 MACD with histogram
- 🎛️ Coin & timeframe selectors

### Portfolio Tab
- 💼 Allocation pie chart (Kelly-weighted)
- 📈 Equity curve + drawdown
- 💰 Position P&L tracking

### Risk Tab
- ⚠️ Max drawdown monitor
- 📊 VaR 95% display
- 🚨 Kill-switch status
- 📉 Daily loss limit tracking

### Whale Radar Tab
- 🐋 Large transaction detection
- 📍 Exchange inflows/outflows
- 🚨 Anomaly alerts

### Agents Tab
- 🤖 Agent status (4 agents)
- 📊 Cycles completed
- ⏱️ Response times

### Strategy Lab Tab
- 🧬 Generated strategies (1000+)
- 📊 Backtest results
- 🏆 Top performers ranking
- 🎯 Genetic evolution progress

---

## 🤖 AI Agents

### 1. MarketObserver
Analyzes market data and detects signals:
- High volume detection
- Price extremes (pumps/dumps)
- Whale movements
- Trend detection

### 2. StrategyGenerator
Creates and evolves trading strategies:
- Genetic algorithm (crossover + mutation)
- Indicator-based strategies (RSI, EMA, MACD, VWAP)
- Fitness evaluation via backtesting
- Population evolution across generations

### 3. RLTrader
Reinforcement Learning trading agent:
- Q-learning algorithm
- State: RSI /MACD/Trend
- Actions: BUY/SELL/HOLD
- Reward: Profit/Loss
- Epsilon-greedy exploration

### 4. RiskEnforcer
Enforces risk policies:
- Position size limits (max 10% per position)
- Daily loss limits (max 5%)
- Portfolio drawdown kill-switch (max 20%)
- Rejects trades violating policies

---

## 📊 Trading Cycle

```
CYCLE START (every 60 seconds)
        ↓
   [1] SCAN MARKET
        ├─ Fetch 300+ cryptos
        ├─ Calculate indicators
        └─ Detect anomalies
        ↓
   [2] GENERATE STRATEGIES
        ├─ Create population (50 strategies)
        ├─ Backtest each
        └─ Evolve best (genetic algorithm)
        ↓
   [3] OPTIMIZE PORTFOLIO
        ├─ Calculate Kelly allocation
        └─ Rebalance if needed
        ↓
   [4] EXECUTE TRADES
        ├─ Paper mode: simulate
        └─ Live mode: real orders
        ↓
   [5] VALIDATE RISK
        ├─ Check drawdown
        ├─ Check daily loss
        ├─ Check position sizes
        └─ Kill-switch if violated
        ↓
   CYCLE END → Wait 60s → Repeat
```

---

## ⚙️ Key Features

### Backtesting Engine
- **Walk-forward analysis** – Train/test on rolling windows
- **Monte Carlo simulation** – 1000+ simulated scenarios
- **Realistic conditions** – Slippage (0.05%), fees (0.1%)
- **Risk metrics** – Sharpe, max drawdown, win rate

### Portfolio Optimization
- **Kelly Criterion** – Position sizing based on edge
- **Efficient Frontier** – Risk/return tradeoff
- **Min Variance** – Lowest volatility allocation
- **Risk-weighted** – Inverse volatility weighting

### Risk Management
- **Max Drawdown** – Default 20%, customizable
- **Daily Loss Limit** – Default 5% daily max loss
- **Position Size Limit** – Max 10% per asset
- **VaR 95%** – Value at Risk calculation

### Multi-Exchange
- **CCXT Integration** – 100+ exchanges supported
- **Automatic Fallback** – Switch if primary exchange down
- **Rate Limiting** – Automatic rate limit handling
- **Unified Interface** – Same code for all exchanges

---

## 🔧 Configuration Examples

### Paper Trading Only
```python
TRADING_MODE = 'paper'
INITIAL_CAPITAL = 10000
```

### Live Trading (Real Money)
```python
TRADING_MODE = 'live'
EXCHANGES = {
    'binance': {
        'apiKey': os.getenv('BINANCE_KEY'),
        'secret': os.getenv('BINANCE_SECRET'),
    }
}
```

### Conservative Risk
```python
MAX_PORTFOLIO_DRAWDOWN = 0.10    # 10% max drawdown
MAX_DAILY_LOSS = 0.02             # 2% daily loss limit
POSITION_SIZE_MAX = 0.05          # 5% positions
```

### Aggressive Trading
```python
MAX_PORTFOLIO_DRAWDOWN = 0.30    # 30% max drawdown
MAX_DAILY_LOSS = 0.10             # 10% daily loss limit
POSITION_SIZE_MAX = 0.20          # 20% positions
```

---

## 📈 Example Output

```
================================================================================
CYCLE 1 START at 2026-03-11 14:30:45.123456
================================================================================
📊 [CYCLE 1] Phase 1: Market Scan
🔍 MarketObserver detected 23 signals
📊 [CYCLE 1] Phase 2: Strategy Generation
🧬 Generation 1 evolved. Best Sharpe: 1.245
📊 [CYCLE 1] Phase 3: Portfolio Optimization
📊 [CYCLE 1] Phase 4: Trade Execution
📄 Paper trading mode - simulating orders
📊 [CYCLE 1] Phase 5: Risk Validation
✅ CYCLE 1 COMPLETE
   Market signals: 23
   Best strategy Sharpe: 1.245
   System risk: OK

⏱️  Waiting 60s until next cycle...
```

---

## 🐛 Troubleshooting

### Dashboard Won't Start
```bash
# Check if port 5011 is in use
netstat -an | findstr :5011  # Windows
lsof -i :5011                # Mac/Linux

# Change port in config.py
DASHBOARD_PORT = 5012
```

### API Connection Failed
```bash
# Check API keys
echo %BINANCE_API_KEY%

# Test connection
python -c "import ccxt; print(ccxt.binance().fetch_ticker('BTC/USDT'))"
```

### Memory Issues
```bash
# Reduce scanner limit
SYMBOLS_TO_SCAN = 50  # Instead of 300

# Reduce strategy population
AGENTS['strategy_generator']['population_size'] = 25
```

---

## 📚 Next Steps (V17)

- [ ] Real-time WebSocket data feeds
- [ ] Options trading support
- [ ] Multi-timeframe analysis
- [ ] Advanced ML (Random Forest, XGBoost)
- [ ] Arbitrage detection
- [ ] Liquidation level tracking
- [ ] Discord / Telegram alerts

---

## 📝 License

MIT License – Free to use and modify

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

---

## 💬 Questions?

- 📖 Check [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)
- 🎮 See [QUICK_START.md](QUICK_START.md)
- 🐛 Report issues on GitHub

---

**Built with ❤️ by the Quant AI Team**  
*Autonomous Trading • AI-Powered • Production-Ready*

**V16 Status**: ✅ PRODUCTION READY

```
         _____ 
        / ___ \
       / /   \ \
      | |  Q  | |
      | |  16 | |
       \ \   / /
        \ \___/
         \____/
       QUANT LAB
```
