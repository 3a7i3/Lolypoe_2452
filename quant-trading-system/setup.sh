#!/bin/bash
# Quant Trading System V5 - Setup Script

echo ""
echo "========================================"
echo "Quant Trading System V5 - Setup"
echo "========================================"
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create data directories
mkdir -p data/market_cache
mkdir -p logs

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import ccxt; import pandas; import numpy; import streamlit; print('✓ All dependencies installed successfully!')"

# Complete
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the system:"
echo "  python main.py --mode live"
echo ""
echo "To start dashboard:"
echo "  streamlit run dashboard/dashboard.py"
echo ""
echo "To run backtest:"
echo "  python main.py --mode backtest"
echo ""
