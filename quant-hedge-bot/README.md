# Quant Hedge Bot - Enterprise Trading Platform

## 📊 Overview

Quant Hedge Bot is a sophisticated quantitative trading platform designed for hedge fund operations. It combines multiple trading strategies, machine learning predictions, and comprehensive risk management into a single, modular platform.

## 🏗️ Architecture

```
quant-hedge-bot/
├── config.py                 # Central configuration (100+ parameters)
├── main.py                  # Main orchestrator - BOT EXECUTION ENGINE
├── requirements.txt         # Python dependencies
│
├── data/                    # Market data storage
│   ├── market_cache/       # Real-time market snapshots
│   ├── historical/         # Historical OHLCV data
│   └── trades/            # Trade history logs
│
├── core/                    # Business logic layer
│   ├── market_scanner.py        # Market scanning & monitoring
│   ├── data_pipeline.py         # Data cleaning & normalization
│   ├── indicators_engine.py     # Technical indicators (10+ types)
│   ├── strategy_engine.py       # Signal generation logic
│   ├── ai_predictor.py         # ML price predictions
│   ├── portfolio_manager.py    # Portfolio allocation & tracking
│   ├── risk_engine.py          # Comprehensive risk management
│   └── trade_executor.py       # Trade execution & logging
│
├── quant/                   # Research & optimization layer
│   ├── backtester.py           # Historical backtesting engine
│   ├── optimizer.py            # Strategy parameter optimization
│   ├── feature_engineering.py  # Feature creation (10+ features)
│   ├── regime_detection.py     # Market regime classification
│   └── anomaly_detection.py    # Anomaly & outlier detection
│
├── ai/                      # Machine learning layer
│   ├── train_model.py          # RandomForest model training
│   ├── lstm_model.py          # LSTM time-series forecasting
│   └── reinforcement_agent.py # Q-Learning adaptive agent
│
├── dashboard/               # Visualization layer
│   ├── dashboard.py            # Streamlit web interface
│   └── live_monitor.py        # Real-time metrics tracking
│
└── utils/                   # Foundation utilities
    ├── logger.py               # Centralized logging
    ├── database.py            # SQLite persistence
    └── notifier.py            # Alert system (Telegram/Email/Slack)
```

## 🚀 Quick Start

### 1. Installation

```bash
cd quant-hedge-bot
pip install -r requirements.txt
```

### 2. Configuration

Edit `config.py` to customize:
- Trading symbols and pairs
- Capital allocation and position sizing
- Indicator parameters (SMA, RSI, MACD, etc.)
- Risk management rules
- Notification channels

### 3. Run Single Cycle

```bash
python main.py
```

### 4. Run Continuous Trading

Set `SCHEDULE_ENABLED = True` in `config.py`, then:

```bash
python main.py
```

### 5. Monitor in Dashboard

```bash
streamlit run dashboard/dashboard.py
```

## 📈 Core Features

### Signal Generation
- **Multi-indicator strategy**: SMA crossovers + RSI + MACD
- **Confidence scoring**: Signal reliability assessment
- **Regime filtering**: Adapt signals to market conditions

### Risk Management
- **Position sizing**: Equal weight, risk-parity, momentum allocation
- **Stop-loss & take-profit**: Automated with intelligent levels
- **Trailing stops**: 5% default threshold, adjustable
- **Drawdown limits**: Maximum daily/total portfolio drawdown
- **Risk metrics**: Sharpe ratio, Sortino ratio, Value at Risk

### Machine Learning
- **Price prediction**: RandomForest 5-period forecasts
- **Trend detection**: Historical SMA + ADX based regime
- **LSTM scaffolding**: Time-series deep learning ready
- **Q-Learning agent**: Reinforcement learning for adaptive trading

### Market Analysis
- **Anomaly detection**: Statistical outliers + volume spikes
- **Regime detection**: BULL/BEAR/SIDEWAYS classification
- **Feature engineering**: 10+ technical features pre-computed
- **Market scanner**: Top gainers/losers, volume filters

### Backtesting & Optimization
- **Historical backtesting**: Full equity curve analysis
- **Parameter optimization**: Grid search for best configuration
- **Slippage & commission**: Realistic cost modeling
- **Trade statistics**: Win rate, ROI, Sharpe ratio

## 📊 Trading Workflow

```
1. MARKET SCANNING
   ↓ Fetch latest price data for all symbols
   ↓ Apply volume and price filters
   
2. DATA PROCESSING
   ↓ Clean data, handle missing values
   ↓ Add technical indicators (10+ types)
   ↓ Engineer features (momentum, volatility, trend)
   
3. REGIME & ANOMALY DETECTION
   ↓ Classify market regime (BULL/BEAR/SIDEWAYS)
   ↓ Detect statistical anomalies
   ↓ Identify volume spikes
   
4. SIGNAL GENERATION
   ↓ Generate multi-indicator signals
   ↓ Calculate confidence scores
   ↓ Filter with regime bias
   
5. PORTFOLIO MANAGEMENT
   ↓ Calculate optimal capital allocation
   ↓ Size positions according to strategy
   ↓ Rebalance existing positions
   
6. RISK VALIDATION
   ↓ Check portfolio drawdown limits
   ↓ Verify daily loss constraints
   ↓ Validate position sizing
   
7. TRADE EXECUTION
   ↓ Execute approved trades
   ↓ Log to file and database
   ↓ Send notifications
   
8. POSITION MANAGEMENT
   ↓ Update trailing stops
   ↓ Check take-profit levels
   ↓ Monitor position PnL
   
9. PERFORMANCE TRACKING
   ↓ Calculate portfolio metrics
   ↓ Update live dashboard
   ↓ Record performance data
```

## 🎯 Configuration Parameters

Key settings in `config.py`:

```python
# Trading
SYMBOLS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD']
CAPITAL = 100000

# Position Sizing
MAX_POSITION_SIZE = 0.1  # 10% per trade
ALLOCATION_METHOD = 'momentum'  # equal, risk_parity, momentum

# Indicators
SMA_SHORT = 20
SMA_LONG = 50
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Risk Management
MAX_DRAWDOWN = 0.15  # 15%
DAILY_LOSS_LIMIT = 2000
TRAILING_STOP_PERCENT = 5

# Machine Learning
SEQUENCE_LENGTH = 60
LSTM_EPOCHS = 50
RANDOM_FOREST_TREES = 100

# Execution
RUN_INTERVAL_MINUTES = 5
SCHEDULE_ENABLED = False
```

## 🔧 Module Details

### Core Layer
- **market_scanner**: Real-time market data acquisition
- **data_pipeline**: Data validation and normalization
- **indicators_engine**: Technical analysis calculations
- **strategy_engine**: Trading signal generation
- **portfolio_manager**: Capital allocation strategies
- **risk_engine**: Risk metrics and position management
- **trade_executor**: Order execution and logging

### Quant Layer
- **backtester**: Historical strategy evaluation
- **optimizer**: Parameter optimization via grid search
- **feature_engineering**: Derived feature creation
- **regime_detection**: Market environment classification
- **anomaly_detection**: Outlier and anomaly identification

### AI Layer
- **train_model**: Model training with validation
- **lstm_model**: Deep learning for time-series
- **reinforcement_agent**: Q-Learning for strategy adaptation

### Dashboard Layer
- **dashboard.py**: Web-based portfolio monitoring
- **live_monitor.py**: Real-time metrics tracking

### Utils Layer
- **logger**: Structured logging to files and console
- **database**: SQLite persistence for trades/positions
- **notifier**: Multi-channel alert system

## 📊 Database Schema

```sql
-- Trades
trades(id, timestamp, symbol, signal, entry_price, 
       exit_price, quantity, pnl, pnl_percent, status)

-- Positions
positions(id, symbol, quantity, entry_price, 
          current_price, pnl, stop_loss, take_profit)

-- Performance
performance(id, date, daily_return, cumulative_return,
            drawdown, sharpe_ratio)
```

## 🎓 Key Algorithms

### Signal Generation
```
IF SMA20 > SMA50 AND RSI < 70 AND MACD > Signal THEN BUY
IF SMA20 < SMA50 OR RSI > 30 OR MACD < Signal THEN SELL
```

### Portfolio Allocation
- **Equal weight**: Divide capital equally across positions
- **Risk-parity**: Weight positions by inverse volatility
- **Momentum**: Weight by price momentum

### Risk Metrics
- **Sharpe Ratio**: Returns per unit of risk
- **Sortino Ratio**: Returns per downside risk
- **Maximum Drawdown**: Peak-to-trough decline
- **Value at Risk**: Maximum potential loss

## 📝 Logging

Logs are written to: `logs/quant_hedge_bot.log`

Log levels:
- **INFO**: Normal operations, trades, signals
- **WARNING**: Risk limit breaches, anomalies
- **ERROR**: Execution failures, data issues
- **DEBUG**: Detailed calculations, internal state

## 🚢 Deployment

### Single Machine
```bash
python main.py
```

### Docker (Optional)
```bash
docker build -t quant-hedge-bot .
docker run -v ./data:/app/data quant-hedge-bot
```

### Cloud Deployment
- Configure cloud provider credentials in `config.py`
- Use environment variables for secrets
- Set up persistent storage for data/logs

## 📈 Performance Monitoring

Monitor via:
1. **Console logs**: Real-time execution status
2. **Streamlit dashboard**: Portfolio visualization
3. **Database queries**: Historical analysis
4. **Performance files**: Daily/cumulative metrics

## ⚡ Performance Tips

1. **Reduce scan frequency**: Increase `RUN_INTERVAL_MINUTES`
2. **Optimize indicators**: Cache computed values
3. **Database indexing**: Add indices for frequent queries
4. **Data retention**: Archive old trades monthly
5. **Memory management**: Use chunked data processing

## 🔒 Security

- Store API keys in environment variables (never in code)
- Use SQLite encryption for sensitive data
- Implement IP whitelisting for notifications
- Log all trades for audit compliance
- Use HTTPS for external API calls

## 📚 Advanced Usage

### Custom Indicators
Add to `core/indicators_engine.py`:
```python
@staticmethod
def custom_indicator(data, params):
    # Your calculation here
    return result
```

### Custom Strategy
Modify `core/strategy_engine.py`:
```python
def generate_custom_signal(data):
    # Your logic here
    return 'BUY', 'SELL', or 'HOLD'
```

### Backtesting
```python
from quant.backtester import Backtester
bt = Backtester(data, strategy)
results = bt.run()
```

### Parameter Optimization
```python
from quant.optimizer import StrategyOptimizer
opt = StrategyOptimizer(data)
best_params = opt.optimize()
```

## 🐛 Troubleshooting

### No data fetched
- Check internet connection
- Verify symbols in `config.py`
- Check yfinance API status

### Signals not generated
- Verify indicator data availability
- Check minimum bars requirement (50+)
- Review signal logic in `strategy_engine.py`

### Database errors
- Verify `data/` directory permissions
- Check SQLite availability
- Review database file corruption

### Memory issues
- Reduce historical data window
- Lower `SEQUENCE_LENGTH` for LSTM
- Implement data streaming

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration parameters
3. Run in DEBUG mode for detailed output
4. Verify data availability

## 📝 License

This project is for educational and trading research purposes.

## 🎯 Roadmap

- [ ] Live market data streaming
- [ ] Advanced order types (OCO, Bracket orders)
- [ ] Multi-timeframe analysis
- [ ] Portfolio correlation analysis
- [ ] Volatility surface modeling
- [ ] Machine learning hyperparameter tuning
- [ ] Advanced charting library integration
- [ ] Performance attribution analysis
- [ ] Sentiment analysis integration
- [ ] Advanced notifications with webhooks

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
