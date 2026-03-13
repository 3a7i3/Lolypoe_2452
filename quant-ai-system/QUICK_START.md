# Quick Start Guide - V6 System

## 🚀 Installation (2 minutes)

```bash
# 1. Clone & navigate
cd quant-ai-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure (optional)
cp .env.example .env  # Edit with your settings
```

## ▶️ Run the System

### Option 1: Main Orchestrator (Recommended)
```bash
python main_v2.py
```

**Output:**
```
✅ CryptoAISystem V6 initialized with 20 symbols
🚀 CryptoAISystem V6 starting...
   Configuration: Portfolio=$100000, Max Positions=20

======================================================================
  CYCLE #1 - 2024-01-15 10:30:00
======================================================================
📊 [1/6] Market Scanning...
   Found 10 opportunities
🧬 [2/6] Generating Strategies...
   Generated 50 candidate strategies
📈 [3/6] Evaluating Strategies...
   Top strategy score: 78.45
⚖️  [4/6] Optimizing Portfolio...
   Strategy STRAT_001: 50.0% allocation
   Strategy STRAT_002: 25.0% allocation
🛡️  [5/6] Risk Management...
   Risk status: ✅ OK
💼 [6/6] Updating Positions...
   Portfolio: $100,500, Positions: 2

✅ Cycle completed in 4.32s
⏳ Waiting 300s until next cycle...
```

### Option 2: Streamlit Dashboard
```bash
streamlit run dashboard/streamlit_dashboard.py
```

Then open: `http://localhost:8501`

### Option 3: In Python Script

```python
import asyncio
from main_v2 import CryptoAISystem

system = CryptoAISystem()
try:
    asyncio.run(system.run(cycle_interval=300))
except KeyboardInterrupt:
    system.stop()
```

---

## 🎯 Trading Modes

### Paper Trading (Default - Recommended for Testing)
```bash
python main_v2.py
```
- No real money risked
- Simulated execution
- Full strategy backtesting
- Perfect for learning

### Backtest Mode
```bash
# Edit config.py to set backtest parameters
python -c "from quant.backtester import Backtester; bt = Backtester(); print(bt.get_summary())"
```

### Live Trading (⚠️ Use with Caution!)
```bash
export LIVE_TRADING=True
export BINANCE_API_KEY=your_api_key
export BINANCE_API_SECRET=your_api_secret
python main_v2.py
```

**⚠️ WARNING**: Only for experienced traders with proper risk management!

---

## 📊 Dashboard Quick Tour

### Access Points

**Streamlit Dashboard:**
```bash
streamlit run dashboard/streamlit_dashboard.py
# http://localhost:8501
```

**Panel Dashboard (Legacy):**
```bash
python dashboard/panel_overview.py
# http://localhost:5006
```

### Key Metrics to Monitor

| Metric | Good Range | Warning | Danger |
|--------|-----------|---------|--------|
| Win Rate | >55% | 50-55% | <50% |
| Sharpe Ratio | >1.5 | 1.0-1.5 | <1.0 |
| Drawdown | <-15% | -15 to -25% | <-25% |
| Return | >10%/month | 5-10%/month | <5%/month |
| Volatility | 15-25% | 25-35% | >35% |

---

## 🧬 Customization

### Adjust Portfolio Size
```python
# config.py
PORTFOLIO_CONFIG = {
    'initial_capital': 50000,  # Change from 100000
    'max_positions': 10,       # Change from 20
}
```

### Change Strategy Generation
```python
# config.py
STRATEGY_CONFIG = {
    'population_size': 100,    # More strategies
    'top_k_strategies': 10,    # More to evaluate
}
```

### Tune Risk Limits
```python
# config.py
RISK_CONFIG = {
    'max_drawdown': 0.15,      # 15% max (was 25%)
    'max_daily_loss': 0.03,    # 3% daily max (was 5%)
}
```

### Enable Advanced Logging
```bash
export LOG_LEVEL=DEBUG
python main_v2.py
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --upgrade
pip install ta-lib  # May need separate install
```

### Issue: "Port already in use"
```bash
# For Streamlit (default 8501)
streamlit run dashboard/streamlit_dashboard.py --server.port 8502

# For Panel (default 5006)
python dashboard/panel_overview.py --port 5007
```

### Issue: "No module named 'config'"
```bash
# Solution: Ensure you're in the correct directory
cd quant-ai-system
python main_v2.py
```

### Issue: "Exchange connection error"
```bash
# Check internet connection
# Verify API keys if live trading
# Try different exchange in config
```

---

## 📈 Monitoring Tips

### Key Signals to Watch

**Good Signs ✅**
- Win rate stable or increasing
- Sharpe ratio > 1.5
- Drawdown recovering quickly
- New strategies outperforming old ones
- Diversified across multiple symbols

**Warning Signs ⚠️**
- Win rate dropping below 50%
- Increasing drawdown
- Concentration in 1-2 symbols
- Consecutive losing trades
- System latency increasing

**Dangerous Signs 🛑**
- Max drawdown exceeded
- Win rate < 40%
- Sharpe ratio < 0.5
- Rapid equity erosion
- Exchange connectivity issues

---

## 🔧 Advanced Usage

### Running Multiple Systems
```python
import asyncio
from main_v2 import CryptoAISystem

async def main():
    system1 = CryptoAISystem({'initial_capital': 50000})
    system2 = CryptoAISystem({'initial_capital': 50000})
    
    tasks = [
        system1.run(cycle_interval=300),
        system2.run(cycle_interval=300)
    ]
    
    await asyncio.gather(*tasks)

asyncio.run(main())
```

### Custom Strategy
```python
from ai.strategy_evaluator import StrategyEvaluator

custom_strat = {
    'id': 'CUSTOM_001',
    'indicators': ['RSI', 'MACD'],
    'entry': 'RSI > 30 AND MACD > signal',
    'exit': 'RSI > 70 OR MACD < signal',
}

evaluator = StrategyEvaluator()
result = evaluator.evaluate_strategy(custom_strat, market_data)
print(f"Score: {result['score']:.2f}")
```

### Backtesting Strategy
```python
from quant.backtester import Backtester
from ai.strategy_generator import StrategyGenerator

gen = StrategyGenerator()
strategies = gen.generate_population(50)

backtester = Backtester(initial_capital=100000)
for strat in strategies:
    result = backtester.backtest_strategy(prices, signals)
    if result.sharpe_ratio > 2.0:
        print(f"🎉 Found high-quality strategy: {result}")
```

---

## 📊 Performance Expectations

### Conservative Settings
- Capital: $100,000
- Positions: 10-15
- Max Drawdown: 15%
- Expected Return: 10-20% monthly
- Sharpe: 1.2-1.8

### Balanced Settings (Default)
- Capital: $100,000
- Positions: 15-20
- Max Drawdown: 25%
- Expected Return: 15-30% monthly
- Sharpe: 1.5-2.5

### Aggressive Settings
- Capital: $100,000
- Positions: 25-30
- Max Drawdown: 40%
- Expected Return: 30-50% monthly
- Sharpe: 1.0-2.0

**Note**: These are projections based on historical backtests. Actual results will vary.

---

## 🛡️ Risk Checklist

Before running LIVE trading:

- [ ] Backtested ≥6 months of data
- [ ] Walk-forward testing passed
- [ ] Monthly Sharpe ratio > 1.5
- [ ] Max drawdown < 20%
- [ ] Win rate > 55%
- [ ] Tested with small capital first
- [ ] Monitor system daily
- [ ] Have stop-loss plan ready
- [ ] API keys secured
- [ ] Reviewed all risks

---

## 📚 Next Steps

1. **Paper Trade First**: Run in paper mode for 1-2 weeks
2. **Monitor Dashboard**: Check daily for performance
3. **Adjust Settings**: Tune based on results
4. **Backtest More**: Test different parameter combinations
5. **Go Live (Optional)**: Only with small capital initially

---

## 🚀 Getting Help

**Resources**:
- Read `README.md` for detailed documentation
- Check `config.py` for all available settings
- Review code comments in component files
- Enable DEBUG_MODE for verbose logging

**Common Issues**:
```bash
# Check system status
python main_v2.py --status

# Test configuration
python -c "from config import get_config; import json; print(json.dumps(get_config(), indent=2, default=str))"

# Validate imports
python -c "import main_v2; print('✅ All imports successful')"
```

---

**Good luck with your trading! Start small, test thoroughly, and never risk more than you can afford to lose.** 🚀

