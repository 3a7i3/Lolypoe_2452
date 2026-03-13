# Quick Start Guide – Crypto Quant V16

## Installation (2 minutes)

```bash
cd crypto_quant_v16
pip install -r requirements.txt
```

## Running the System

### Option 1: Launch Dashboard (Recommended)

**Windows:**
```bash
launch_v16_dashboard.bat
```

**Linux/Mac:**
```bash
panel serve ui/quant_dashboard.py --port 5011 --show
```

Then open: **http://localhost:5011/quant_dashboard**

Dashboard features 7 tabs:
- Market (300+ cryptos scanner)
- Charts (candlestick + RSI + MACD)
- Portfolio (allocation + equity curve)
- Risk (drawdown monitor)
- Whales (anomaly detection)
- Agents (4 AI agents status)
- Strategy Lab (1000+ strategies)

### Option 2: Run Autonomous Trading Loop

```bash
python main_v16.py
```

This runs the complete trading cycle:
1. Scan 300+ cryptos
2. Generate 50 strategies
3. Evolve strategies (genetic algorithm)
4. Optimize portfolio (Kelly allocation)
5. Execute trades (paper mode)
6. Validate risk limits

Output shows each phase with metrics.

### Option 3: Run Single System Test

```bash
python -c "
import asyncio
from config import CONFIG
from main_v16 import QuantSystemV16

system = QuantSystemV16(CONFIG)
print(system.get_system_status())
"
```

## Key Files

| File | Purpose |
|------|---------|
| `config.py` | Global configuration (APIs, parameters, risk limits) |
| `main_v16.py` | Main orchestrator (runs trading cycles) |
| `ui/quant_dashboard.py` | Panel dashboard interface |
| `core/*.py` | Exchange, scanner, portfolio, risk, execution |
| `ai/*.py` | 4 AI agents (observer, generator, RL trader, enforcer) |
| `quant/*.py` | Backtesting and portfolio optimization |
| `requirements.txt` | Python dependencies |
| `launch_v16_dashboard.bat` | Windows launcher script |

## Configuration

Edit `config.py` to customize:

```python
# Trading mode
TRADING_MODE = 'paper'  # or 'live'

# Capital
INITIAL_CAPITAL = 10000.0

# Risk limits
MAX_PORTFOLIO_DRAWDOWN = 0.20  # 20% max drawdown
MAX_DAILY_LOSS = 0.05           # 5% daily max loss
POSITION_SIZE_MAX = 0.10        # 10% per position

# Exchanges with API keys
EXCHANGES = {
    'binance': {
        'apiKey': 'your-key',
        'secret': 'your-secret'
    }
}

# Portfolio allocation
PORTFOLIO_ALLOCATION = {
    'BTC': 0.35,
    'ETH': 0.25,
    'SOL': 0.15,
    'AVAX': 0.15,
    'LINK': 0.10
}
```

## System Architecture

```
DATA LAYER
  ↓
CORE INFRASTRUCTURE (5 modules)
  ↓
AI AGENTS (4 specialized agents)
  ↓
QUANT ENGINES (backtester + optimizer)
  ↓
EXECUTION (paper or live trading)
  ↓
DASHBOARD + MONITORING
```

## What Each Agent Does

| Agent | Role | Action |
|-------|------|--------|
| **MarketObserver** | Analyzes market trends | Detects high volume, price spikes, whales |
| **StrategyGenerator** | Creates trading strategies | Genetic algorithm evolution, 1000 strategies |
| **RLTrader** | Learns optimal trades | Q-learning with rewards |
| **RiskEnforcer** | Prevents losses | Enforces position limits, daily loss cap, kill-switch |

## Trading Cycle (60s)

```
[1] SCAN (300+ cryptos) → Detect anomalies → 23 signals
    ↓
[2] GENERATE (50 strategies) → Backtest → Evolve → Best Sharpe 1.245
    ↓
[3] OPTIMIZE (Portfolio) → Calculate Kelly allocation → BTC:35%, ETH:25%
    ↓
[4] EXECUTE (Paper mode) → Simulate orders → 5 trades
    ↓
[5] RISK CHECK → Max DD OK, Daily loss OK → Status: RUNNING
    ↓
WAIT 60s → REPEAT
```

## Example Output

```
============================================================
CYCLE 1 START at 2026-03-11 14:30:45
============================================================
📊 Phase 1: Market Scan
   MarketObserver detected 23 signals
📊 Phase 2: Strategy Generation
   Generation 1 evolved. Best Sharpe: 1.245
📊 Phase 3: Portfolio Optimization
   Allocation updated (Kelly weighted)
📊 Phase 4: Trade Execution
   5 trades executed (paper mode)
📊 Phase 5: Risk Validation
   Status: OK | Max DD: 2.3% | Daily Loss: -0.5%
============================================================
✅ CYCLE 1 COMPLETE – Waiting 60s
```

## Testing Without Live APIs

V16 works **completely offline** using simulated data:
- Market data: Synthetic prices + indicators
- Strategies: Genetic evolution on simulated returns
- Trading: Paper mode with virtual portfolio
- Backtesting: Monte Carlo on real historical patterns

Perfect for testing before going live!

## Troubleshooting

**Dashboard won't start on port 5011:**
```bash
# Check if port is in use
netstat -an | findstr :5011

# Use different port
panel serve ui/quant_dashboard.py --port 5012
```

**Import errors:**
```bash
# Re-install dependencies
pip install -r requirements.txt --force-reinstall
```

**System runs slow:**
```python
# In config.py, reduce:
num_symbols = 50  # Instead of 300
population_size = 25  # Instead of 50
```

## Next Steps

1. ✅ Run dashboard (see live data)
2. ✅ Run main_v16.py (see trading cycles)
3. ✅ Add API keys to config.py (for real data)
4. ✅ Test on paper mode first
5. ✅ Monitor risk dashboard
6. ✅ Switch to live mode when ready

## Support

- Full docs: See [README.md](README.md)
- Configuration: See [config.py](config.py)
- Dashboard: http://localhost:5011/quant_dashboard
- Logs: Check console output

---

**V16 Status:** Production Ready ✅

Good luck trading! 🚀
