# QUICK REFERENCE CARD

## One-Minute Deploy Guide

### Quick Start (3 commands)
```bash
# 1. Download/Navigate to project
cd quant-trading-system

# 2. Copy environment file
cp .env.production .env

# 3. Deploy
docker-compose up -d
```

### Access Services
| Service | URL | Purpose |
|---------|-----|---------|
| **API** | http://localhost:8000 | REST endpoints |
| **Docs** | http://localhost:8000/docs | API Swagger docs |
| **Dashboard** | http://localhost:8050 | Real-time monitoring |
| **PgAdmin** | http://localhost:5050 | Database admin |
| **Health** | http://localhost:8000/health | Service status |

---

## Essential Commands

### Deploy & Stop
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f dashboard
```

### Database
```bash
# Access database
docker-compose exec postgres psql -U crypto_trader -d crypto_trading

# Backup
docker-compose exec postgres pg_dump -U crypto_trader crypto_trading > backup.sql

# Restore
docker-compose exec -T postgres psql -U crypto_trader crypto_trading < backup.sql
```

### Production Deploy
```bash
# Use production docker-compose with HA
docker-compose -f docker-compose.prod.yml up -d

# Includes: Primary + Secondary API, PostgreSQL, Redis, Nginx, Prometheus, Grafana
```

---

## System Architecture (One Page)

```
┌─────────────┐
│   Browser   │
├─────────────┤
│   Nginx     │  ← Load balancer, SSL, rate limiting
├─────────────┤
│ API Servers │  ← FastAPI, 25+ endpoints
├─────────────┤
│ Core System │  ← 9 ML/Strategy modules (Phase 3)
├─────────────┤
│ PostgreSQL  │  ← 8 tables, persistent storage
│ Redis       │  ← Cache layer
├─────────────┤
│ Exchanges   │  ← CCXT integration
└─────────────┘
```

### Key Components

| Component | Role | Files |
|-----------|------|-------|
| **Phase 3** | ML/Strategy | core/, ai/, quant/ (14 files, 3,500+ LOC) |
| **Phase 4** | Infrastructure | api/, database/, dashboard/ (8 files, 1,330+ LOC) |
| **API** | REST endpoints | api/rest_api.py (25+ endpoints) |
| **WebSocket** | Real-time | api/websocket_handler.py (5 channels) |
| **Dashboard** | UI | dashboard/dash_app.py (dark Plotly theme) |
| **Database** | Persistence | database/models.py (8 tables) |
| **Docker** | Deployment | Dockerfile, docker-compose.yml, nginx.conf |

---

## Configuration

### .env File (Most Important Settings)

```bash
# Database
DB_PASSWORD=YOUR_PASSWORD              # Change this!
DATABASE_URL=postgresql://...          # Auto-generated

# Trading
TRADING_MODE=paper                     # paper | live
AUTO_TRADING=false                     # Enable/disable

# API
API_WORKERS=4                          # Number of workers
LOG_LEVEL=info                         # Logging level

# Market
NUM_SYMBOLS=500                        # Cryptos to monitor
MARKET_SCAN_INTERVAL=30                # Seconds

# Strategy
STRATEGY_MODE=institutional             # Strategy configuration
CONFIDENCE_THRESHOLD=0.6               # Min confidence
```

See `.env.production` for all options.

---

## API Endpoints (Key 25+)

### System
```
GET  /health              # Health check
GET  /status              # System status
```

### Signals (Trading)
```
GET  /signals/{symbol}                 # Recent signals
POST /signals/generate/{symbol}        # Generate new signals
```

### Trades
```
GET  /trades/open                      # Open trades
GET  /trades/{symbol}                  # Symbol trades
POST /trades/{id}/close                # Close trade
```

### Portfolio
```
GET  /portfolio                        # Current state
POST /portfolio/optimize               # Optimize allocation
POST /portfolio/rebalance              # Execute rebalance
```

### Analytics
```
GET  /metrics/daily                    # Daily metrics
GET  /metrics/current                  # Current metrics
GET  /metrics/strategy/{name}          # Strategy performance
```

### Backtesting
```
POST /backtest                         # Start backtest
GET  /backtest/{id}                    # Results
```

### Intelligence
```
GET  /anomalies                        # Recent anomalies
```

Full docs: http://localhost:8000/docs

---

## WebSocket Channels (Real-time)

```
/ws/prices/{symbol}        ← Price/volume updates
/ws/signals                ← Global signals
/ws/signals/{symbol}       ← Symbol signals
/ws/trades                 ← Trade execution
/ws/portfolio              ← Portfolio changes
/ws/metrics                ← Performance metrics
/ws/anomalies              ← Anomaly detection
/ws/alerts                 ← System alerts
```

---

## Dashboard Features

| Feature | Description |
|---------|-------------|
| **Equity Curve** | Real-time P&L chart |
| **Strategy Leaderboard** | 5 strategies ranked by win rate |
| **Metrics Cards** | Sharpe, Drawdown, Win Rate, etc |
| **Open Trades** | Current positions with P&L |
| **Signals Monitor** | Recent signals with confidence |
| **Regime Display** | Current market regime (HMM) |
| **Anomalies** | Recent market anomalies |
| **System Status** | Health badge and indicators |

Auto-refresh every 5 seconds.

---

## Database Schema (8 Tables)

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `signals` | Trading signals | symbol, action, confidence, regime |
| `trades` | Executed trades | symbol, entry_price, exit_price, pnl |
| `portfolio_snapshots` | State snapshots | positions (JSON), allocation (JSON) |
| `daily_metrics` | Performance metrics | sharpe, sortino, calmar, drawdown |
| `strategy_performance` | Per-strategy stats | strategy_id, win_rate, profit_factor |
| `anomaly_events` | Market anomalies | symbol, anomaly_type, severity |
| `regime_changes` | Regime switches | from_regime, to_regime, confidence |
| `backtests` | Backtest results | parameters (JSON), trades (JSON) |

Normalization: Full 3NF design with proper indexing.

---

## Monitoring Checklist

### Health Checks
```bash
# All services
docker-compose ps

# API endpoint
curl http://localhost:8000/health

# Database
docker-compose exec postgres psql -U crypto_trader -d crypto_trading -c "SELECT 1"

# Redis
docker-compose exec redis redis-cli ping

# Resource usage
docker stats
```

### Logs
```bash
# API logs
docker-compose logs -f api

# Dashboard logs
docker-compose logs -f dashboard

# Database logs
docker-compose logs -f postgres

# All logs
docker-compose logs -f
```

### Metrics
```bash
# View in Prometheus
http://localhost:9090  # (production)

# View in Grafana
http://localhost:3000  # (production)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Services won't start | `docker-compose down -v && docker-compose up -d` |
| DB connection error | Wait 30s for postgres to initialize |
| Out of memory | Reduce API_WORKERS or increase server RAM |
| High CPU | Check `docker stats`, reduce workers |
| API not responding | Check logs: `docker-compose logs api` |
| Dashboard not loading | Verify API running first |

---

## Security Checklist

- [ ] Changed DB_PASSWORD
- [ ] Generated SECRET_KEY
- [ ] Configured CORS_ORIGINS
- [ ] Set up SSL certificates (production)
- [ ] Firebase firewall rules
- [ ] Enabled rate limiting (Nginx)
- [ ] Set log rotation (500M max)
- [ ] Automated backups configured
- [ ] Monitoring alerts enabled
- [ ] Tested failover/recovery

---

## Performance Tuning

### Development (Single Machine)
```yaml
api:
  environment:
    API_WORKERS: 2

redis:
  command: redis-server --maxmemory 256mb

postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-c max_connections=100"
```

### Production (Distributed)
```yaml
# docker-compose.prod.yml
api-primary:
  environment:
    API_WORKERS: 8
api-secondary:
  environment:
    API_WORKERS: 4
redis:
  command: redis-server --maxmemory 1gb
postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-c max_connections=500"
```

---

## Backup & Recovery

### Daily Backup
```bash
# Schedule this daily
docker-compose exec postgres pg_dump -U crypto_trader crypto_trading \
  > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore from Backup
```bash
docker-compose exec -T postgres psql -U crypto_trader crypto_trading < backup.sql
```

### Backup Verification
```bash
# Check backup file size
ls -lh backup_*.sql

# Test restore (dry run)
docker-compose run postgres psql -Udummy < backup.sql
```

---

## Deployment Environments

### Development
```bash
docker-compose up -d
# 7 services, single instances, no redundancy
```

### Production (HA)
```bash
docker-compose -f docker-compose.prod.yml up -d
# 9 services, redundant API servers, monitoring stack
```

### Manual Deploy (No Docker)
```bash
pip install -r requirements.txt
python -c "from api.rest_api import run_api; run_api()"
python -c "from dashboard.dash_app import run_dashboard; run_dashboard()"
```

---

## Support Resources

| Resource | Location |
|----------|----------|
| **API Docs** | http://localhost:8000/docs |
| **System Architecture** | SYSTEM_ARCHITECTURE.md (5,000+ words) |
| **Deployment Guide** | DEPLOYMENT.md (400+ lines) |
| **Configuration** | config.py (200+ parameters) |
| **Project Status** | PROJECT_STATUS.md (complete summary) |
| **Phase 3 Details** | Core system components |
| **Phase 4 Details** | Infrastructure & deployment |

---

## Key Statistics

- **1,500+ cryptos** across 4 exchanges
- **100+ technical indicators** for features
- **5 trading strategies** + ensemble voting
- **4 anomaly detection methods**
- **2 deep learning models** (LSTM + RL)
- **3 portfolio optimizers**
- **25+ REST API endpoints**
- **5 WebSocket channels**
- **8 database tables** (time-series optimized)
- **9 Docker services** (7 dev / 9 prod)

---

## Version Info

| Component | Version |
|-----------|---------|
| **System** | v4.0 (Phase 3 + Phase 4) |
| **Python** | 3.10+ |
| **Docker** | 20.10+ |
| **PostgreSQL** | 15 |
| **Redis** | 7 |
| **FastAPI** | 0.100+ |
| **Dash** | 2.14+ |
| **TensorFlow** | 2.12+ |

---

## Next Steps

```bash
# 1. Deploy
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. Access dashboard
open http://localhost:8050

# 4. Review API docs
open http://localhost:8000/docs

# 5. Check logs
docker-compose logs -f

# 6. Read documentation
cat DEPLOYMENT.md
```

---

**Ready to deploy?** 🚀

```bash
./deploy.sh development false    # Linux/Mac
# or
deploy.bat development false     # Windows
```

System is production-ready! 🟢
