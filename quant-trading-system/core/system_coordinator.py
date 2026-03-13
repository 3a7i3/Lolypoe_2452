"""
System Integration Coordinator - Orchestrates all AI system components
Coordinates: Market scanner, feature engineering, strategy engine, anomaly/regime detection
Plus: ML models, portfolio optimization, backtester, and risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import asyncio

import config
from core.market_scanner import MarketScanner
from core.data_pipeline import AdvancedDataPipeline
from core.strategy_engine import InstitutionalStrategyEngine
from ai.feature_engineering import AdvancedFeatureEngineer
from ai.anomaly_detection import AnomalyDetector
from ai.regime_detection import RegimeDetector
from ai.lstm_trainer import LSTMTrainer
from ai.rl_trading_agent import RLTradingAgent
from quant.kelly_optimizer import KellyCriterionOptimizer
from quant.risk_parity_optimizer import RiskParityOptimizer
from quant.sharpe_optimizer import SharpeOptimizer
from quant.backtester import ProfessionalBacktester

logger = logging.getLogger(__name__)

class CryptoAISystem:
    """Institutional-grade cryptocurrency AI trading system"""
    
    def __init__(self):
        logger.info("[CRYPTO AI SYSTEM] Initializing institutional trading infrastructure...")
        
        # Core infrastructure
        self.market_scanner = MarketScanner()
        self.data_pipeline = AdvancedDataPipeline()
        self.strategy_engine = InstitutionalStrategyEngine()
        
        # AI/ML components
        self.feature_engineer = AdvancedFeatureEngineer()
        self.anomaly_detector = AnomalyDetector()
        self.regime_detector = RegimeDetector()
        
        # Model training
        self.lstm_trainer = LSTMTrainer()
        self.rl_agent = RLTradingAgent()
        
        # Portfolio optimization
        self.kelly_optimizer = KellyCriterionOptimizer()
        self.risk_parity_optimizer = RiskParityOptimizer()
        self.sharpe_optimizer = SharpeOptimizer()
        
        # Backtesting
        self.backtester = ProfessionalBacktester()
        
        # System state
        self.system_status = {
            'initialized_at': datetime.now().isoformat(),
            'market_data_loaded': False,
            'models_trained': False,
            'portfolio_optimized': False,
            'last_update': None,
            'total_signals_generated': 0,
            'total_anomalies_detected': 0,
            'active_positions': {}
        }
        
        logger.info("✓ Crypto AI System fully initialized")
    
    async def scan_universe(self, n_top: int = 50) -> Dict:
        """
        Scan entire cryptocurrency universe
        
        Returns: Top performing cryptos with market data
        """
        try:
            logger.info(f"[SYSTEM] Scanning universe for top {n_top} cryptos...")
            
            # Scan market
            scan_results = await self.market_scanner.scan_crypto_universe(n_top=n_top)
            
            self.system_status['market_data_loaded'] = True
            self.system_status['last_update'] = datetime.now().isoformat()
            
            logger.info(f"✓ Universe scan complete: {len(scan_results)} assets")
            
            return scan_results
            
        except Exception as e:
            logger.error(f"Universe scan error: {e}")
            return {}
    
    async def load_training_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Load historical data for training
        
        Args:
            symbols: List of crypto symbols
        
        Returns:
            {symbol: ohlcv_dataframe} dictionary
        """
        try:
            logger.info(f"[SYSTEM] Loading training data for {len(symbols)} symbols...")
            
            data = await self.data_pipeline.load_batch_parallel(
                symbols,
                timeframe='1d',
                limit=1095  # 3 years
            )
            
            logger.info(f"✓ Training data loaded: {len(data)} symbols")
            
            return data
            
        except Exception as e:
            logger.error(f"Data loading error: {e}")
            return {}
    
    async def generate_trading_signals(self, symbol: str, ohlcv_df: pd.DataFrame,
                                      indicators: Dict) -> Dict:
        """
        Generate ensemble trading signal with all components
        
        Args:
            symbol: Cryptocurrency symbol
            ohlcv_df: OHLCV data
            indicators: Technical indicators
        
        Returns:
            Comprehensive trading signal with AI components
        """
        try:
            # 1. Detect market regime
            regime_result = self.regime_detector.detect_regime(ohlcv_df, indicators)
            regime = regime_result['regime']
            regime_confidence = regime_result['confidence']
            
            # 2. Detect anomalies
            anomalies = self.anomaly_detector.detect_specific_anomalies(
                ohlcv_df, symbol, indicators
            )
            has_anomalies = len(anomalies) > 0
            
            # 3. Generate strategy signals
            strategy_signal = await self.strategy_engine.generate_ensemble_signal(
                symbol, ohlcv_df, indicators
            )
            
            # 4. Get regime-based signal
            regime_signal = self.regime_detector.get_regime_signal()
            
            # 5. Generate RL signal (if trained)
            if symbol in self.rl_agent.agents:
                # Extract state for RL (simplified)
                state = np.array(list(indicators.values())[:20])
                rl_signal = self.rl_agent.generate_signal(state, symbol)
            else:
                rl_signal = {'action': 'HOLD', 'confidence': 0.5}
            
            # 6. Aggregate all signals
            final_signal = self._aggregate_signals(
                strategy_signal,
                regime_signal,
                rl_signal,
                has_anomalies
            )
            
            self.system_status['total_signals_generated'] += 1
            
            return final_signal
            
        except Exception as e:
            logger.error(f"Signal generation error for {symbol}: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'error': str(e)}
    
    def _aggregate_signals(self, strategy_signal: Dict, regime_signal: Dict,
                          rl_signal: Dict, has_anomalies: bool) -> Dict:
        """Aggregate signals from multiple sources"""
        
        # Weighted voting
        weights = {
            'strategy': 0.4,
            'regime': 0.3,
            'rl': 0.3
        }
        
        # Map actions to scores
        action_scores = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
        
        weighted_score = (
            action_scores.get(strategy_signal.get('action', 'HOLD'), 0) * weights['strategy'] +
            action_scores.get(regime_signal.get('action', 'HOLD'), 0) * weights['regime'] +
            action_scores.get(rl_signal.get('action', 'HOLD'), 0) * weights['rl']
        )
        
        # Determine final action
        if weighted_score > 0.3:
            final_action = 'BUY'
        elif weighted_score < -0.3:
            final_action = 'SELL'
        else:
            final_action = 'HOLD'
        
        # Average confidence
        avg_confidence = np.mean([
            strategy_signal.get('confidence', 0.5),
            regime_signal.get('confidence', 0.5),
            rl_signal.get('confidence', 0.5)
        ])
        
        # Reduce confidence if anomalies detected
        if has_anomalies:
            avg_confidence *= 0.7
            logger.warning("Anomalies detected - signal confidence reduced")
        
        return {
            'symbol': strategy_signal.get('symbol'),
            'action': final_action,
            'confidence': float(avg_confidence),
            'position_size': strategy_signal.get('position_size', 0),
            'entry_price': strategy_signal.get('entry_price'),
            'stop_loss': strategy_signal.get('stop_loss'),
            'take_profit': strategy_signal.get('take_profit'),
            'components': {
                'strategy_signal': strategy_signal,
                'regime_signal': regime_signal,
                'rl_signal': rl_signal
            },
            'has_anomalies': has_anomalies,
            'timestamp': datetime.now().isoformat()
        }
    
    async def optimize_portfolio(self, symbols: List[str], returns_df: pd.DataFrame,
                                method: str = 'kelly_criterion') -> Dict[str, float]:
        """
        Optimize portfolio allocation
        
        Args:
            symbols: List of symbols
            returns_df: Historical returns
            method: 'kelly_criterion' (default), 'risk_parity', or 'sharpe_maximization'
        
        Returns:
            {symbol: position_size} dictionary
        """
        try:
            logger.info(f"[SYSTEM] Optimizing portfolio using {method}...")
            
            # Calculate required metrics
            volatilities = returns_df.std() * np.sqrt(252)  # Annualized
            sharpe_ratios = self._calculate_sharpe_ratios(returns_df)
            win_rates = self._calculate_win_rates(returns_df)
            
            # Run optimizer
            if method == 'kelly_criterion':
                positions = self.kelly_optimizer.optimize_positions(
                    returns_df, sharpe_ratios, win_rates
                )
            elif method == 'risk_parity':
                positions = self.risk_parity_optimizer.optimize_positions(
                    returns_df, dict(volatilities)
                )
            elif method == 'sharpe_maximization':
                positions = self.sharpe_optimizer.optimize_positions(
                    returns_df, sharpe_ratios
                )
            else:
                logger.error(f"Unknown optimization method: {method}")
                positions = {s: 1.0/len(symbols) for s in symbols}
            
            self.system_status['portfolio_optimized'] = True
            
            logger.info(f"✓ Portfolio optimized: {len(positions)} positions")
            
            return positions
            
        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
            return {}
    
    @staticmethod
    def _calculate_sharpe_ratios(returns_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Sharpe ratios for each asset"""
        risk_free_rate = 0.02 / 252
        
        sharpe_dict = {}
        for col in returns_df.columns:
            returns = returns_df[col].dropna()
            excess_return = returns.mean() - risk_free_rate
            std_return = returns.std()
            
            if std_return > 0:
                sharpe_dict[col] = excess_return / std_return * np.sqrt(252)
            else:
                sharpe_dict[col] = 0.0
        
        return sharpe_dict
    
    @staticmethod
    def _calculate_win_rates(returns_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate historical win rates"""
        win_rates = {}
        
        for col in returns_df.columns:
            returns = returns_df[col].dropna()
            win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0.5
            win_rates[col] = win_rate
        
        return win_rates
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        self.system_status['current_time'] = datetime.now().isoformat()
        
        return {
            'status': self.system_status,
            'components': {
                'market_scanner': f"✓ Ready ({self.market_scanner.n_symbols} symbols)",
                'data_pipeline': f"✓ Ready (16 workers, {len(self.data_pipeline.cache)} cached)",
                'strategy_engine': f"✓ Ready (5 strategies)",
                'anomaly_detector': f"✓ Ready ({self.anomaly_detector.anomaly_stats['total_anomalies']} detected)",
                'regime_detector': f"✓ Ready (regime: {self.regime_detector.current_regime})",
                'lstm_trainer': f"✓ Ready ({len(self.lstm_trainer.models)} models)",
                'rl_agent': f"✓ Ready ({len(self.rl_agent.agents)} agents)",
                'portfolio_optimizers': "✓ Ready (Kelly, Risk Parity, Sharpe)",
                'backtester': "✓ Ready (Walk-forward, Monte Carlo)"
            }
        }


logger.info("[CRYPTO AI SYSTEM] System orchestration layer ready")
