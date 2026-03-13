# ⚙️ V9.1 CONFIGURATION REFERENCE

## Environment Variables

### Core Execution
```powershell
# Maximum cycles to run (0 = infinite)
$env:V9_MAX_CYCLES = "5"

# Number of strategies per cycle
$env:V9_POPULATION = "300"

# Sleep seconds between cycles
$env:V9_SLEEP_SECONDS = "2"

# Random seed for reproducibility
$env:V9_SEED = "42"
```

### Market Data
```powershell
# Number of candles to generate
$env:V9_MARKET_CANDLES = "500"

# Lookback period for features (bars)
$env:V9_LOOKBACK_PERIOD = "100"

# Market volatility (synthetic data)
$env:V9_MARKET_VOLATILITY = "0.03"

# Trend strength (0.0 - 1.0)
$env:V9_TREND_STRENGTH = "0.5"
```

### Genetic Algorithm
```powershell
# Generations per cycle
$env:V9_GENERATIONS = "3"

# Mutation rate (0.0 - 1.0)
$env:V9_MUTATION_RATE = "0.15"

# Crossover rate (0.0 - 1.0)
$env:V9_CROSSOVER_RATE = "0.7"

# Elite count (top X strategies survive every generation)
$env:V9_ELITE_COUNT = "10"
```

### Risk Management
```powershell
# Kelly fraction safety factor (0.0 - 1.0)
$env:V9_KELLY_SAFETY = "0.5"

# Target portfolio volatility
$env:V9_TARGET_VOLATILITY = "0.15"

# Maximum single-strategy weight (%)
$env:V9_MAX_POSITION_WEIGHT = "0.30"

# Minimum Sharpe for trading
$env:V9_MIN_SHARPE = "2.0"

# Maximum drawdown threshold
$env:V9_MAX_DRAWDOWN = "0.10"
```

### Whale Radar
```powershell
# Whale transaction threshold (USD)
$env:V9_WHALE_THRESHOLD = "500000"

# Threat level threshold for blocking trades
$env:V9_WHALE_BLOCK_THRESHOLD = "2"

# Number of past transactions to analyze
$env:V9_WHALE_LOOKBACK = "50"
```

### Backtesting
```powershell
# Slippage per trade (%)
$env:V9_SLIPPAGE = "0.001"

# Commission per trade (%)
$env:V9_COMMISSION = "0.001"

# Initial capital
$env:V9_INITIAL_CAPITAL = "100000"

# Monte Carlo simulations
$env:V9_MONTECARLO_SIMULATIONS = "1000"

# Monte Carlo shock max (%)
$env:V9_MONTECARLO_MAX_SHOCK = "95"
```

### Logging & Output
```powershell
# Log level (DEBUG, INFO, WARNING, ERROR)
$env:V9_LOG_LEVEL = "INFO"

# Enable detailed cycle logs
$env:V9_DEBUG_CYCLES = "false"

# Save all strategies to file
$env:V9_SAVE_ALL_STRATEGIES = "false"

# Control Center update frequency (cycles)
$env:V9_DISPLAY_FREQUENCY = "1"
```

---

## Configuration Examples

### 1️⃣ QUICK TEST
```powershell
# Test setup (< 10 seconds)
$env:V9_MAX_CYCLES = "1"
$env:V9_POPULATION = "50"
$env:V9_GENERATIONS = "1"
$env:V9_MONTECARLO_SIMULATIONS = "100"
python main_v91.py
```
**Use**: Validate installation works

---

### 2️⃣ RESEARCH MODE
```powershell
# Data gathering (2-5 minutes)
$env:V9_MAX_CYCLES = "5"
$env:V9_POPULATION = "300"
$env:V9_GENERATIONS = "3"
$env:V9_MONTECARLO_SIMULATIONS = "500"
$env:V9_DEBUG_CYCLES = "true"
python main_v91.py
```
**Use**: Build strategy database

---

### 3️⃣ PRODUCTION SIMULATION
```powershell
# Realistic backtest (15-30 minutes)
$env:V9_MAX_CYCLES = "20"
$env:V9_POPULATION = "500"
$env:V9_GENERATIONS = "5"
$env:V9_SLIPPAGE = "0.002"
$env:V9_COMMISSION = "0.001"
$env:V9_MONTECARLO_SIMULATIONS = "2000"
python main_v91.py
```
**Use**: Pre-production validation

---

### 4️⃣ OVERNIGHT RUN
```powershell
# Extended learning (8+ hours)
$env:V9_MAX_CYCLES = "0"
$env:V9_POPULATION = "1000"
$env:V9_GENERATIONS = "10"
$env:V9_SLEEP_SECONDS = "1"
$env:V9_SAVE_ALL_STRATEGIES = "true"
python main_v91.py
```
**Use**: Comprehensive strategy discovery

---

### 5️⃣ LOW-RISK MODE
```powershell
# Conservative strategy selection
$env:V9_KELLY_SAFETY = "0.25"          # 25% Kelly (safer)
$env:V9_MIN_SHARPE = "3.0"             # Higher bar
$env:V9_MAX_DRAWDOWN = "0.05"          # Tighter drawdown
$env:V9_MAX_POSITION_WEIGHT = "0.15"   # Smaller positions
$env:V9_WHALE_BLOCK_THRESHOLD = "1"    # Block on ANY whale activity
python main_v91.py
```
**Use**: Risk-averse trading

---

### 6️⃣ AGGRESSIVE MODE
```powershell
# Risk-seeking strategy selection
$env:V9_KELLY_SAFETY = "0.75"          # 75% Kelly (aggressive)
$env:V9_MIN_SHARPE = "1.5"             # Lower bar
$env:V9_MAX_DRAWDOWN = "0.20"          # Allow higher DD
$env:V9_MAX_POSITION_WEIGHT = "0.50"   # Larger positions
$env:V9_WHALE_BLOCK_THRESHOLD = "5"    # Allow whale activity
python main_v91.py
```
**Use**: Higher return targeting

---

### 7️⃣ TRENDING MARKET
```powershell
# Boost for momentum strategies
$env:V9_TREND_STRENGTH = "0.8"         # Strong trend
$env:V9_MARKET_VOLATILITY = "0.02"     # Lower volatility
$env:V9_MIN_SHARPE = "1.5"             # Trend filters work with lower Sharpe
python main_v91.py
```
**Use**: When Bitcoin is trending

---

### 8️⃣ CHOPPY MARKET
```powershell
# Boost for mean reversion strategies
$env:V9_TREND_STRENGTH = "0.2"         # Weak trend
$env:V9_MARKET_VOLATILITY = "0.05"     # Higher volatility
$env:V9_TARGET_VOLATILITY = "0.30"     # Accept more vol
python main_v91.py
```
**Use**: When Bitcoin is ranging

---

### 9️⃣ HIGH-FREQUENCY TUNING
```powershell
# Optimize for fast cycles
$env:V9_POPULATION = "200"             # Smaller population
$env:V9_GENERATIONS = "1"              # Single generation
$env:V9_MONTECARLO_SIMULATIONS = "100" # Quick validation
$env:V9_SLEEP_SECONDS = "0"            # No delay
python main_v91.py
```
**Use**: Rapid iteration

---

### 🔟 REPRODUCIBILITY
```powershell
# Same results every run
$env:V9_SEED = "42"
$env:V9_MAX_CYCLES = "5"
$env:V9_POPULATION = "300"
$env:V9_DEBUG_CYCLES = "true"
python main_v91.py
```
**Use**: Testing & validation

---

## Default Configuration

If not specified, V9.1 uses:

```python
class V9_1_Config:
    # Execution
    MAX_CYCLES = int(os.getenv('V9_MAX_CYCLES', 5))
    POPULATION = int(os.getenv('V9_POPULATION', 300))
    SLEEP_SECONDS = int(os.getenv('V9_SLEEP_SECONDS', 2))
    SEED = int(os.getenv('V9_SEED', 42))
    
    # Market Data
    MARKET_CANDLES = int(os.getenv('V9_MARKET_CANDLES', 500))
    LOOKBACK_PERIOD = int(os.getenv('V9_LOOKBACK_PERIOD', 100))
    MARKET_VOLATILITY = float(os.getenv('V9_MARKET_VOLATILITY', 0.03))
    TREND_STRENGTH = float(os.getenv('V9_TREND_STRENGTH', 0.5))
    
    # Genetic Algorithm
    GENERATIONS = int(os.getenv('V9_GENERATIONS', 3))
    MUTATION_RATE = float(os.getenv('V9_MUTATION_RATE', 0.15))
    CROSSOVER_RATE = float(os.getenv('V9_CROSSOVER_RATE', 0.7))
    ELITE_COUNT = int(os.getenv('V9_ELITE_COUNT', 10))
    
    # Risk Management
    KELLY_SAFETY = float(os.getenv('V9_KELLY_SAFETY', 0.5))
    TARGET_VOLATILITY = float(os.getenv('V9_TARGET_VOLATILITY', 0.15))
    MAX_POSITION_WEIGHT = float(os.getenv('V9_MAX_POSITION_WEIGHT', 0.30))
    MIN_SHARPE = float(os.getenv('V9_MIN_SHARPE', 2.0))
    MAX_DRAWDOWN = float(os.getenv('V9_MAX_DRAWDOWN', 0.10))
    
    # Whale Radar
    WHALE_THRESHOLD = float(os.getenv('V9_WHALE_THRESHOLD', 500000))
    WHALE_BLOCK_THRESHOLD = int(os.getenv('V9_WHALE_BLOCK_THRESHOLD', 2))
    WHALE_LOOKBACK = int(os.getenv('V9_WHALE_LOOKBACK', 50))
    
    # Backtesting
    SLIPPAGE = float(os.getenv('V9_SLIPPAGE', 0.001))
    COMMISSION = float(os.getenv('V9_COMMISSION', 0.001))
    INITIAL_CAPITAL = float(os.getenv('V9_INITIAL_CAPITAL', 100000))
    MONTECARLO_SIMULATIONS = int(os.getenv('V9_MONTECARLO_SIMULATIONS', 1000))
    MONTECARLO_MAX_SHOCK = float(os.getenv('V9_MONTECARLO_MAX_SHOCK', 95))
```

---

## Parameter Tuning Guide

### Sharpe Ratio Improvements
```powershell
# Too many unprofitable strategies?
$env:V9_MIN_SHARPE = "2.5"    # Raise bar

# Taking too long to find good strategies?
$env:V9_POPULATION = "500"    # More diversity
$env:V9_GENERATIONS = "5"     # More evolution
```

### Risk Management
```powershell
# Losing too much on bad weeks?
$env:V9_MAX_DRAWDOWN = "0.05"      # Tighter DD limit
$env:V9_KELLY_SAFETY = "0.25"      # Smaller positions

# Returns too small?
$env:V9_KELLY_SAFETY = "0.75"      # Larger positions
$env:V9_MAX_DRAWDOWN = "0.15"      # Accept more DD
```

### Convergence Speed
```powershell
# Finding good strategies slowly?
$env:V9_POPULATION = "1000"        # More strategies to pick from
$env:V9_MUTATIONS = "20"           # More attempts per generation

# Running too slowly?
$env:V9_MONTECARLO_SIMULATIONS = "100"  # Quick validation
$env:V9_GENERATIONS = "1"          # Single pass
```

### Market Responsiveness
```powershell
# Not adapting to market changes?
$env:V9_MAX_CYCLES = "0"           # Continuous learning
$env:V9_SLEEP_SECONDS = "0"        # No delays

# Too many false trades?
$env:V9_WHALE_BLOCK_THRESHOLD = "1"    # Block on whale activity
$env:V9_MIN_SHARPE = "3.0"             # Higher signal quality
```

---

## Performance Impact

| Parameter | Higher Value | Impact |
|-----------|--------------|--------|
| POPULATION | 1000 → 100 | ⚡ 10x faster, ❌ worse strategies |
| GENERATIONS | 10 → 1 | ⚡ 10x faster, ❌ less evolved |
| MONTECARLO | 2000 → 100 | ⚡ 20x faster, ⚠️ less reliable |
| KELLY_SAFETY | 0.25 → 1.0 | 📈 50% more returns (more risk) |
| MIN_SHARPE | 1.5 → 3.0 | ✅ safer (fewer trades) |

---

## Quick Optimization Checklist

```
Choose your priority:

□ SPEED (want results fast)
  - POPULATION = 100
  - GENERATIONS = 1
  - MONTECARLO = 100

□ QUALITY (want best strategies)
  - POPULATION = 500
  - GENERATIONS = 5
  - MONTECARLO = 2000

□ SAFETY (want to limit losses)
  - MAX_DRAWDOWN = 0.05
  - MIN_SHARPE = 3.0
  - KELLY_SAFETY = 0.25

□ RETURNS (want bigger profits)
  - KELLY_SAFETY = 0.75
  - MAX_POSITION_WEIGHT = 0.50
  - MIN_SHARPE = 1.5
```

---

## Environment Variables Cheat Sheet

```powershell
# One-liner QA run
$env:V9_MAX_CYCLES="1"; $env:V9_POPULATION="50"; python main_v91.py

# One-liner research run
$env:V9_MAX_CYCLES="10"; $env:V9_POPULATION="300"; python main_v91.py

# One-liner aggressive run
$env:V9_KELLY_SAFETY="0.75"; $env:V9_MIN_SHARPE="1.5"; python main_v91.py

# One-liner conservative run
$env:V9_KELLY_SAFETY="0.25"; $env:V9_MIN_SHARPE="3.0"; python main_v91.py
```

---

**Need Help?** Read `README_V91.md` or `QUICK_START_V91.md`
