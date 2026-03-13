# Deployment Guide - Quant Hedge Bot

## 🚀 Deployment Options

### Option 1: Local Development (Windows/Linux/Mac)

#### Prerequisites
- Python 3.8+
- pip package manager
- 2GB+ RAM
- Internet connection (for market data)

#### Installation Steps

1. **Clone or download the project**
```bash
cd quant-hedge-bot
```

2. **Run setup script** (Windows)
```bash
setup.bat
```

Or manual setup:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure the bot**
```bash
# Edit config.py with your settings
notepad config.py
```

4. **Run the bot**
```bash
python main.py
```

5. **Monitor the bot**
```bash
streamlit run dashboard/dashboard.py
```

---

### Option 2: Docker Deployment

#### Prerequisites
- Docker installed
- Docker Hub account (for image storage)

#### Dockerfile

Create `Dockerfile` in project root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directories
RUN mkdir -p data/market_cache data/historical data/trades logs

# Expose port for dashboard
EXPOSE 8501

# Set environment
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501')"

# Run the bot
CMD ["python", "main.py"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  quant-hedge-bot:
    build: .
    container_name: quant-hedge-bot
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config.py:/app/config.py
    environment:
      - PYTHONUNBUFFERED=1
      - SCHEDULE_ENABLED=true
      - RUN_INTERVAL_MINUTES=5
    restart: unless-stopped
    ports:
      - "8501:8501"
    networks:
      - trading-net

  dashboard:
    build: .
    container_name: quant-dashboard
    command: streamlit run dashboard/dashboard.py --server.port=8502
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    ports:
      - "8502:8502"
    networks:
      - trading-net

networks:
  trading-net:
    driver: bridge
```

#### Build and Run

```bash
# Build Docker image
docker build -t quant-hedge-bot:latest .

# Run container
docker run -d \
  --name quant-bot \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -p 8501:8501 \
  quant-hedge-bot:latest

# Or use docker-compose
docker-compose up -d

# View logs
docker logs -f quant-bot

# Stop container
docker stop quant-bot
docker rm quant-bot
```

---

### Option 3: AWS Deployment

#### EC2 Instance Setup

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.medium (2GB RAM minimum)
   - Storage: 20GB gp2
   - Security group: Allow SSH (22), HTTP (80), HTTPS (443)

2. **Connect to Instance**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

3. **Install Dependencies**
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3.11 python3-pip python3-venv

# Install build tools
sudo apt-get install -y build-essential

# Clone repository
git clone https://github.com/your-repo/quant-hedge-bot.git
cd quant-hedge-bot
```

4. **Setup Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials (if using Binance/S3)
aws configure

# Setup environment variables
cat > .env << EOF
DEBUG_MODE=false
SCHEDULE_ENABLED=true
RUN_INTERVAL_MINUTES=5
TELEGRAM_TOKEN=your-token
EOF
```

5. **Create Systemd Service**
```bash
# Create service file
sudo tee /etc/systemd/system/quant-hedge-bot.service << EOF
[Unit]
Description=Quant Hedge Bot Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/quant-hedge-bot
Environment="PATH=/home/ubuntu/quant-hedge-bot/venv/bin"
ExecStart=/home/ubuntu/quant-hedge-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable quant-hedge-bot.service
sudo systemctl start quant-hedge-bot.service

# Check status
sudo systemctl status quant-hedge-bot.service

# View logs
sudo journalctl -u quant-hedge-bot.service -f
```

6. **Setup Nginx Reverse Proxy** (for Streamlit Dashboard)
```bash
sudo apt-get install -y nginx

# Create nginx config
sudo tee /etc/nginx/sites-available/quant-bot << EOF
upstream streamlit {
    server localhost:8501;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/quant-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

7. **SSL Certificate** (Let's Encrypt)
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option 4: Azure App Service

#### Setup on Azure

1. **Create App Service Plan**
```bash
az appservice plan create \
  --name quant-hedge-plan \
  --resource-group myResourceGroup \
  --sku B1 \
  --is-linux
```

2. **Create Web App**
```bash
az webapp create \
  --resource-group myResourceGroup \
  --plan quant-hedge-plan \
  --name quant-hedge-bot \
  --runtime "python:3.11"
```

3. **Deploy Code**
```bash
# Connect to repository
az webapp deployment source config-zip \
  --resource-group myResourceGroup \
  --name quant-hedge-bot \
  --src project.zip

# Or use Git
git remote add azure https://your-repo.git
git push azure main
```

---

### Option 5: DigitalOcean Deployment

#### 1-Click Deployment

1. **Create Droplet**
   - Select: Ubuntu 22.04 LTS
   - Size: 2GB RAM
   - Region: Your choice
   - Add SSH key

2. **Connect and Setup**
```bash
ssh root@your-droplet-ip

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3.11 python3-pip python3-venv git

# Clone and setup
git clone https://github.com/your-repo/quant-hedge-bot.git
cd quant-hedge-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create supervisor config
apt-get install -y supervisor

# Setup bot and dashboard with supervisor
```

---

## 🔧 Production Configuration

### Environment Variables

Create `.env` file:
```bash
# Debug
DEBUG_MODE=false

# Scheduling
SCHEDULE_ENABLED=true
RUN_INTERVAL_MINUTES=5

# Notifications
TELEGRAM_TOKEN=your-token
TELEGRAM_CHAT_ID=your-chat-id
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Database
DB_PATH=/app/data/trading.db

# Logging
LOG_LEVEL=INFO
LOG_PATH=/app/logs

# API Keys (if using exchanges)
BINANCE_API_KEY=your-key
BINANCE_SECRET_KEY=your-secret
```

### Load Configuration

Modify `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
SCHEDULE_ENABLED = os.getenv('SCHEDULE_ENABLED', 'false').lower() == 'true'
RUN_INTERVAL_MINUTES = int(os.getenv('RUN_INTERVAL_MINUTES', '5'))
```

---

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Check bot process
ps aux | grep main.py

# Check database
sqlite3 data/trading.db "SELECT COUNT(*) FROM trades;"

# Check logs
tail -f logs/quant_hedge_bot.log

# Monitor system resources
top -p $(pgrep -f main.py)
```

### Backup Strategy

```bash
# Daily backup (add to crontab)
0 2 * * * tar -czf /backups/quant-$(date +\%Y\%m\%d).tar.gz /app/data/

# Database backup
sqlite3 data/trading.db ".backup data/trading_backup.db"

# Upload to cloud
aws s3 cp data/trading_backup.db s3://your-bucket/backups/
```

### Log Rotation

Create `/etc/logrotate.d/quant-hedge-bot`:
```
/app/logs/quant_hedge_bot.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
}
```

---

## 🚨 Troubleshooting

### Bot Not Starting
```bash
# Check Python installation
python3 --version

# Check virtual environment
source venv/bin/activate
python -c "import pandas; print('OK')"

# Check configuration
python -c "from config import *; print('Config OK')"

# Run with debug
DEBUG_MODE=true python main.py
```

### Memory Issues
```bash
# Monitor memory usage
free -h

# Reduce data window in config.py
HISTORICAL_DAYS = 30  # Reduce from 365

# Enable garbage collection
import gc
gc.collect()
```

### Data Fetch Failures
```bash
# Test yfinance
python -c "import yfinance; yf.download('BTC-USD')"

# Check internet connection
ping 8.8.8.8

# Check API rate limits
# Increase RUN_INTERVAL_MINUTES in config.py
```

### Dashboard Not Accessible
```bash
# Check Streamlit
netstat -tulpn | grep 8501

# Restart Streamlit
pkill -f streamlit
streamlit run dashboard/dashboard.py

# Check firewall rules
sudo ufw allow 8501
```

---

## 📈 Performance Optimization

### Database Optimization

```sql
-- Add indices for faster queries
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_date ON trades(timestamp);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- Vacuum database
VACUUM;
```

### Code Optimization

1. **Vectorize operations**
```python
# Instead of loop
prices_list = [data['Close'].iloc[i] * multiplier for i in range(len(data))]

# Use vectorized operation
prices = data['Close'] * multiplier
```

2. **Cache calculations**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(symbol):
    return calculate(symbol)
```

3. **Reduce data size**
```python
# Store only necessary columns
df = df[['Close', 'Volume', 'Date']]

# Use appropriate dtypes
df['Date'] = pd.to_datetime(df['Date'])
df['Close'] = df['Close'].astype('float32')
```

---

## 🔒 Security Hardening

1. **Firewall Rules**
```bash
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 8501  # Dashboard
sudo ufw enable
```

2. **API Key Protection**
```bash
# Use environment variables, never hardcode
export TELEGRAM_TOKEN="your-token"

# Encrypt sensitive files
gpg -c config.py
```

3. **Regular Updates**
```bash
pip install --upgrade -r requirements.txt
sudo apt-get update && sudo apt-get upgrade -y
```

---

## 📊 Monitoring Tools

### uptime.robot
- Free uptime monitoring
- Email alerts when bot goes down
- Dashboard with status history

### Grafana + Prometheus
- Advanced metrics visualization
- Custom dashboards
- Long-term trend analysis

### New Relic
- Application performance monitoring
- Error tracking
- Infrastructure monitoring

---

## ✅ Pre-Deployment Checklist

- [ ] All dependencies installed
- [ ] Configuration reviewed and tested
- [ ] Database initialized and backed up
- [ ] API keys configured securely
- [ ] Notifications tested
- [ ] Backtest passed profitability check
- [ ] Risk limits set appropriately
- [ ] Logging enabled
- [ ] Monitoring configured
- [ ] Disaster recovery plan in place
- [ ] Team trained on system operation
- [ ] Documentation reviewed

---

## 🎯 Post-Deployment

### Monitor First 24 Hours
- Watch for unexpected errors
- Verify trades are executing
- Confirm database writing
- Test notifications

### First Week
- Monitor trade performance
- Review logs for issues
- Verify backup procedures
- Test recovery procedures

### Ongoing
- Daily performance review
- Weekly trade analysis
- Monthly optimization
- Quarterly strategy review

---

**Deployment Date**:  
**Version**: 1.0.0  
**Status**: Production Ready

For more information, see:
- README.md - Getting started guide
- TECH_STACK.md - Technical architecture
- PROJECT_SUMMARY.md - Complete overview
