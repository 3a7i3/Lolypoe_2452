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

### CCXT / Multi-Exchange (options A-G)
```powershell
# Symboles tradés séparés par virgule
$env:V9_CCXT_SYMBOLS = "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT"

# Timeframe des bougies (1m, 5m, 15m, 1h, 4h, 1d)
$env:V9_CCXT_TIMEFRAME = "1h"

# Nombre de bougies historiques à charger
$env:V9_CCXT_HISTORY_LIMIT = "200"

# TTL du cache en mémoire (secondes ; 0 = désactivé)
$env:V9_CCXT_CACHE_TTL = "60"

# Ordre de priorité des exchanges (fallback automatique)
$env:V9_CCXT_EXCHANGES = "binance,kraken,okx"

# Chemin SQLite pour cache persistant des bougies (vide = désactivé)
$env:V9_CCXT_CACHE_DB = ""

# Active le live ticker feed REST polling (option G)
$env:V9_CCXT_WS_ENABLED = "false"

# Intervalle de rafraîchissement du ticker (secondes)
$env:V9_CCXT_WS_INTERVAL = "5"

# Utilise ccxt.pro WebSocket au lieu du polling REST (option L)
$env:V9_CCXT_WS_PRO = "false"
```

### Alertes Telegram (option H)
```powershell
# Token du bot Telegram (obtenu via @BotFather)
$env:V9_TELEGRAM_BOT_TOKEN = ""

# ID du canal ou chat cible
$env:V9_TELEGRAM_CHAT_ID = ""

# Délai minimum entre 2 alertes du même type (secondes)
$env:V9_TELEGRAM_COOLDOWN = "60"
```

### Kelly Criterion (option K)
```powershell
# Fraction maximale du capital par trade (0.01 - 1.0)
$env:V9_KELLY_MAX_FRACTION = "0.25"

# Active le demi-Kelly pour réduire la variance
$env:V9_KELLY_HALF = "true"
```

### CVaR — Conditional Value at Risk (option M)
```powershell
# Niveau de confiance pour le calcul du tail risk (0.5 - 0.999)
$env:V9_CVAR_CONFIDENCE = "0.95"

# Perte maximum tolérée dans le tail (fraction du capital)
$env:V9_CVAR_MAX_LOSS = "0.05"
```

### Strategy Scoreboard SQL (option N)
```powershell
# Chemin de la base de données SQLite du scoreboard
$env:V9_SCOREBOARD_SQL_PATH = "databases/strategy_scoreboard.db"
```

### Paper Trading Live (option O)
```powershell
# Capital initial en USD
$env:V9_INITIAL_BALANCE = "100000"
```

### Circuit Breaker (option P)
```powershell
# Perte journalière max en fraction du capital avant blocage
$env:V9_CB_DAILY_LOSS = "0.05"

# Drawdown global max avant blocage
$env:V9_CB_DRAWDOWN_LIMIT = "0.15"

# Nombre de pertes consécutives avant blocage
$env:V9_CB_CONSECUTIVE = "3"
```

### Symbol Router Multi-Symbole (option Q)
```powershell
# Nombre de symboles tradés en parallèle
$env:V9_SYMBOL_ROUTER_MAX = "3"

# Pondération du capital : "volume" ou "equal"
$env:V9_SYMBOL_ROUTER_WEIGHTING = "volume"

# Volume minimum USD pour qu'un symbole soit éligible
$env:V9_SYMBOL_ROUTER_MIN_VOLUME = "0"
```

### Sentiment Feed — Fear & Greed (option R)
```powershell
# Active le feed Fear & Greed Index
$env:V9_SENTIMENT_ENABLED = "true"

# TTL du cache en secondes
$env:V9_SENTIMENT_CACHE_TTL = "300"

# Score utilisé si l'API est inaccessible (0-100)
$env:V9_SENTIMENT_FALLBACK = "50"

# Score en dessous duquel la taille de position est réduite
$env:V9_SENTIMENT_BEARISH_THRESHOLD = "30"
```

### Stop Loss / Take Profit (option S)
```powershell
# Stop loss fixe en fraction de l'entrée (ex: 0.05 = -5%)
$env:V9_SL_PCT = "0.05"

# Take profit fixe en fraction de l'entrée (ex: 0.10 = +10%)
$env:V9_TP_PCT = "0.10"

# Active le SL/TP basé sur ATR au lieu du % fixe
$env:V9_SL_ATR_ENABLED = "false"

# Distance SL = ATR × multiplicateur
$env:V9_SL_ATR_MULT = "2.0"

# Distance TP = ATR × multiplicateur
$env:V9_SL_TP_MULT = "4.0"
```

### Trailing Stop (option T)
```powershell
# Active le trailing stop
$env:V9_SL_TRAILING_ENABLED = "false"

# % trailing en dessous du pic (ex: 0.03 = -3% du plus haut)
$env:V9_SL_TRAILING_PCT = "0.03"
```

### Walk-Forward Optimization (option U)
```powershell
# Active la validation walk-forward
$env:V9_WFO_ENABLED = "false"

# Nombre de splits train/test
$env:V9_WFO_N_SPLITS = "5"

# Fraction d'entraînement par split (0.1 - 0.95)
$env:V9_WFO_TRAIN_RATIO = "0.7"
```

### Position Sizer adaptatif Kelly + CVaR (option V)
```powershell
# Fraction Kelly maximale (0.01 - 1.0)
$env:V9_SIZER_MAX_KELLY = "0.25"

# Active le demi-Kelly conservateur
$env:V9_SIZER_HALF_KELLY = "true"

# Multiplicateur de sécurité CVaR (1.0 = neutre)
$env:V9_SIZER_CVAR_SAFETY = "1.0"

# Taille de position minimale (fraction du capital)
$env:V9_SIZER_MIN_SIZE = "0.01"

# Taille de position maximale (fraction du capital)
$env:V9_SIZER_MAX_SIZE = "0.25"
```

### Regime Strategy Selector (option W)
```powershell
# Active le filtre de stratégies par régime de marché détecté
$env:V9_REGIME_SELECTOR_ENABLED = "true"

# Score de compatibilité minimum pour qu'une stratégie soit retenue (0.0 - 1.0)
$env:V9_REGIME_SELECTOR_MIN_SCORE = "0.25"
```

### Portfolio Rebalancer (option X)
```powershell
# Active le rééquilibrage automatique
$env:V9_REBALANCER_ENABLED = "false"

# Drift minimum en % pour déclencher un rééquilibrage
$env:V9_REBALANCER_DRIFT = "0.05"

# Nombre maximum d'ordres de rééquilibrage par cycle
$env:V9_REBALANCER_MAX_ORDERS = "3"

# Nombre de cycles entre chaque rééquilibrage
$env:V9_REBALANCER_FREQ = "10"
```

### HTML Reporter (option Y)
```powershell
# Active la génération de rapports HTML dark-mode
$env:V9_REPORT_ENABLED = "false"

# Cycles entre chaque rapport
$env:V9_REPORT_FREQUENCY = "50"

# Répertoire de sortie des rapports
$env:V9_REPORT_OUTPUT_DIR = "reports/"

# Nombre de rapports à conserver (les plus anciens sont supprimés)
$env:V9_REPORT_KEEP_LAST = "10"
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

## Profils Avancés (options H→Z)

### 🛡️ MODE PROTECTION MAXIMALE (SL/TP + Circuit Breaker)
```powershell
$env:V9_SL_PCT = "0.03"                  # SL à -3%
$env:V9_TP_PCT = "0.06"                  # TP à +6%
$env:V9_SL_TRAILING_ENABLED = "true"     # Trailing stop
$env:V9_SL_TRAILING_PCT = "0.02"         # Trail à 2%
$env:V9_CB_DAILY_LOSS = "0.03"           # Stop si -3% sur la journée
$env:V9_CB_CONSECUTIVE = "2"             # Stop après 2 pertes consécutives
$env:V9_MAX_CYCLES = "0"
python main_v91.py
```

### 📊 MODE DONNÉES RÉELLES BINANCE + RAPPORT HTML
```powershell
$env:V9_CCXT_SYMBOLS = "BTCUSDT,ETHUSDT"
$env:V9_CCXT_TIMEFRAME = "1h"
$env:V9_CCXT_HISTORY_LIMIT = "500"
$env:V9_REPORT_ENABLED = "true"
$env:V9_REPORT_FREQUENCY = "10"
$env:V9_REPORT_OUTPUT_DIR = "reports/"
$env:V9_MAX_CYCLES = "20"
python main_v91.py
```

### 🔬 MODE WALK-FORWARD (validation robustesse)
```powershell
$env:V9_WFO_ENABLED = "true"
$env:V9_WFO_N_SPLITS = "5"
$env:V9_WFO_TRAIN_RATIO = "0.7"
$env:V9_MIN_SHARPE = "2.5"               # Bar plus élevée après WFO
$env:V9_REGIME_SELECTOR_ENABLED = "true" # Filtre par régime
$env:V9_REGIME_SELECTOR_MIN_SCORE = "0.4"
$env:V9_MAX_CYCLES = "10"
python main_v91.py
```

### 🌐 MODE MULTI-SYMBOLES + RÉÉQUILIBRAGE
```powershell
$env:V9_CCXT_SYMBOLS = "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT"
$env:V9_SYMBOL_ROUTER_MAX = "4"
$env:V9_SYMBOL_ROUTER_WEIGHTING = "volume"
$env:V9_REBALANCER_ENABLED = "true"
$env:V9_REBALANCER_DRIFT = "0.05"
$env:V9_REBALANCER_FREQ = "5"
$env:V9_MAX_CYCLES = "0"
python main_v91.py
```

### 📱 MODE ALERTES TELEGRAM
```powershell
$env:V9_TELEGRAM_BOT_TOKEN = "VOTRE_TOKEN"
$env:V9_TELEGRAM_CHAT_ID = "VOTRE_CHAT_ID"
$env:V9_TELEGRAM_COOLDOWN = "120"         # 1 alerte toutes les 2 min max
$env:V9_SENTIMENT_ENABLED = "true"
$env:V9_MAX_CYCLES = "0"
python main_v91.py
```

### ⚡ MODE TOUT ACTIVÉ (démonstration complète)
```powershell
$env:V9_MAX_CYCLES = "5"
$env:V9_CCXT_SYMBOLS = "BTCUSDT,ETHUSDT"
$env:V9_SL_PCT = "0.04"; $env:V9_TP_PCT = "0.08"
$env:V9_SL_TRAILING_ENABLED = "true"
$env:V9_WFO_ENABLED = "true"
$env:V9_REGIME_SELECTOR_ENABLED = "true"
$env:V9_REBALANCER_ENABLED = "true"
$env:V9_REPORT_ENABLED = "true"
$env:V9_SENTIMENT_ENABLED = "true"
python main_v91.py
```

---

## Tableau Complet des Variables V9_*

| Variable | Défaut | Option | Description |
|----------|--------|--------|-------------|
| `V9_MAX_CYCLES` | `3` | Core | Cycles max (0 = infini) |
| `V9_POPULATION` | `300` | Core | Stratégies par cycle |
| `V9_SLEEP_SECONDS` | `2` | Core | Pause entre cycles |
| `V9_SEED` | `42` | Core | Seed reproductibilité |
| `V9_GENERATIONS` | `3` | Core | Générations GA |
| `V9_MIN_SHARPE` | `2.0` | Core | Sharpe min pour trader |
| `V9_MAX_DRAWDOWN` | `0.25` | Core | Drawdown max |
| `V9_KELLY_SAFETY` | `0.5` | Core | Fraction Kelly (legacy) |
| `V9_CCXT_SYMBOLS` | `BTCUSDT,...` | A | Symboles CCXT |
| `V9_CCXT_TIMEFRAME` | `1h` | A | Timeframe |
| `V9_CCXT_HISTORY_LIMIT` | `200` | A | Bougies à charger |
| `V9_CCXT_CACHE_TTL` | `60` | A | Cache TTL (s) |
| `V9_CCXT_EXCHANGES` | `binance,...` | D | Exchanges priorité |
| `V9_CCXT_CACHE_DB` | `` | E | Cache SQLite persistant |
| `V9_CCXT_WS_ENABLED` | `false` | G | Live ticker polling |
| `V9_CCXT_WS_INTERVAL` | `5` | G | Intervalle ticker (s) |
| `V9_CCXT_WS_PRO` | `false` | L | ccxt.pro WebSocket |
| `V9_TELEGRAM_BOT_TOKEN` | `` | H | Token bot Telegram |
| `V9_TELEGRAM_CHAT_ID` | `` | H | Chat ID Telegram |
| `V9_TELEGRAM_COOLDOWN` | `60` | H | Cooldown alertes (s) |
| `V9_KELLY_MAX_FRACTION` | `0.25` | K | Kelly fraction max |
| `V9_KELLY_HALF` | `true` | K | Demi-Kelly |
| `V9_CVAR_CONFIDENCE` | `0.95` | M | Niveau confiance CVaR |
| `V9_CVAR_MAX_LOSS` | `0.05` | M | Perte tail max |
| `V9_SCOREBOARD_SQL_PATH` | `databases/...` | N | Scoreboard SQLite |
| `V9_INITIAL_BALANCE` | `100000` | O | Capital initial USD |
| `V9_CB_DAILY_LOSS` | `0.05` | P | Perte jour max |
| `V9_CB_DRAWDOWN_LIMIT` | `0.15` | P | Drawdown max global |
| `V9_CB_CONSECUTIVE` | `3` | P | Pertes consécutives max |
| `V9_SYMBOL_ROUTER_MAX` | `3` | Q | Symboles en parallèle |
| `V9_SYMBOL_ROUTER_WEIGHTING` | `volume` | Q | Pondération capital |
| `V9_SYMBOL_ROUTER_MIN_VOLUME` | `0` | Q | Volume min USD |
| `V9_SENTIMENT_ENABLED` | `true` | R | Fear & Greed Index |
| `V9_SENTIMENT_CACHE_TTL` | `300` | R | Cache sentiment (s) |
| `V9_SENTIMENT_FALLBACK` | `50` | R | Score fallback |
| `V9_SENTIMENT_BEARISH_THRESHOLD` | `30` | R | Seuil baissier |
| `V9_SL_PCT` | `0.05` | S | Stop loss fixe % |
| `V9_TP_PCT` | `0.10` | S | Take profit fixe % |
| `V9_SL_ATR_ENABLED` | `false` | S | SL/TP basé ATR |
| `V9_SL_ATR_MULT` | `2.0` | S | Multiplicateur ATR SL |
| `V9_SL_TP_MULT` | `4.0` | S | Multiplicateur ATR TP |
| `V9_SL_TRAILING_ENABLED` | `false` | T | Trailing stop |
| `V9_SL_TRAILING_PCT` | `0.03` | T | % trailing stop |
| `V9_WFO_ENABLED` | `false` | U | Walk-Forward |
| `V9_WFO_N_SPLITS` | `5` | U | Splits train/test |
| `V9_WFO_TRAIN_RATIO` | `0.7` | U | Ratio entraînement |
| `V9_SIZER_MAX_KELLY` | `0.25` | V | Kelly max (sizer) |
| `V9_SIZER_HALF_KELLY` | `true` | V | Demi-Kelly (sizer) |
| `V9_SIZER_CVAR_SAFETY` | `1.0` | V | Safety CVaR |
| `V9_SIZER_MIN_SIZE` | `0.01` | V | Taille position min |
| `V9_SIZER_MAX_SIZE` | `0.25` | V | Taille position max |
| `V9_REGIME_SELECTOR_ENABLED` | `true` | W | Filtre par régime |
| `V9_REGIME_SELECTOR_MIN_SCORE` | `0.25` | W | Score compatibilité min |
| `V9_REBALANCER_ENABLED` | `false` | X | Rééquilibrage auto |
| `V9_REBALANCER_DRIFT` | `0.05` | X | Drift seuil |
| `V9_REBALANCER_MAX_ORDERS` | `3` | X | Ordres max/cycle |
| `V9_REBALANCER_FREQ` | `10` | X | Cycles entre rebalance |
| `V9_REPORT_ENABLED` | `false` | Y | Rapports HTML |
| `V9_REPORT_FREQUENCY` | `50` | Y | Cycles entre rapports |
| `V9_REPORT_OUTPUT_DIR` | `reports/` | Y | Répertoire sorties |
| `V9_REPORT_KEEP_LAST` | `10` | Y | Rapports à conserver |

---

**Need Help?** Read `README_V91.md` or `QUICK_START_V91.md`
