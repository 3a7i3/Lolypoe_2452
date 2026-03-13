"""
Monitoring & Logging System
Real-time system health and performance tracking
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System health metrics"""
    timestamp: datetime
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_agents: int = 0
    pending_trades: int = 0
    completed_trades: int = 0
    total_pnl: float = 0.0
    error_count: int = 0
    last_trade_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'active_agents': self.active_agents,
            'pending_trades': self.pending_trades,
            'completed_trades': self.completed_trades,
            'total_pnl': self.total_pnl,
            'error_count': self.error_count,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None
        }


@dataclass
class Alert:
    """Alert notification"""
    level: str  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class MonitoringSystem:
    """System monitoring and health tracking"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        self.max_history = 1000
        
        logger.info("MonitoringSystem initialized")
    
    def record_metrics(self, metrics: SystemMetrics):
        """Record system metrics"""
        self.metrics_history.append(metrics)
        
        # Keep only recent history
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        # Check thresholds
        self._check_thresholds(metrics)
    
    def _check_thresholds(self, metrics: SystemMetrics):
        """Check if metrics exceed thresholds"""
        if metrics.cpu_usage > 90:
            self.create_alert(Alert(
                level='WARNING',
                title='High CPU Usage',
                message=f'CPU usage at {metrics.cpu_usage:.1f}%',
                metadata={'cpu_usage': metrics.cpu_usage}
            ))
        
        if metrics.memory_usage > 85:
            self.create_alert(Alert(
                level='WARNING',
                title='High Memory Usage',
                message=f'Memory usage at {metrics.memory_usage:.1f}%',
                metadata={'memory_usage': metrics.memory_usage}
            ))
        
        if metrics.error_count > 10:
            self.create_alert(Alert(
                level='ERROR',
                title='High Error Rate',
                message=f'Error count: {metrics.error_count}',
                metadata={'error_count': metrics.error_count}
            ))
    
    def create_alert(self, alert: Alert):
        """Create and log alert"""
        self.alerts.append(alert)
        
        # Log based on level
        if alert.level == 'INFO':
            logger.info(f"[{alert.level}] {alert.title}: {alert.message}")
        elif alert.level == 'WARNING':
            logger.warning(f"[{alert.level}] {alert.title}: {alert.message}")
        elif alert.level == 'ERROR':
            logger.error(f"[{alert.level}] {alert.title}: {alert.message}")
        elif alert.level == 'CRITICAL':
            logger.critical(f"[{alert.level}] {alert.title}: {alert.message}")
        
        # Keep only recent alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def get_latest_metrics(self) -> Optional[SystemMetrics]:
        """Get latest metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_recent_alerts(self, level: Optional[str] = None, limit: int = 50) -> List[Alert]:
        """Get recent alerts"""
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[-limit:]
    
    def get_metrics_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict:
        """Get metrics summary for time window"""
        cutoff = datetime.now() - time_window
        recent = [m for m in self.metrics_history if m.timestamp >= cutoff]
        
        if not recent:
            return {}
        
        return {
            'count': len(recent),
            'avg_cpu': sum(m.cpu_usage for m in recent) / len(recent),
            'max_cpu': max(m.cpu_usage for m in recent),
            'avg_memory': sum(m.memory_usage for m in recent) / len(recent),
            'max_memory': max(m.memory_usage for m in recent),
            'total_trades': sum(m.completed_trades for m in recent),
            'total_errors': sum(m.error_count for m in recent),
            'total_pnl': recent[-1].total_pnl if recent else 0
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics to format"""
        latest = self.get_latest_metrics()
        
        if format == 'json':
            return json.dumps(latest.to_dict(), indent=2) if latest else "{}"
        else:
            return str(latest) if latest else ""


class LogHandler(logging.Handler):
    """Custom logging handler for monitoring"""
    
    def __init__(self, monitoring_system: MonitoringSystem):
        super().__init__()
        self.monitoring = monitoring_system
    
    def emit(self, record: logging.LogRecord):
        """Emit log record to monitoring system"""
        # Avoid recursive loops when alerts themselves are logged from this module.
        if record.name == __name__:
            return

        if record.levelno >= logging.ERROR:
            alert = Alert(
                level=record.levelname,
                title=record.name,
                message=record.getMessage(),
                metadata={'logger': record.name, 'module': record.module}
            )
            self.monitoring.create_alert(alert)


class PerformanceTracker:
    """Track trading performance metrics"""
    
    def __init__(self):
        self.trades: List[Dict] = []
        self.strategies: Dict[str, Dict] = {}
        
        logger.info("PerformanceTracker initialized")
    
    def record_trade(self, trade: Dict):
        """Record trade execution"""
        self.trades.append({
            **trade,
            'timestamp': datetime.now()
        })
        logger.info(f"Trade recorded: {trade['symbol']} {trade['side']} {trade['quantity']}@{trade['price']}")
    
    def update_strategy_performance(self, strategy_id: str, metrics: Dict):
        """Update strategy performance"""
        self.strategies[strategy_id] = {
            **metrics,
            'updated_at': datetime.now()
        }
    
    def get_strategy_stats(self, strategy_id: str) -> Optional[Dict]:
        """Get strategy statistics"""
        return self.strategies.get(strategy_id)
    
    def get_all_stats(self) -> Dict:
        """Get all statistics"""
        return {
            'total_trades': len(self.trades),
            'strategies': self.strategies,
            'timestamp': datetime.now().isoformat()
        }


class HealthCheck:
    """System health checker"""
    
    def __init__(self, monitoring: MonitoringSystem):
        self.monitoring = monitoring
        self.checks = {}
    
    def register_check(self, name: str, check_fn) -> None:
        """Register a health check function"""
        self.checks[name] = check_fn
    
    async def run_health_check(self) -> Dict[str, bool]:
        """Run all health checks"""
        results = {}
        
        for name, check_fn in self.checks.items():
            try:
                results[name] = await check_fn() if asyncio.iscoroutinefunction(check_fn) else check_fn()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        
        # Create alert if any check fails
        if not all(results.values()):
            failed = [name for name, result in results.items() if not result]
            self.monitoring.create_alert(Alert(
                level='WARNING',
                title='Health Check Failed',
                message=f'Failed checks: {", ".join(failed)}',
                metadata={'failed_checks': failed}
            ))
        
        return results
    
    async def continuous_health_monitoring(self, interval: int = 60):
        """Run continuous health monitoring"""
        while True:
            try:
                health_status = await self.run_health_check()
                logger.info(f"Health check completed: {health_status}")
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(interval)


# Demo usage
async def demo():
    """Demonstrate monitoring system"""
    logger.info("\n" + "="*60)
    logger.info("Monitoring System Demo")
    logger.info("="*60)
    
    # Setup monitoring
    monitoring = MonitoringSystem()
    
    # Add custom logging handler
    log_handler = LogHandler(monitoring)
    logging.getLogger().addHandler(log_handler)
    
    # Setup health checks
    health = HealthCheck(monitoring)
    health.register_check('database', lambda: True)
    health.register_check('exchange_api', lambda: True)
    
    logger.info("\n📊 Recording system metrics...")
    
    # Record sample metrics
    for i in range(5):
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=20 + i * 10,
            memory_usage=30 + i * 5,
            active_agents=5,
            pending_trades=2,
            completed_trades=10 + i,
            total_pnl=1000 * (i + 1),
            error_count=i
        )
        monitoring.record_metrics(metrics)
        logger.info(f"Metrics recorded: CPU={metrics.cpu_usage}%, Memory={metrics.memory_usage}%")
        await asyncio.sleep(0.5)
    
    logger.info("\n🏥 Running health checks...")
    health_status = await health.run_health_check()
    logger.info(f"Health status: {health_status}")
    
    logger.info("\n📈 System summary:")
    summary = monitoring.get_metrics_summary(timedelta(minutes=5))
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n⚠️  Recent alerts:")
    alerts = monitoring.get_recent_alerts(limit=10)
    for alert in alerts:
        logger.info(f"  [{alert.level}] {alert.title}: {alert.message}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(demo())
