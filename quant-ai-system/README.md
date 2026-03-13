# Crypto AI Trading System V6 - Complete Documentation

## 🎯 Overview

**Crypto AI Trading System V6** is an autonomous, AI-driven quantitative trading platform for cryptocurrency markets. It combines machine learning, reinforcement learning, genetic algorithms, and advanced risk management to generate, evaluate, and execute trading strategies automatically.

### Key Features

✅ **Autonomous Strategy Generation** - AI generates unlimited trading strategies  
✅ **Real-time Strategy Evaluation** - Backtests and scores strategies instantly  
✅ **Reinforcement Learning** - DQN agent continuously improves performance  
✅ **Genetic Algorithm Optimization** - Evolves best strategies over time  
✅ **Advanced Risk Management** - Drawdown control, position sizing, stop-loss  
✅ **Portfolio Optimization** - Kelly Criterion allocation & rebalancing  
✅ **Multi-Asset Support** - 1,500+ cryptocurrencies across 4 exchanges  
✅ **Real-time Dashboard** - Streamlit web interface for monitoring  
✅ **Walk-Forward Testing** - Validates strategy performance  
✅ **Monte Carlo Simulation** - Stress tests strategies  

---

## 📁 Project Structure

```
quant-ai-system/
├── main.py                    # Main orchestrator (entry point)
├── main_v2.py                # Enhanced orchestrator with full integration
├── config.py                 # System configuration
│
├── core/                      # Core trading components
│   ├── market_scanner.py      # Market opportunity scanner
│   ├── portfolio_manager.py   # Portfolio & position management
│   ├── risk_engine.py         # Risk management system
│   └── execution_engine.py    # Order execution & trade management
│
├── ai/                        # Artificial Intelligence modules
│   ├── strategy_generator.py  # AI strategy generation
│   ├── strategy_evaluator.py  # Strategy backtesting & scoring
│   ├── strategy_selector.py   # Strategy selection with GA
│   ├── price_predictor.py     # LSTM price prediction
│   └── reinforcement_agent.py # DQN trading agent
│
├── quant/                     # Quantitative analysis
│   ├── optimizer.py           # GA & portfolio optimization
│   ├── backtester.py          # Advanced backtesting engine
│
├── dashboard/
│   ├── streamlit_dashboard.py # Real-time monitoring dashboard
│   └── panel_overview.py      # Panel-based overview (V5)
│
└── utils/
    ├── logger.py              # Logging utilities
    └── data_handler.py        # Data management
```

---

## 🚀 Getting Started

### Installation

```bash
# Clone repository
git clone <repo-url>
cd quant-ai-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `config.py` to customize:

```python
# Portfolio settings
PORTFOLIO_CONFIG = {
    'initial_capital': 100000,      # Starting capital
    'max_positions': 20,             # Max open positions
    'max_position_size': 0.10,       # Max 10% per position
    'max_drawdown': 0.25,            # Max 25% drawdown
}

# Strategy generation
STRATEGY_CONFIG = {
    'population_size': 50,           # Generate 50 strategies
    'top_k_strategies': 5,           # Evaluate top 5
}

# Risk management
RISK_CONFIG = {
    'max_daily_loss': 0.05,          # Max 5% daily loss
    'stop_loss_percent': 0.10,       # 10% stop loss
}
```

### Run the System

**Option 1: Main Orchestrator**
```bash
python main_v2.py
```

**Option 2: Streamlit Dashboard**
```bash
streamlit run dashboard/streamlit_dashboard.py
```

**Option 3: Run with Specific Config**
```bash
# Paper trading mode
LIVE_TRADING=False python main_v2.py

# Debug mode
DEBUG_MODE=True python main_v2.py
```

---

## 🔧 Core Components

### 1. Strategy Generator (`ai/strategy_generator.py`)

Generates unlimited trading strategies using:
- **10 Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic, ADX, CCI, VWAP
- **10 Rules**: Cross-overs, breakouts, overbought/oversold, divergences, etc.
- **Parameterized Combinations**: Each strategy has unique parameters

```python
from ai.strategy_generator import StrategyGenerator

gen = StrategyGenerator()
strategy = gen.generate_strategy()  # Single strategy
strategies = gen.generate_population(50)  # 50 strategies
```

**Output**:
```python
{
    'id': 'STRAT_00001',
    'indicators': ['RSI', 'MACD', 'EMA'],
    'rules': ['cross_above', 'divergence'],
    'parameters': {'RSI_period': 14, 'MACD_fast': 12},
    'entry_logic': 'IF RSI crosses above MACD AND EMA > threshold THEN BUY',
    'exit_logic': 'IF RSI crosses below MACD OR EMA < threshold THEN SELL',
    'timeframe': '1h',
    'risk_reward_ratio': 2.5
}
```

### 2. Strategy Evaluator (`ai/strategy_evaluator.py`)

Backtests and scores strategies using:
- **Sharpe Ratio** - Risk-adjusted returns
- **Sortino Ratio** - Downside risk only
- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Gains / Losses ratio
- **Max Drawdown** - Worst peak-to-trough
- **Total Return** - Overall profitability

```python
from ai.strategy_evaluator import StrategyEvaluator

evaluator = StrategyEvaluator()
result = evaluator.evaluate_strategy(strategy, market_data)
results = evaluator.evaluate_population(strategies, market_data)
```

**Composite Score Formula**:
```
Score = (Total Return × 20) 
       + (Sharpe Ratio × 5)
       + (Win Rate × 10)
       + ((1 - Max Drawdown) × 15)
       + (Min(Profit Factor, 5) × 5)
```

### 3. Portfolio Manager (`core/portfolio_manager.py`)

Manages positions and allocation:
- **Kelly Criterion** - Optimal position sizing
- **Risk Parity** - Equal risk allocation
- **Dynamic Rebalancing** - Automatic portfolio adjustment
- **Position Tracking** - PnL, return %, status

```python
from core.portfolio_manager import PortfolioManager

pm = PortfolioManager(initial_capital=100000)
pm.open_position('BTC/USDT', 1.5, 45000)
pm.update_position_prices({'BTC/USDT': 45500})
metrics = pm.get_metrics()
```

### 4. Risk Engine (`core/risk_engine.py`)

Comprehensive risk management:
- **Max Drawdown Enforcement** - Stops trading if exceeded
- **Daily Loss Limits** - Halts on max daily loss
- **Position Stop-Loss** - Automatic position closure
- **Value at Risk (VaR)** - 95% VaR calculation
- **Volatility Monitoring** - Real-time portfolio volatility

```python
from core.risk_engine import RiskEngine

risk = RiskEngine(max_drawdown=0.25, max_daily_loss=0.05)
risk_ok = risk.check_drawdown_limit(equity_curve)
stops = risk.calculate_position_stops(positions)
metrics = risk.get_risk_metrics(portfolio_value, equity_curve, returns)
```

### 5. Reinforcement Learning Agent (`ai/reinforcement_agent.py`)

Deep Q-Network (DQN) for continuous improvement:
- **Action Space**: BUY, SELL, HOLD
- **State Space**: Market features (price, volume, momentum)
- **Reward**: Risk-adjusted returns (Sharpe ratio)
- **Training**: Experience replay with epsilon-greedy exploration

```python
from ai.reinforcement_agent import RLTradingAgent

agent = RLTradingAgent(state_size=10)
agent.train_episode(states, rewards, batch_size=32)
action = agent.choose_action(state, training=True)
stats = agent.get_training_stats()
```

### 6. Market Scanner (`core/market_scanner.py`)

Identifies trading opportunities:
- **Opportunity Scoring** - 0-100 score based on technicals
- **Signal Detection** - Breakouts, volume spikes, momentum
- **Volume Filtering** - Min volume requirement
- **Multi-Symbol Scanning** - Scan entire market

```python
from core.market_scanner import MarketScanner

scanner = MarketScanner(min_volume_usd=100000)
opportunities = scanner.scan_market(market_data, limit=20)
filtered = scanner.get_filtered_opportunities(min_score=50, trend_filter='UP')
```

### 7. Execution Engine (`core/execution_engine.py`)

Order management and execution:
- **Market Orders** - Immediate execution
- **Limit Orders** - Conditional execution
- **Stop Orders** - Stop-loss orders
- **Commission & Slippage** - Realistic cost modeling

```python
from core.execution_engine import ExecutionEngine, OrderSide, OrderType

engine = ExecutionEngine(commission_rate=0.001)
order = engine.create_order('BTC/USDT', OrderSide.BUY, 1.5, OrderType.MARKET)
engine.submit_order(order)
stats = engine.get_execution_stats()
```

### 8. Backtester (`quant/backtester.py`)

Advanced backtesting with:
- **Walk-Forward Testing** - In-sample vs out-of-sample
- **Monte Carlo Simulation** - Stress testing with 100+ simulations
- **Drawdown Analysis** - Peak-to-trough analysis
- **Performance Metrics** - Sharpe, Sortino, profit factor

```python
from quant.backtester import Backtester

bt = Backtester(initial_capital=100000)
result = bt.backtest_strategy(prices, signals)
wf_result = bt.walk_forward_test(prices, signals)
mc_results = bt.monte_carlo_test(prices, num_simulations=100)
```

---

## 🧬 Genetic Algorithm Strategy Evolution

The system continuously evolves strategies:

1. **Generation** → Create population of random strategies
2. **Evaluation** → Backtest each strategy, calculate fitness score
3. **Selection** → Tournament selection of best performers
4. **Crossover** → Combine best strategies (genetic crossover)
5. **Mutation** → Random parameter adjustments
6. **Repeat** → Evolve for N generations

```python
from ai.strategy_selector import StrategySelector

selector = StrategySelector(population_size=50, top_k=5)
best = selector.evolve_strategies(market_data, generations=10)
```

---

## 📊 System Workflow

```
┌─────────────────────────────────────────────────────────┐
│                   SYSTEM CYCLE (5 min)                  │
└────────────┬────────────────────────────────────────────┘
             │
   ┌─────────▼─────────┐
   │ 1. Market Scan    │  Identify trading opportunities
   └────────┬──────────┘
            │
   ┌────────▼──────────────┐
   │ 2. Generate Strats    │  Create 50 candidate strategies
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │ 3. Evaluate Strats    │  Backtest and score each
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │ 4. Select Best 5      │  Choose top performers
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │ 5. Optimize Portfolio │  Kelly sizing, rebalance
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │ 6. Risk Check         │  Verify limits, adjust
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │ 7. Update Positions   │  Execute orders, update PnL
   └────────┬──────────────┘
            │
            └──────────────> [Wait 5 min] ──┐
                                           │
                                    [Repeat] ─┘
```

---

## 📈 Performance Metrics

### Strategy Metrics
- **Win Rate**: % of profitable trades (target: >50%)
- **Sharpe Ratio**: Risk-adjusted returns (target: >1.0)
- **Sortino Ratio**: Downside risk ratio (target: >1.5)
- **Profit Factor**: Gains/Losses (target: >1.5)
- **Max Drawdown**: Worst drawdown (limit: -25%)

### Portfolio Metrics
- **Total Return**: Cumulative return % 
- **Annual Return**: Annualized return
- **Volatility**: Annual standard deviation
- **Sharpe Ratio**: Overall risk-adjusted return
- **Information Ratio**: Alpha generation
- **Sortino Ratio**: Downside risk adjusted

---

## 🛑 Risk Management

### Position-Level
- **Kelly Criterion**: Optimal sizing based on win rate
- **Max Position Size**: 10% of portfolio per trade
- **Stop Loss**: 10% automatic exit
- **Take Profit**: 30% auto-close

### Portfolio-Level
- **Max Drawdown**: 25% trigger halt
- **Max Daily Loss**: 5% daily limit
- **Concentration Limit**: Single position max
- **Sector Limits**: Diversification requirements

### System-Level
- **Circuit Breaker**: Auto-halt on extreme drawdown
- **Connectivity Check**: Verify exchange connectivity
- **Data Validation**: Monitor data quality
- **Heartbeat**: System health monitoring

---

## 🔄 Multi-Asset Support

**Supported Exchanges:**
- Binance (1,500+ pairs)
- Bybit (500+ pairs)
- Coinbase (200+ pairs)
- Kraken (200+ pairs)

**Tradeable Assets:**
```
Top 20 by market cap:
BTC, ETH, BNB, SOL, ADA, XRP, DOGE, AVAX, LINK, MATIC,
UNI, XLM, LTC, ATOM, ARB, OP, APT, BLUR, FIT, FTT
```

---

## 📊 Dashboard Features

Real-time Streamlit dashboard includes:

1. **Performance Tab**
   - Equity curve with drawdown shading
   - Daily returns distribution
   - Drawdown timeline analysis

2. **Positions Tab**
   - Active trades table
   - Position breakdown pie chart
   - Win/loss statistics

3. **Strategies Tab**
   - Strategy performance comparison
   - Win rates and Sharpe ratios
   - Current allocation

4. **Analytics Tab**
   - Risk-return scatter plot
   - Monthly returns
   - Advanced metrics (Sortino, Information Ratio)

5. **Settings Tab**
   - Real-time parameter tuning
   - Config save/reset
   - Trading mode selection

---

## ⚙️ Configuration Options

### Environment Variables

```bash
# Trading mode
export LIVE_TRADING=False  # or True for live
export PAPER_TRADING=True

# API Keys (if using live trading)
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret

# Logging
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
export DEBUG_MODE=False

# System
export API_HOST=localhost
export API_PORT=8000
```

### Config File

```python
# config.py
PORTFOLIO_CONFIG = {
    'initial_capital': 100000,
    'max_positions': 20,
    'max_position_size': 0.10,
    'max_drawdown': 0.25,
    'rebalance_frequency': 'daily'
}

STRATEGY_CONFIG = {
    'population_size': 50,
    'top_k_strategies': 5,
    'generation_frequency': 'hourly'
}
```

---

## 🚨 Troubleshooting

### Issue: Low Win Rate
**Solution**: 
- Increase strategy diversity (population_size)
- Adjust indicator periods
- Increase genetic algorithm generations
- Add regime detection filters

### Issue: High Drawdown
**Solution**:
- Lower max_position_size
- Implement stronger stop-losses
- Increase max_drawdown_limit trigger
- Add portfolio diversification

### Issue: Slow Strategy Evaluation
**Solution**:
- Use smaller population_size initially
- Run backtester in parallel (GPU)
- Cache historical data
- Reduce evaluation frequency

### Issue: Connection Errors
**Solution**:
- Verify API keys and permissions
- Check exchange connectivity
- Ensure rate limiting compliance
- Add connection retry logic

---

## 📚 Advanced Topics

### Custom Indicators

Add custom indicators by extending `StrategyGenerator`:

```python
def my_indicator(prices):
    # Your indicator logic
    return signal

# Add to strategy_generator.py
self.indicators['my_indicator'] = my_indicator
```

### Custom Optimization

Implement custom objective functions:

```python
def custom_objective(params):
    result = backtest_with_params(params)
    return result.sharpe_ratio * result.win_rate

optimizer.optimize_parameters(custom_objective, param_ranges)
```

### Machine Learning Integration

Add custom ML models:

```python
from quant.backtester import Backtester
import tensorflow as tf

# Train LSTM on historical data
model = tf.keras.Sequential([...])
predictions = model.predict(market_data)
```

---

## 📝 License & Disclaimer

⚠️ **DISCLAIMER**: This system is for educational and research purposes only. 
- Past performance does not guarantee future results
- Use with paper trading first before live trading
- Risk management is essential
- Never risk capital you cannot afford to lose
- Consult financial advisors before live trading

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Multi-timeframe analysis
- Options trading strategies
- Crypto derivatives (futures, perpetuals)
- Machine learning model ensemble
- Real-time data integration via CCXT

---

## 📞 Support

For issues and questions:
- Check this documentation
- Review configuration in `config.py`
- Check logs in `logs/` directory
- Verify dependencies with `pip check`

---

**Version**: V6.0.0  
**Last Updated**: 2024  
**Status**: Production-Ready ✅
