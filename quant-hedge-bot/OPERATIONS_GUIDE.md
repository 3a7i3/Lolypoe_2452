# Professional Hedge Fund System - Deployment & Operations Guide

## 🚀 Production Deployment

### Phase 1: Pre-Deployment Verification

#### 1. System Requirements
```bash
# Minimum hardware
- CPU: 4+ cores
- RAM: 8GB+ (16GB recommended)
- Storage: 100GB SSD
- Network: 100Mbps+ internet connection
- Uptime: 99.9%+ ISP guarantee

# Operating Systems
- Linux (Ubuntu 20.04+) - Recommended
- macOS (10.15+)
- Windows Server 2019+
```

#### 2. Dependencies Check
```bash
# Verify Python environment
python --version  # 3.8+
pip --version
conda --version   # if using conda

# Test imports
python -c "import pandas, numpy, tensorflow, ccxt, streamlit; print('✓ All dependencies OK')"
```

#### 3. Data Connectivity
```bash
# Test exchange connectivity
python -c "import ccxt; print(ccxt.exchanges)"

# Test yfinance connectivity
python -c "import yfinance; print(yfinance.download('BTC-USD', period='1d'))"

# Test database
python -c "from utils.database import db; db.initialize_database(); print('✓ Database OK')"
```

### Phase 2: Configuration & Setup

#### 1. Copy Production Configuration
```bash
cp config.py config_prod.py
```

#### 2. Set Production Parameters
```python
# config.py
PROFESSIONAL_MODE = True
PROFESSIONAL_24_7_MODE = True
PRODUCTION_MODE = True
PRODUCTION_CAPITAL = 100000  # Your hedge fund capital

# Risk parameters
MAX_DRAWDOWN_PERCENT = 0.15
DAILY_LOSS_LIMIT = 0.03
KELLY_FRACTION = 0.5

# Exchange configuration
EXCHANGES_TO_MONITOR = ['binance', 'kraken', 'coinbase']
NUM_CRYPTO_TO_MONITOR = 500

# Strategies
ENABLED_STRATEGIES = [
    'trend_following',
    'mean_reversion',
    'breakout',
    'volatility_trading',
    'market_making'
]

# Advanced tools
MONTE_CARLO_ENABLED = True
WALK_FORWARD_ENABLED = True
KELLY_CRITERION_ENABLED = True

# Logging
LOG_LEVEL = 'INFO'
SAVE_INTERMEDIATE_DATA = True
```

#### 3. Set Environment Variables
```bash
# .env file
TELEGRAM_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id
DEBUG_MODE=false
PROFESSIONAL_CAPITAL=100000
```

### Phase 3: Single Node Deployment (Linux/Ubuntu)

#### 1. Setup System User
```bash
# Create dedicated trading user
sudo useradd -m -s /bin/bash trading
sudo -i -u trading

# Clone repository
cd /home/trading
git clone https://github.com/your-repo/quant-hedge-bot.git
cd quant-hedge-bot
```

#### 2. Create Python Environment
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Create Systemd Service
```bash
# Create service file
sudo tee /etc/systemd/system/hedge-fund-bot.service << EOF
[Unit]
Description=Professional Hedge Fund Trading Bot
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/quant-hedge-bot
Environment="PATH=/home/trading/quant-hedge-bot/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/trading/quant-hedge-bot/venv/bin/python professional_main.py
Restart=always
RestartSec=30

# Resource limits
MemoryLimit=8G
CPUQuota=400%

# Logging
StandardOutput=append:/home/trading/quant-hedge-bot/logs/bot.log
StandardError=append:/home/trading/quant-hedge-bot/logs/bot.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hedge-fund-bot.service
sudo systemctl start hedge-fund-bot.service

# Check status
sudo systemctl status hedge-fund-bot.service
```

#### 4. Dashboard Setup
```bash
# Create dashboard service
sudo tee /etc/systemd/system/hedge-fund-dashboard.service << EOF
[Unit]
Description=Professional Hedge Fund Dashboard
After=network.target
Wants=hedge-fund-bot.service

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/quant-hedge-bot
Environment="PATH=/home/trading/quant-hedge-bot/venv/bin"
ExecStart=/home/trading/quant-hedge-bot/venv/bin/streamlit run professional_dashboard.py --server.port=8501

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable hedge-fund-dashboard.service
sudo systemctl start hedge-fund-dashboard.service
```

#### 5. Nginx Reverse Proxy
```bash
# Install nginx
sudo apt-get install -y nginx

# Create proxy configuration
sudo tee /etc/nginx/sites-available/hedge-fund << EOF
upstream streamlit {
    server localhost:8501;
}

server {
    listen 80;
    server_name trading.yourcompany.com;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/hedge-fund /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Phase 4: Monitoring & Operations

#### 1. System Health Monitoring
```bash
# Create monitoring script (monitor.sh)
#!/bin/bash

while true; do
    echo "=== Hedge Fund Bot Status ==="
    systemctl status hedge-fund-bot.service
    
    echo "=== Resource Usage ==="
    ps aux | grep python | grep professional_main
    
    echo "=== Database Check ==="
    sqlite3 data/trades/quant_hedge.db "SELECT COUNT(*) FROM trades;"
    
    echo "=== Log Tail ==="
    tail -n 5 logs/quant_hedge_bot.log
    
    sleep 300  # Every 5 minutes
done
```

#### 2. Log Rotation
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/hedge-fund << EOF
/home/trading/quant-hedge-bot/logs/quant_hedge_bot.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 trading trading
    sharedscripts
    postrotate
        systemctl reload hedge-fund-bot.service > /dev/null 2>&1 || true
    endscript
}
EOF
```

#### 3. Daily Performance Report
```python
# daily_report.py
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from utils.logger import logger

def generate_daily_report():
    """Generate daily performance report."""
    
    conn = sqlite3.connect('data/trades/quant_hedge.db')
    
    # Get today's trades
    today = datetime.now().date()
    query = f"SELECT * FROM trades WHERE datetime(timestamp) >= '{today}'"
    trades_today = pd.read_sql_query(query, conn)
    
    # Calculate metrics
    total_pnl = trades_today['pnl'].sum()
    num_trades = len(trades_today)
    win_rate = (trades_today['pnl'] > 0).sum() / num_trades if num_trades > 0 else 0
    
    report = f"""
    DAILY PERFORMANCE REPORT - {today}
    ==================================
    Total Trades: {num_trades}
    Total P&L: ${total_pnl:.2f}
    Win Rate: {win_rate:.1%}
    Best Trade: ${trades_today['pnl'].max():.2f}
    Worst Trade: ${trades_today['pnl'].min():.2f}
    """
    
    logger.info(report)
    conn.close()
    
    return report

if __name__ == "__main__":
    generate_daily_report()
```

### Phase 5: Database Backup Strategy

#### 1. Automated Daily Backups
```bash
# backup.sh
#!/bin/bash

BACKUP_DIR="/backups/hedge-fund"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/home/trading/quant-hedge-bot/data/trades/quant_hedge.db"

# Create backup
sqlite3 $DB_FILE ".backup $BACKUP_DIR/quant_hedge_$DATE.db"

# Compress
gzip $BACKUP_DIR/quant_hedge_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload to cloud (optional)
# aws s3 cp $BACKUP_DIR/quant_hedge_$DATE.db.gz s3://your-bucket/backups/
```

#### 2. Cron Job
```bash
# Add to crontab
crontab -e

# Run backup daily at 2 AM
0 2 * * * /home/trading/quant-hedge-bot/backup.sh
```

### Phase 6: Production Monitoring Stack

#### 1. Prometheus Integration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hedge-fund-bot'
    static_configs:
      - targets: ['localhost:8000']  # Metrics endpoint
```

#### 2. Grafana Dashboard
- Portfolio Value Over Time
- Daily P&L Distribution
- Strategy Performance Comparison
- Risk Metrics (VaR, Sharpe Ratio)
- System Resource Usage

### Phase 7: Alerting System

#### 1. Critical Alerts
```python
# Alert conditions
ALERTS = {
    'daily_loss_limit_hit': 'Daily loss limit exceeded',
    'max_drawdown_reached': 'Maximum drawdown reached',
    'connection_error': 'Exchange connection lost',
    'database_error': 'Database connection failed',
    'high_slippage': 'Execution slippage too high',
    'insufficient_liquidity': 'Insufficient market liquidity',
    'strategy_error': 'Strategy calculation error',
    'system_cpu_high': 'CPU usage > 80%',
    'system_memory_high': 'Memory usage > 80%',
    'disk_space_low': 'Disk space < 10GB'
}
```

#### 2. Telegram Alerts
```python
# Send Telegram alerts
async def send_alert(alert_type, message):
    if TELEGRAM_ENABLED:
        await send_telegram_notification(
            f"⚠️ {alert_type}: {message}"
        )
        logger.warning(f"Alert: {alert_type}")
```

### Phase 8: Disaster Recovery

#### 1. RTO/RPO Targets
- **RTO (Recovery Time Objective)**: 15 minutes
- **RPO (Recovery Point Objective)**: 5 minutes

#### 2. Failover Procedure
```bash
# 1. Detect failure
systemctl status hedge-fund-bot.service

# 2. Check logs
tail -f logs/quant_hedge_bot.log

# 3. Restore from backup if needed
sqlite3 restored.db ".restore $(ls -t backups/*.gz | head -1 | z gunzip -c)"

# 4. Restart service
systemctl restart hedge-fund-bot.service
```

### Phase 9: Testing Before Production

#### 1. Paper Trading Mode
```python
# config.py
PAPER_TRADING = True  # Simulated execution, no real money
DRY_RUN = True        # No actual orders
```

#### 2. Backtesting
```bash
python -c "
from quant.backtester import Backtester
from quant.walk_forward_tester import WalkForwardTester

# Run backtest
bt = Backtester()
results = bt.run()

# Run walk-forward
wf = WalkForwardTester()
wf_results = wf.run()
"
```

#### 3. Stress Testing
```bash
# Test with extreme scenarios
python -c "
from advanced.monte_carlo import MonteCarloSimulator

mc = MonteCarloSimulator()
stress_results = mc.stress_test(shock_magnitude=0.5)  # 50% shock
"
```

### Phase 10: Performance Tuning

#### 1. Optimize Data Pipeline
```python
# Increase batch size for performance
BATCH_PROCESS_SIZE = 500  # Larger batches

# Enable parallel processing
USE_PARALLEL_PROCESSING = True
NUM_WORKERS = 8  # Match CPU cores
```

#### 2. Database Optimization
```sql
-- Add indices for faster queries
CREATE INDEX idx_trades_date ON trades(timestamp);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_performance_date ON performance(date);

-- Analyze query performance
VACUUM;
ANALYZE;
```

## 🔄 Operational Procedures

### Daily Checklist
- [ ] Verify bot is running (systemctl status)
- [ ] Check logs for errors
- [ ] Verify database integrity
- [ ] Monitor dashboard metrics
- [ ] Check system resources (CPU, memory, disk)
- [ ] Review trades executed
- [ ] Confirm backups completed
- [ ] Check alert systems

### Weekly Tasks
- [ ] Review strategy performance
- [ ] Analyze P&L attribution
- [ ] Check parameter drift
- [ ] Review risk metrics
- [ ] Validate backtest results
- [ ] Test failover procedures
- [ ] Update documentation

### Monthly Tasks
- [ ] Full system audit
- [ ] Parameter reoptimization
- [ ] Strategy performance review
- [ ] Compliance reporting
- [ ] Database maintenance
- [ ] Security audit
- [ ] Capacity planning

## 📊 KPIs to Monitor

- **Daily P&L**: Target $500+
- **Sharpe Ratio**: Target 1.8+
- **Win Rate**: Target 60%+
- **Max Drawdown**: Monitor < 20%
- **System Uptime**: Target 99.9%
- **Execution Latency**: Monitor < 100ms
- **Strategy Consistency**: Monitor parameter stability

---

**Version**: 2.0 Production Edition  
**Last Updated**: March 2026  
**Status**: Ready for Deployment
