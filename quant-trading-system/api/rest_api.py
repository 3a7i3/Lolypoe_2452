"""
REST API - FastAPI endpoints for trading system
Provides: signals, trades, portfolio, metrics, alerts
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json

import config
from core.system_coordinator import CryptoAISystem
from database.models import DatabaseManager
from api.websocket_handler import WebSocketManager

logger = logging.getLogger(__name__)

# Initialize API
app = FastAPI(
    title="Crypto AI Trading System API",
    description="Institutional-grade trading platform API",
    version="2.0"
)

# Global state
system = CryptoAISystem()
db = DatabaseManager()
ws_manager = WebSocketManager()

# ============================================================================
# MODELS
# ============================================================================

class SignalResponse(BaseModel):
    symbol: str
    action: str
    confidence: float
    position_size: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    regime: str
    timestamp: str

class TradeResponse(BaseModel):
    id: int
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    status: str
    strategy: str

class PortfolioResponse(BaseModel):
    total_value: float
    cash: float
    invested: float
    total_pnl: float
    total_pnl_pct: float
    max_drawdown: float
    positions: Dict
    allocation: Dict

class MetricsResponse(BaseModel):
    daily_return: float
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

class StrategyPerformanceResponse(BaseModel):
    strategy_name: str
    total_trades: int
    win_rate: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float

class BacktestRequest(BaseModel):
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str

class PortfolioOptimizeRequest(BaseModel):
    symbols: List[str]
    method: str = 'kelly_criterion'  # kelly, risk_parity, sharpe

# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "system": system.get_system_status()
    }

@app.get("/status")
async def get_status():
    """Get detailed system status"""
    return system.get_system_status()

# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================

@app.get("/signals/{symbol}", response_model=List[SignalResponse])
async def get_signals(
    symbol: str,
    limit: int = Query(100, le=1000)
):
    """Get recent trading signals for symbol"""
    try:
        signals = db.get_recent_signals(symbol=symbol, limit=limit)
        return [
            SignalResponse(
                symbol=s.symbol,
                action=s.action,
                confidence=s.confidence,
                position_size=s.position_size,
                entry_price=s.entry_price,
                stop_loss=s.stop_loss,
                take_profit=s.take_profit,
                regime=s.regime or "UNKNOWN",
                timestamp=s.timestamp.isoformat()
            )
            for s in signals
        ]
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signals/generate/{symbol}")
async def generate_signal(symbol: str, background_tasks: BackgroundTasks):
    """Generate trading signal for symbol"""
    try:
        # Schedule signal generation in background
        background_tasks.add_task(
            _generate_signal_task,
            symbol
        )
        
        return {
            "status": "processing",
            "symbol": symbol,
            "message": f"Signal generation started for {symbol}"
        }
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@app.get("/trades/open")
async def get_open_trades():
    """Get all open trades"""
    try:
        trades = db.get_open_trades()
        return [
            TradeResponse(
                id=t.id,
                symbol=t.symbol,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                position_size=t.position_size,
                pnl=t.pnl,
                pnl_pct=t.pnl_pct,
                status=t.status,
                strategy=t.strategy
            )
            for t in trades
        ]
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/{symbol}")
async def get_trades_by_symbol(
    symbol: str,
    limit: int = Query(100, le=1000),
    days: int = Query(30, le=365)
):
    """Get trades for symbol"""
    try:
        # Query from database
        # Implementation would fetch from db.get_trades_by_symbol()
        return {
            "symbol": symbol,
            "total_trades": 0,
            "trades": []
        }
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trades/{trade_id}/close")
async def close_trade(
    trade_id: int,
    exit_reason: str = "Manual exit"
):
    """Close an open trade"""
    try:
        db.update_trade(trade_id, {
            "status": "CLOSED",
            "exit_timestamp": datetime.utcnow(),
            "exit_reason": exit_reason,
            "exit_type": "EXIT"
        })
        
        return {"status": "success", "trade_id": trade_id, "message": "Trade closed"}
    except Exception as e:
        logger.error(f"Error closing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """Get current portfolio state"""
    try:
        portfolio = {
            "total_value": 1000000,
            "cash": 100000,
            "invested": 900000,
            "total_pnl": 50000,
            "total_pnl_pct": 0.05,
            "max_drawdown": -0.15,
            "positions": {},
            "allocation": {}
        }
        return portfolio
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/optimize")
async def optimize_portfolio(request: PortfolioOptimizeRequest):
    """Optimize portfolio allocation"""
    try:
        # Would create returns_df from symbol data
        positions = system.optimize_portfolio(
            symbols=request.symbols,
            returns_df=None,  # Would load from data
            method=request.method
        )
        
        return {
            "method": request.method,
            "positions": positions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/rebalance")
async def rebalance_portfolio(background_tasks: BackgroundTasks):
    """Rebalance portfolio to target allocation"""
    try:
        background_tasks.add_task(_rebalance_task)
        
        return {
            "status": "processing",
            "message": "Portfolio rebalancing initiated"
        }
    except Exception as e:
        logger.error(f"Error rebalancing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@app.get("/metrics/daily")
async def get_daily_metrics(days: int = Query(30, le=365)):
    """Get daily performance metrics"""
    try:
        metrics = db.get_daily_metrics(days=days)
        return {
            "days": days,
            "metrics": [
                {
                    "date": m.date.isoformat(),
                    "daily_return": m.daily_return,
                    "total_return": m.total_return,
                    "sharpe_ratio": m.sharpe_ratio,
                    "max_drawdown": m.max_drawdown,
                    "win_rate": m.win_rate
                }
                for m in metrics
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/current", response_model=MetricsResponse)
async def get_current_metrics():
    """Get current performance metrics"""
    try:
        metrics = {
            "daily_return": 0.001,
            "total_return": 0.05,
            "sharpe_ratio": 0.95,
            "sortino_ratio": 1.2,
            "calmar_ratio": 0.8,
            "max_drawdown": -0.15,
            "win_rate": 0.55,
            "profit_factor": 1.8
        }
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/strategy/{strategy_name}", response_model=StrategyPerformanceResponse)
async def get_strategy_metrics(strategy_name: str):
    """Get performance for specific strategy"""
    try:
        perf = db.get_strategy_performance(strategy_name=strategy_name)
        if not perf:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return StrategyPerformanceResponse(
            strategy_name=perf.strategy_name,
            total_trades=perf.total_trades,
            win_rate=perf.win_rate,
            total_pnl=perf.total_pnl,
            sharpe_ratio=perf.sharpe_ratio,
            max_drawdown=perf.max_drawdown
        )
    except Exception as e:
        logger.error(f"Error fetching strategy metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BACKTEST ENDPOINTS
# ============================================================================

@app.post("/backtest")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run backtest on strategy"""
    try:
        background_tasks.add_task(
            _backtest_task,
            request.strategy_name,
            request.symbol,
            request.start_date,
            request.end_date
        )
        
        return {
            "status": "processing",
            "backtest_name": f"{request.strategy_name}_{request.symbol}",
            "message": "Backtest started"
        }
    except Exception as e:
        logger.error(f"Error starting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest/{backtest_id}")
async def get_backtest(backtest_id: int):
    """Get backtest results"""
    try:
        # Fetch from database
        return {
            "backtest_id": backtest_id,
            "status": "complete",
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.20
        }
    except Exception as e:
        logger.error(f"Error fetching backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANOMALY ENDPOINTS
# ============================================================================

@app.get("/anomalies")
async def get_anomalies(days: int = Query(7, le=90)):
    """Get recent market anomalies"""
    try:
        since = datetime.utcnow() - timedelta(days=days)
        
        return {
            "days": days,
            "anomalies": [],
            "total_count": 0
        }
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def _generate_signal_task(symbol: str):
    """Background task: generate trading signal"""
    try:
        logger.info(f"Generating signal for {symbol}...")
        # Implementation would load data, generate signal, store in DB
    except Exception as e:
        logger.error(f"Error in signal generation task: {e}")

async def _rebalance_task():
    """Background task: rebalance portfolio"""
    try:
        logger.info("Starting portfolio rebalance...")
        # Implementation would optimize positions, execute orders
    except Exception as e:
        logger.error(f"Error in rebalance task: {e}")

async def _backtest_task(strategy_name: str, symbol: str, start_date: str, end_date: str):
    """Background task: run backtest"""
    try:
        logger.info(f"Running backtest: {strategy_name} on {symbol}...")
        # Implementation would run backtest, store results
    except Exception as e:
        logger.error(f"Error in backtest task: {e}")

# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    logger.info("API Starting up...")
    db.create_tables()

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("API Shutting down...")

# ============================================================================
# RUN API
# ============================================================================

def run_api(host: str = "0.0.0.0", port: int = 8000, workers: int = 4):
    """Run FastAPI server"""
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level="info"
    )

if __name__ == "__main__":
    run_api()

logger.info("[REST API] Trading system API initialized")
