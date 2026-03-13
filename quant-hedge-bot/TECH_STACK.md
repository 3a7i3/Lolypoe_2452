# Technology Stack - Quant Hedge Bot

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│          STREAMLIT DASHBOARD (Port 8501)            │
├─────────────────────────────────────────────────────┤
│  Dashboard Layer (Visualization & Monitoring)       │
│  ├── Real-time portfolio metrics                    │
│  ├── Trade history and position tracking            │
│  └── Performance charts and analytics               │
├─────────────────────────────────────────────────────┤
│  Application Layer (Business Logic)                 │
│  ├── Market Scanner & Data Pipeline                 │
│  ├── Indicators Engine (Technical Analysis)         │
│  ├── Strategy Engine (Signal Generation)            │
│  ├── Portfolio Manager (Allocation & Tracking)      │
│  ├── Risk Engine (Position & Risk Management)       │
│  └── Trade Executor (Order Management)              │
├─────────────────────────────────────────────────────┤
│  Intelligence Layer (ML & AI)                       │
│  ├── RandomForest Price Prediction                  │
│  ├── LSTM Time-Series Forecasting                   │
│  ├── Q-Learning Reinforcement Agent                 │
│  ├── Feature Engineering Pipeline                   │
│  ├── Regime Detection                               │
│  └── Anomaly Detection                              │
├─────────────────────────────────────────────────────┤
│  Research Layer (Backtesting & Optimization)        │
│  ├── Backtester (Historical Performance)            │
│  ├── Parameter Optimizer (Grid Search)              │
│  └── Strategy Analyzer                              │
├─────────────────────────────────────────────────────┤
│  Data Layer (Persistence & Storage)                 │
│  ├── SQLite Database (Trades, Positions, Metrics)   │
│  ├── File Logger (Execution Logs)                   │
│  └── Configuration Management                       │
├─────────────────────────────────────────────────────┤
│  External Integrations                              │
│  ├── yfinance (Market Data)                         │
│  ├── Telegram/Email/Slack (Notifications)           │
│  └── Binance/CCXT (Exchange Integration)            │
└─────────────────────────────────────────────────────┘
```

## 📦 Core Dependencies

### Data & Computation
- **pandas** (2.1.0): DataFrames, time-series manipulation
- **numpy** (1.24.3): Numerical computing
- **yfinance** (0.2.28): Market data acquisition
- **ta** (0.11.0): Technical analysis indicators

### Machine Learning
- **scikit-learn** (1.5.0): RandomForest, preprocessing
- **tensorflow** (2.13.0): LSTM, deep learning
- **keras**: Integrated with TensorFlow

### Dashboard & Visualization
- **streamlit** (1.28.0): Web interface, real-time dashboards
- **plotly** (5.17.0): Interactive charts

### Exchange Integration
- **python-binance** (1.1.0): Binance API
- **ccxt** (4.0.0): Multi-exchange support

### Notifications & Alerts
- **python-telegram-bot** (20.1): Telegram integration
- **requests** (2.31.0): HTTP client

### Utilities
- **schedule** (1.2.0): Task scheduling
- **python-dotenv** (1.0.0): Environment variables
- **psutil** (5.9.5): System monitoring

## 🗂️ Project Structure Details

### Configuration Management

**config.py** - Single source of truth for all settings
```python
# Trading parameters
SYMBOLS = ['BTC-USD', 'ETH-USD']
CAPITAL = 100000

# Strategy parameters
SMA_SHORT = 20
RSI_PERIOD = 14

# Risk management
MAX_DRAWDOWN = 0.15
TRAILING_STOP_PERCENT = 5

# ML parameters
SEQUENCE_LENGTH = 60
LSTM_EPOCHS = 50
```

### Core Modules (8 modules)

1. **market_scanner.py**
   - yfinance data fetching
   - Multi-symbol support
   - Volume and price filtering
   - Market analysis (gainers/losers)

2. **data_pipeline.py**
   - Data cleaning (NaN handling)
   - Normalization
   - Feature engineering
   - Sequence creation for LSTM

3. **indicators_engine.py**
   - Technical indicators: SMA, EMA, RSI, MACD, ATR, Bollinger, OBV, VWAP, ADX
   - Efficient computation
   - MultiIndex column handling

4. **strategy_engine.py**
   - Multi-indicator signal logic
   - Confidence scoring
   - Regime filtering

5. **ai_predictor.py**
   - RandomForest model
   - Price prediction (N-period ahead)
   - Normalization and scaling

6. **portfolio_manager.py**
   - 3 allocation strategies (equal, risk-parity, momentum)
   - Position tracking
   - Portfolio statistics

7. **risk_engine.py**
   - Drawdown monitoring
   - Daily loss limits
   - Trailing stops
   - Sharpe/Sortino ratios
   - Value at Risk

8. **trade_executor.py**
   - Order execution logging
   - Database persistence
   - Notification triggers

### Research Modules (5 modules)

1. **backtester.py**
   - Historical performance simulation
   - Equity curve tracking
   - Slippage and commission modeling
   - Trade statistics

2. **optimizer.py**
   - Grid search parameter optimization
   - Best parameter selection
   - Performance ranking

3. **feature_engineering.py**
   - 10+ derived features
   - Momentum indicators
   - Volatility measures
   - Volume analysis

4. **regime_detection.py**
   - Market regime classification (BULL/BEAR/SIDEWAYS)
   - Confidence scoring
   - SMA and return-based analysis

5. **anomaly_detection.py**
   - Statistical anomaly detection
   - Volume spike detection
   - Outlier identification

### AI Modules (3 modules)

1. **train_model.py**
   - RandomForest model training
   - Cross-validation
   - Feature importance analysis

2. **lstm_model.py**
   - LSTM architecture definition
   - Time-series forecasting
   - TensorFlow integration

3. **reinforcement_agent.py**
   - Q-Learning algorithm
   - State/action/reward definition
   - Epsilon-greedy exploration

### Dashboard Modules (2 modules)

1. **dashboard.py**
   - Streamlit web interface
   - Portfolio overview
   - Trade history visualization
   - Performance metrics

2. **live_monitor.py**
   - Real-time metrics tracking
   - Console status display
   - Performance updates

### Utility Modules (3 modules)

1. **logger.py**
   - Centralized logging
   - File and console handlers
   - Multiple log levels

2. **database.py**
   - SQLite schema definition
   - CRUD operations
   - Trade and position tracking

3. **notifier.py**
   - Multi-channel notifications
   - Telegram support
   - Email and Slack scaffolding

## 🔄 Data Flow

```
Market Data (yfinance)
        ↓
   Data Pipeline
   ├── Clean data (handle NaN)
   ├── Normalize values
   ├── Add features (momentum, volatility)
   └── Create sequences (for LSTM)
        ↓
   Indicators Engine
   ├── Calculate SMA, EMA, RSI
   ├── Calculate MACD, ATR
   └── Calculate OBV, VWAP, Bollinger
        ↓
   Regime Detection
   └── Classify BULL/BEAR/SIDEWAYS
        ↓
   Strategy Engine
   ├── Generate signal (BUY/SELL)
   ├── Calculate confidence
   └── Apply regime filter
        ↓
   Risk Engine
   ├── Validate drawdown
   ├── Check daily loss limit
   └── Size position
        ↓
   Trade Executor
   ├── Execute trade
   ├── Log to database
   └── Send notification
        ↓
   Portfolio Manager
   ├── Update positions
   ├── Calculate P&L
   └── Update allocations
        ↓
   Dashboard
   └── Display metrics
```

## 🧮 Algorithms & Calculations

### Technical Indicators

**SMA (Simple Moving Average)**
```
SMA = (Price[t] + Price[t-1] + ... + Price[t-n+1]) / n
```

**RSI (Relative Strength Index)**
```
RS = Average Gain / Average Loss
RSI = 100 - (100 / (1 + RS))
```

**MACD (Moving Average Convergence Divergence)**
```
MACD Line = EMA12 - EMA26
Signal Line = EMA9 of MACD
Histogram = MACD - Signal
```

**ATR (Average True Range)**
```
TR = max(High - Low, |High - Close|, |Low - Close|)
ATR = SMA(TR, 14)
```

### Risk Metrics

**Sharpe Ratio**
```
Sharpe = (Return - Risk_Free_Rate) / Std_Dev
```

**Sortino Ratio**
```
Sortino = (Return - Risk_Free_Rate) / Downside_Dev
```

**Maximum Drawdown**
```
Drawdown = (Trough - Peak) / Peak
Max_Drawdown = Maximum Drawdown Value
```

### Allocation Strategies

**Equal Weight**
```
Weight = 1 / N (for each of N positions)
```

**Risk Parity**
```
Weight = Inverse_Volatility / Sum_Inverse_Volatility
```

**Momentum**
```
Weight = Momentum / Sum_Momentum
```

## 🎯 Signal Generation Logic

```
BUY Signal:
  IF SMA20 > SMA50 (Trend Up)
  AND RSI(14) < 70 (Not Overbought)
  AND MACD Histogram > 0 (Momentum Up)
  → BUY with Confidence Score

SELL Signal:
  IF SMA20 < SMA50 (Trend Down)
  OR RSI(14) > 30 (Not Oversold)
  OR MACD Histogram < 0 (Momentum Down)
  → SELL

CONFIDENCE:
  = Average of normalized indicator signals
  = Range [0.0 to 1.0]
```

## 💾 Database Schema

### Trades Table
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    symbol TEXT,
    signal TEXT,
    entry_price REAL,
    exit_price REAL,
    quantity REAL,
    pnl REAL,
    pnl_percent REAL,
    status TEXT
);
```

### Positions Table
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    quantity REAL,
    entry_price REAL,
    current_price REAL,
    pnl REAL,
    stop_loss REAL,
    take_profit REAL
);
```

### Performance Table
```sql
CREATE TABLE performance (
    id INTEGER PRIMARY KEY,
    date TEXT,
    daily_return REAL,
    cumulative_return REAL,
    drawdown REAL,
    sharpe_ratio REAL
);
```

## 🔌 Integration Points

### Market Data
- **yfinance**: Historical and real-time data (default)
- **Binance API**: Crypto exchange data
- **CCXT**: Multi-exchange support

### Execution
- **Paper Trading**: Simulated execution
- **Binance**: Live trading integration (scaffolded)
- **CCXT**: Multi-exchange execution (scaffolded)

### Notifications
- **Telegram**: Real-time alerts
- **Email**: Daily summaries (scaffolded)
- **Slack**: Team notifications (scaffolded)

## 📊 Performance Considerations

### Optimization Techniques
1. **Vectorized Operations**: Use NumPy/Pandas for bulk calculations
2. **Caching**: Store computed indicators
3. **Incremental Updates**: Update data streams, not full recalculation
4. **Parallel Processing**: Multi-threaded data fetching
5. **Database Indexing**: Optimize queries with indices

### Memory Management
- **Chunked Data Processing**: Process data in batches
- **Circular Buffers**: Replace oldest data with new
- **Garbage Collection**: Cleanup unused objects

### Scalability
- **Modular Design**: Independent modules
- **Configuration-Driven**: Easy parameter changes
- **Database Persistence**: Long-term data storage
- **Cloud Ready**: Deployable to AWS/Azure/GCP

## 🚀 Deployment Options

### Local Development
- Windows/Linux/Mac
- Python venv
- SQLite database
- Streamlit dashboard

### Docker Container
- Containerized environment
- Easy deployment
- Consistent dependencies
- Volume mounting for data

### Cloud Deployment
- AWS EC2/Lambda
- Azure App Service
- Google Cloud Run
- DigitalOcean

### Kubernetes
- Horizontal scaling
- Load balancing
- Self-healing
- Resource management

## 🔒 Security Architecture

### API Key Management
- Environment variables
- Encrypted configurations
- Key rotation

### Data Protection
- SQLite encryption
- HTTPS for external calls
- Secure logging (no secrets in logs)

### Access Control
- IP whitelisting
- Authentication tokens
- Audit logging

## 📈 Performance Metrics

### Monitored Metrics
- Portfolio value (real-time)
- Total P&L (absolute and %)
- Position count
- Win rate %
- Sharpe ratio
- Maximum drawdown
- Daily return
- Cumulative return

### Dashboards
- Real-time Streamlit interface
- Daily performance summaries
- Trade history with analysis
- Risk metrics visualization

## 🔧 Extensibility

### Adding Custom Indicators
1. Add method to `IndicatorsEngine`
2. Return pandas Series
3. Reference in `StrategyEngine`

### Custom Strategies
1. Modify `StrategyEngine.generate_signal()`
2. Combine multiple indicators
3. Return BUY/SELL/HOLD

### New Data Sources
1. Create connector in `MarketScanner`
2. Follow yfinance data format
3. Integrate with `DataPipeline`

### Custom Risk Checks
1. Add method to `RiskEngine`
2. Check before execution
3. Log and alert on violation

---

## Summary

Quant Hedge Bot combines enterprise-grade software architecture with hedge fund trading requirements, providing:

- ✅ Production-ready code
- ✅ Comprehensive documentation
- ✅ Multiple deployment options
- ✅ Scalable architecture
- ✅ Real-time monitoring
- ✅ Historical analysis
- ✅ ML/AI integration
- ✅ Risk management

**Version**: 1.0.0  
**Status**: Production Ready
