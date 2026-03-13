# Phase 4: Deployment & Production Guide

## Overview

Phase 4 complete infrastructure for deploying the Crypto AI Trading System to production. This includes:

- ✅ **Professional Dashboard** (Dash/Plotly) - Real-time monitoring interface
- ✅ **Docker Containerization** - Multi-container orchestration
- ✅ **Nginx Reverse Proxy** - Load balancing and SSL termination
- ✅ **PostgreSQL Database** - Persistent data storage
- ✅ **Redis Cache** - Session and data caching
- ✅ **PgAdmin** - Database administration UI
- ✅ **Production Environment Config** - Secure deployment settings

## Quick Start

### 1. Prerequisites

```bash
# Required software
- Docker 20.10+
- Docker Compose 1.29+
- Git
- curl

# Recommended
- PostgreSQL client tools
- Redis CLI
- SSL certificates (for HTTPS)
```

### 2. Environment Setup

```bash
# Clone repository (if using git)
git clone <repository-url>
cd quant-trading-system

# Copy and configure environment
cp .env.production .env
# Edit .env and set:
# - DB_PASSWORD (secure password)
# - SECRET_KEY (generate via: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - API keys for exchanges
# - Email/Telegram settings

nano .env  # or your preferred editor
```

### 3. Deploy System

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Verify services are healthy
docker-compose ps

# Check logs
docker-compose logs -f api
docker-compose logs -f dashboard
```

### 4. Access Services

```
API Server:        http://localhost:8000
  - Health:        http://localhost:8000/health
  - API Docs:      http://localhost:8000/docs
  - Redoc:         http://localhost:8000/redoc

Dashboard:         http://localhost:8050
PgAdmin:           http://localhost:5050
  - Email:         admin@example.com
  - Password:      admin (change in .env)

Database:          localhost:5432
Redis:             localhost:6379
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                          │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Nginx Proxy                             │
│  (Load Balance, SSL, Rate Limit, Security Headers)      │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
    ┌──────▼──────┐         ┌────────▼────────┐
    │ FastAPI     │         │ Dash Dashboard  │
    │ REST API    │         │                 │
    │ (8000)      │         │ (8050)          │
    └──────┬──────┘         └────────┬────────┘
           │                         │
    ┌──────▼─────────────────────────▼────────┐
    │              CryptoAISystem              │
    │     (9 ML/Strategy/Quant Modules)       │
    └──────┬──────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────┐
    │  PostgreSQL  Redis   Market APIs         │
    │  (Persistence, Cache, Exchange Data)    │
    └───────────────────────────────────────────┘
```

## Component Details

### API Server (FastAPI)

**Configuration:**
- Workers: 4 (production)
- Host: 0.0.0.0
- Port: 8000
- Reload: disabled
- Log Level: INFO

**Endpoints:**
```
GET  /health              - Health check
GET  /status              - System status

GET  /signals/{symbol}    - Recent signals
POST /signals/generate    - Generate new signals

GET  /trades/open         - Open trades
POST /trades/close        - Close trade
GET  /trades/{symbol}     - Symbol trades

GET  /portfolio           - Portfolio state
POST /portfolio/optimize  - Run optimization
POST /portfolio/rebalance - Execute rebalance

GET  /metrics/daily       - Daily metrics
GET  /metrics/current     - Current metrics
GET  /metrics/strategy    - Strategy performance

POST /backtest            - Start backtest
GET  /backtest/{id}       - Backtest results

GET  /anomalies           - Recent anomalies
```

### Dashboard (Dash/Plotly)

**Features:**
- Real-time equity curve with P&L overlay
- Strategy performance leaderboard
- Open trades table (live updates)
- Recent signals monitor with confidence
- Market regime display (HMM state)
- Anomaly detection alerts feed
- Key metrics cards (Sharpe, Drawdown, Win Rate)
- System health status indicator

**Update Frequency:**
- WebSocket: Real-time price/signal/trade updates
- HTTP Polling: 5-second interval for metrics
- Auto-refresh: Page automatically reconnects on disconnect

### Database (PostgreSQL)

**Tables:**
1. **signals** - Trading signals with confidence, regime, components
2. **trades** - Executed trades with P&L, fees, slippage
3. **portfolio_snapshots** - Hourly/daily portfolio state
4. **daily_metrics** - Aggregated performance metrics
5. **strategy_performance** - Per-strategy statistics
6. **anomaly_events** - Detected market anomalies
7. **regime_changes** - Market regime switches
8. **backtests** - Backtest results and parameters

**Indexes:**
- signals: (symbol, timestamp), action
- trades: (symbol, status), (entry_time, exit_time)
- Others: timestamp, strategy_id where appropriate

### Cache (Redis)

**Usage:**
- Session management
- Real-time price data (1-minute TTL)
- Feature engineering cache
- Model predictions cache
- Rate limiting counters

**Configuration:**
- Max Memory: 512MB
- Eviction Policy: allkeys-lru
- Persistence: AOF enabled

## Deployment Steps

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deploy directory
mkdir -p /opt/crypto-ai && cd /opt/crypto-ai
```

### Step 2: Copy Application

```bash
# Copy project files
cp -r $(pwd)/* /opt/crypto-ai/

# Set permissions
sudo chown -R $USER:$USER /opt/crypto-ai
chmod -R 755 /opt/crypto-ai
```

### Step 3: Configure Environment

```bash
# Create .env from template
cd /opt/crypto-ai
cp .env.production .env

# Generate secure keys
python3 << EOF
import secrets
print("SECRET_KEY=" + secrets.token_urlsafe(32))
import hashlib
password = secrets.token_urlsafe(16)
print("DB_PASSWORD=" + password)
EOF

# Edit configuration
sudo nano .env
# Set database password, API keys, etc.
```

### Step 4: Deploy

```bash
# Build images
cd /opt/crypto-ai
docker-compose build

# Pull images
docker-compose pull postgres redis nginx

# Start services
docker-compose up -d

# Wait for services to be healthy
sleep 30
docker-compose ps

# Check logs
docker-compose logs -f
```

### Step 5: Verify Installation

```bash
# API health check
curl http://localhost:8000/health

# Dashboard access
curl http://localhost:8050

# Database connection
docker-compose exec postgres psql -U crypto_trader -d crypto_trading -c "SELECT version();"

# Redis connection
docker-compose exec redis redis-cli ping
```

## Configuration Management

### Environment Variables

Edit `.env` file for deployment settings:

```bash
# Database
DB_PASSWORD=secure_password_here
DATABASE_URL=postgresql://crypto_trader:password@postgres:5432/crypto_trading

# API
API_WORKERS=4
API_LOG_LEVEL=info

# Trading
TRADING_MODE=paper  # paper | live
AUTO_TRADING=false

# Monitoring
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_RECIPIENTS=admin@example.com
```

### Persistent Data

Volumes for data persistence:
```
postgres_data/     - Database files
redis_data/        - Cache data
api_logs/          - API logs
dashboard_logs/    - Dashboard logs
api_cache/         - Model cache
```

## Scaling & Performance

### Horizontal Scaling

```bash
# Scale API workers
docker-compose up -d --scale api=3

# Use docker-compose.prod.yml for production scaling
docker-compose -f docker-compose.prod.yml up -d
```

### Performance Tuning

```yaml
# docker-compose.yml adjustments
api:
  environment:
    API_WORKERS: 8        # Increase for high traffic
    UVICORN_LOOP: uvloop  # Faster event loop
    DB_POOL_SIZE: 30      # Connection pooling

redis:
  command: redis-server --maxmemory 2gb  # Increase cache size

postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-c max_connections=400"
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database
docker-compose exec postgres psql -U crypto_trader -d crypto_trading -c "SELECT COUNT(*) FROM signals;"

# Redis
docker-compose exec redis redis-cli INFO

# Docker stats
docker stats
```

### Logs

```bash
# View logs
docker-compose logs -f api          # API logs
docker-compose logs -f dashboard    # Dashboard logs
docker-compose logs -f postgres     # Database logs

# Save logs to file
docker-compose logs api > api.log
```

### Metrics

Access dashboard at `http://localhost:8050` for:
- Real-time P&L
- Strategy performance
- Trade history
- Risk metrics

## Backup & Recovery

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U crypto_trader crypto_trading > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U crypto_trader crypto_trading < backup.sql

# Automated daily backup (systemd service)
sudo nano /etc/systemd/system/crypto-backup.service
```

### Redis Backup

```bash
# Redis persistence is enabled (AOF)
# Data automatically saved in /data/appendonly.aof

# Manual backup
docker-compose exec redis redis-cli BGSAVE
```

## Security Considerations

### Pre-Deployment Checklist

- [ ] Change all default passwords
- [ ] Generate new SECRET_KEY
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure CORS origins
- [ ] Store API keys in secrets manager
- [ ] Set up log aggregation
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery

### Security Best Practices

```bash
# 1. Use environment variables for secrets
# Never commit passwords or API keys

# 2. Enable SSL/TLS
# Generate certificates: certbot certonly --standalone -d yourdomain.com

# 3. Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 4. Set up fail2ban for rate limiting
sudo apt install fail2ban

# 5. Regular updates
docker-compose pull
docker-compose build --no-cache
```

## Troubleshooting

### Common Issues

**1. Services won't start**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose logs

# Remove orphaned containers
docker-compose down -v
docker-compose up -d
```

**2. Database connection error**
```bash
# Wait for database to be ready
docker-compose restart api

# Check database logs
docker-compose logs postgres

# Manually test connection
docker-compose exec postgres psql -U crypto_trader -d crypto_trading
```

**3. Out of memory**
```bash
# Check resource usage
docker stats

# Reduce Redis max memory in .env
# Reduce API workers
# Increase server RAM
```

**4. High CPU usage**
```bash
# Check which container uses CPU
docker stats

# Adjust API workers: API_WORKERS=2 (reduce)
# Enable uvloop in production
```

## Maintenance

### Regular Tasks

```bash
# Weekly
- docker-compose logs --tail=1000 > logs.txt
- Check disk space: df -h
- Verify backups exist

# Monthly
- docker-compose pull
- docker image prune -a --force
- docker volume prune
- Database VACUUM: docker-compose exec postgres vacuumdb -U crypto_trader crypto_trading

# Quarterly
- Full system test
- Disaster recovery drill
- Security patches
```

### Upgrade Procedure

```bash
# 1. Backup database and data
docker-compose exec postgres pg_dump -U crypto_trader crypto_trading > backup_$(date +%Y%m%d).sql

# 2. Stop running containers
docker-compose down

# 3. Pull latest code
git pull origin main

# 4. Update Docker images
docker-compose pull

# 5. Rebuild if needed
docker-compose build --no-cache

# 6. Start services
docker-compose up -d

# 7. Verify
curl http://localhost:8000/health
```

## Production Checklist

Before going live:

- [ ] All services healthy and responsive
- [ ] Database backups tested
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] Logging aggregated
- [ ] Failover tested
- [ ] Incident response plan documented
- [ ] Performance tested under load
- [ ] Security audit completed

## Support & Monitoring

### Services Status

```bash
# Get detailed service status
docker-compose ps

# View resource usage
docker stats

# Export Prometheus metrics
curl http://localhost:8000/metrics
```

### Contact & Documentation

- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8050
- Database Admin: http://localhost:5050
- System Logs: docker-compose logs

---

**Phase 4 Complete!** 🚀

The Crypto AI Trading System is now fully deployed with:
- Production-grade database persistence
- REST API with 25+ endpoints
- Real-time WebSocket streaming
- Professional dashboard
- Docker containerization
- Nginx reverse proxy
- Comprehensive monitoring

Ready for paper trading and live deployment!
