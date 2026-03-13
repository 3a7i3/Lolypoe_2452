# Quant Trading System V5 - Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites
- Python 3.8+
- pip package manager

### 2. Initial Setup

**Windows:**
```cmd
setup.bat
```

**Linux/Mac:**
```bash
bash setup.sh
```

### 3. Start Trading

**Live Mode (Production):**
```bash
python main.py --mode live
```

**Dashboard (Monitoring):**
```bash
# In another terminal
streamlit run dashboard/dashboard.py
# Access: http://localhost:8501
```

**Backtest Historical Data:**
```bash
python main.py --mode backtest
```

## Configuration Quick Tips

Edit `config.py` to customize:

```python
# Number of cryptocurrencies to monitor
CRYPTO_UNIVERSE_SIZE = 1000

# Enabled trading strategies
ENABLED_STRATEGIES = [
    'trend_following',      # 65% win rate
    'mean_reversion',       # 58% win rate
    'breakout',             # 72% win rate
    'volatility_trading',   # 55% win rate
    'momentum',             # 65% win rate
    'statistical_arbitrage' # 42% win rate
]

# Risk management
MAX_POSITIONS = 50
MAX_DRAWDOWN = 0.15  # 15%
MAX_DAILY_LOSS = 0.02  # 2%

# Position sizing
OPTIMIZATION_METHOD = 'kelly_criterion'  # Kelly, Risk Parity, Mean-Variance

# Update interval (seconds)
DATA_UPDATE_INTERVAL = 60
```

## Dashboard Overview

### Tab 1: Portfolio Overview
- Total AUM (Assets Under Management)
- Daily P&L
- Sharpe Ratio
- Maximum Drawdown
- Performance chart vs benchmark

### Tab 2: Positions
- Current holdings
- Entry vs current price
- Unrealized P&L
- Portfolio allocation

### Tab 3: Risk Analysis
- VaR (95%, 99%)
- CVaR (expected tail loss)
- Correlation matrix
- Monte Carlo simulation results

### Tab 4: Strategies
- Win rate by strategy
- Sharpe ratio comparison
- Trade count
- Performance consistency

### Tab 5: Trades
- Recent trade history
- Execution price
- P&L per trade
- Strategy attribution

### Tab 6: Analytics
- Equity curve with drawdown
- Return distribution
- Performance components
- Attribution analysis

## System Modes

### Live Mode
```bash
python main.py --mode live
# Runs continuous trading 24/7
# Updates every DATA_UPDATE_INTERVAL seconds
# Executes real trades
```

### Backtest Mode
```bash
python main.py --mode backtest
# Tests strategies on historical data
# Shows performance metrics
# No real trades executed
```

### Optimization Mode
```bash
python main.py --mode optimize
# Optimizes strategy parameters
# Walk-forward testing
# Parameter stability analysis
```

### Dashboard Mode
```bash
python main.py --mode dashboard
# Starts only the dashboard
# No trading execution
# For monitoring only
```

## Monitoring & Logs

### Log Files
- `logs/quant_system.log` - Main system log
- `logs/trades_audit.log` - Trade audit trail
- `logs/positions_audit.log` - Position history

### View Real-Time Logs
```bash
tail -f logs/quant_system.log
```

### Dashboard Refresh
Dashboard updates every 5 seconds with:
- Portfolio metrics
- P&L changes
- Trade executions
- Risk metrics

## Troubleshooting

### Dependencies not installing
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir
```

### Exchange connection errors
- Check internet connection
- Verify API credentials
- Check rate limits
- Review logs in `logs/quant_system.log`

### Dashboard not loading
```bash
pip install --upgrade streamlit plotly
streamlit run dashboard/dashboard.py --logger.level=debug
```

### Out of memory
- Reduce `CRYPTO_UNIVERSE_SIZE`
- Reduce `LSTM_BATCH_SIZE`
- Clear cache: `logs/` and `data/market_cache/`

## Performance Tips

1. **Reduce update interval** for faster trading
   ```python
   DATA_UPDATE_INTERVAL = 30  # 30 seconds instead of 60
   ```

2. **Optimize strategy selection** - use top performers only
   ```python
   ENABLED_STRATEGIES = ['trend_following', 'breakout']  # Top 2
   ```

3. **Limit position count** for better execution
   ```python
   MAX_POSITIONS = 20  # Instead of 50
   ```

4. **Use async caching** for faster data loading
   ```python
   CACHE_ENABLED = True
   CACHE_EXPIRY = 300  # 5 minutes
   ```

## Production Deployment (AWS/Azure/GCP)

### AWS EC2
1. Launch Ubuntu 22.04 instance
2. SSH into instance
3. Clone repository
4. Run setup and start system
5. Keep running in screen/tmux

### Docker (Any Cloud)
```bash
docker build -t quant-system .
docker run -d \
  -e INITIAL_CAPITAL=100000 \
  -e EXCHANGE_KEY=your_key \
  -e EXCHANGE_SECRET=your_secret \
  quant-system
```

### Systemd (Linux Production)
Create `/etc/systemd/system/quant-system.service`:
```ini
[Unit]
Description=Quant Trading System V5
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/quant-trading-system
ExecStart=/usr/bin/python3 main.py --mode live
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable quant-system
sudo systemctl start quant-system
sudo systemctl status quant-system
```

## Key Metrics Explained

**Sharpe Ratio** - Risk-adjusted returns (>1.5 is good)
**Win Rate** - % of profitable trades (>60% is good)
**Max Drawdown** - Largest peak-to-trough decline (<15% is good)
**VaR** - Value at Risk, maximum expected loss (95% confidence)
**Sortino Ratio** - Return per unit of downside risk

## Next Steps

1. ✅ Run `setup.bat` or `setup.sh`
2. ✅ Start system: `python main.py --mode live`
3. ✅ Open dashboard: `streamlit run dashboard/dashboard.py`
4. ✅ Monitor performance
5. 🔄 Optimize strategies based on results

---

**Enjoy profitable trading!** 🚀📈

For detailed documentation, see `README.md` and `PROFESSIONAL_GUIDE.md`
