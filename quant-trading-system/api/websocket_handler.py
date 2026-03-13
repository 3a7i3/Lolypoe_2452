"""
WebSocket Handler - Real-time streaming for dashboard
Sends: price updates, signals, trades, portfolio changes
"""

import asyncio
import logging
import json
from typing import Set, Dict, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.subscription_counts: Dict[str, int] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Accept WebSocket connection for channel"""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
            self.subscription_counts[channel] = 0
        
        self.active_connections[channel].add(websocket)
        self.subscription_counts[channel] += 1
        
        logger.info(f"Client connected to {channel} ({self.subscription_counts[channel]} subscribers)")
    
    async def disconnect(self, websocket: WebSocket, channel: str):
        """Remove WebSocket connection"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            self.subscription_counts[channel] = len(self.active_connections[channel])
            
            logger.info(f"Client disconnected from {channel} ({self.subscription_counts[channel]} subscribers)")
    
    async def broadcast(self, channel: str, message: Dict):
        """Broadcast message to all subscribers of channel"""
        if channel not in self.active_connections:
            return
        
        message['timestamp'] = datetime.utcnow().isoformat()
        message_json = json.dumps(message)
        
        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error sending to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection, channel)
    
    async def broadcast_price_update(self, symbol: str, price: float, volume: float):
        """Broadcast price update"""
        await self.broadcast(f"price_{symbol}", {
            "type": "price_update",
            "symbol": symbol,
            "price": price,
            "volume": volume
        })
    
    async def broadcast_signal(self, signal_data: Dict):
        """Broadcast new trading signal"""
        symbol = signal_data.get('symbol', 'ALL')
        await self.broadcast(f"signals_{symbol}", {
            "type": "new_signal",
            "data": signal_data
        })
        
        # Also broadcast to general signals channel
        await self.broadcast("signals", {
            "type": "new_signal",
            "data": signal_data
        })
    
    async def broadcast_trade_executed(self, trade_data: Dict):
        """Broadcast executed trade"""
        symbol = trade_data.get('symbol', 'ALL')
        await self.broadcast(f"trades_{symbol}", {
            "type": "trade_executed",
            "data": trade_data
        })
        
        # Also broadcast to portfolio channel
        await self.broadcast("portfolio", {
            "type": "trade_executed",
            "data": trade_data
        })
    
    async def broadcast_portfolio_update(self, portfolio_data: Dict):
        """Broadcast portfolio state change"""
        await self.broadcast("portfolio", {
            "type": "portfolio_update",
            "data": portfolio_data
        })
    
    async def broadcast_metrics_update(self, metrics_data: Dict):
        """Broadcast metrics update"""
        await self.broadcast("metrics", {
            "type": "metrics_update",
            "data": metrics_data
        })
    
    async def broadcast_anomaly(self, anomaly_data: Dict):
        """Broadcast detected anomaly"""
        symbol = anomaly_data.get('symbol', 'ALL')
        await self.broadcast(f"anomalies_{symbol}", {
            "type": "anomaly_detected",
            "data": anomaly_data
        })
    
    async def broadcast_alert(self, alert_data: Dict):
        """Broadcast system alert"""
        await self.broadcast("alerts", {
            "type": "alert",
            "data": alert_data
        })
    
    def get_stats(self) -> Dict:
        """Get WebSocket statistics"""
        total_connections = sum(len(conn) for conn in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "active_channels": len(self.active_connections),
            "channels": {
                channel: count
                for channel, count in self.subscription_counts.items()
                if count > 0
            }
        }


# Example WebSocket endpoints to add to FastAPI app:

"""
@app.websocket("/ws/prices/{symbol}")
async def websocket_prices(websocket: WebSocket, symbol: str):
    await ws_manager.connect(websocket, f"price_{symbol}")
    try:
        while True:
            data = await websocket.receive_text()
            # Process incoming messages if needed
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, f"price_{symbol}")

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await ws_manager.connect(websocket, "signals")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "signals")

@app.websocket("/ws/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    await ws_manager.connect(websocket, "portfolio")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "portfolio")

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await ws_manager.connect(websocket, "metrics")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "metrics")

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket, "alerts")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "alerts")
"""

logger.info("[WEBSOCKET MANAGER] Real-time streaming initialized")
