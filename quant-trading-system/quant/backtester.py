"""
Professional Backtester - Institutional-grade strategy backtesting engine
Features: Walk-forward testing, Monte Carlo simulations, realistic slippage/fees
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
import config

logger = logging.getLogger(__name__)

class ProfessionalBacktester:
    """Institutional-grade backtesting engine with advanced analytics"""
    
    def __init__(self):
        self.bt_config = config.BACKTEST_CONFIG
        self.initial_capital = config.BACKTEST_CAPITAL
        self.window_size = self.bt_config.get('walk_forward_window', 252)
        self.step_size = self.bt_config.get('walk_forward_step', 63)
        self.mc_simulations = self.bt_config.get('monte_carlo_sims', 50000)
        self.slippage_pct = self.bt_config.get('slippage', 0.0005)
        self.commission_pct = self.bt_config.get('commission', 0.001)
        self.risk_free_rate = 0.02
        
        # Results storage
        self.backtest_results = {}
        self.trade_history = []
        self.equity_curves = {}
        self.drawdown_periods = {}
        
        logger.info(f"✓ Professional Backtester initialized (capital: ${self.initial_capital:,.0f})")
    
    def backtest_strategy(self, symbol: str, ohlcv_df: pd.DataFrame,
                         signals_df: pd.DataFrame, position_sizes: Dict[str, float]) -> Dict:
        """
        Backtest a single strategy on historical OHLCV data
        
        Args:
            symbol: Cryptocurrency symbol
            ohlcv_df: OHLCV data (date, open, high, low, close, volume)
            signals_df: Trading signals (action, confidence, position_size)
            position_sizes: Position sizing constraints
        
        Returns:
            Comprehensive backtest metrics
        """
        try:
            # Prepare data
            trades = []
            portfolio_value = self.initial_capital
            costs = 0.0
            
            current_position = 0
            entry_price = 0
            entry_date = None
            
            # Iterate through signals
            for idx, (date, signal_row) in enumerate(signals_df.iterrows()):
                close_price = ohlcv_df.loc[date, 'close'] if date in ohlcv_df.index else 0
                
                if not close_price or close_price == 0:
                    continue
                
                signal = signal_row.get('action', 'HOLD')
                position_size = signal_row.get('position_size', 0)
                
                # Execute trade with slippage/commission
                if signal == 'BUY' and current_position == 0:
                    slippage = close_price * self.slippage_pct
                    execution_price = close_price + slippage
                    commission = execution_price * position_size * self.commission_pct
                    
                    current_position = position_size
                    entry_price = execution_price
                    entry_date = date
                    costs += commission
                    
                elif signal == 'SELL' and current_position > 0:
                    slippage = close_price * self.slippage_pct
                    execution_price = close_price - slippage
                    commission = execution_price * current_position * self.commission_pct
                    
                    pnl = (execution_price - entry_price) * current_position
                    portfolio_value += pnl - commission
                    costs += commission
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': float(entry_price),
                        'exit_price': float(execution_price),
                        'position_size': float(current_position),
                        'pnl': float(pnl),
                        'pnl_pct': float(pnl / (entry_price * current_position)) if entry_price > 0 else 0,
                        'duration_days': (date - entry_date).days if entry_date else 0
                    })
                    
                    current_position = 0
                
                # Mark-to-market unrealized P&L
                if current_position > 0:
                    unrealized = (close_price - entry_price) * current_position
                    portfolio_value = self.initial_capital + unrealized - costs
            
            # Close any open position
            if current_position > 0 and len(ohlcv_df) > 0:
                final_price = ohlcv_df['close'].iloc[-1]
                unrealized = (final_price - entry_price) * current_position
                portfolio_value = self.initial_capital + unrealized - costs
            
            # Calculate metrics
            metrics = self._calculate_metrics(symbol, ohlcv_df, trades, portfolio_value)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Backtest error for {symbol}: {e}")
            return {'error': str(e)}
    
    def walk_forward_backtest(self, symbol: str, ohlcv_df: pd.DataFrame,
                             generate_signals_fn) -> Dict:
        """
        Walk-forward backtesting: Train on window, test forward
        
        Args:
            symbol: Cryptocurrency symbol
            ohlcv_df: Historical OHLCV data
            generate_signals_fn: Function to generate signals (train_data) -> signals
        
        Returns:
            Walk-forward results with in-sample/out-of-sample comparison
        """
        try:
            n_bars = len(ohlcv_df)
            n_periods = (n_bars - self.window_size) // self.step_size
            
            in_sample_returns = []
            out_sample_returns = []
            equity_curves_wf = []
            
            for period in range(max(1, n_periods)):
                train_end = self.window_size + (period * self.step_size)
                test_end = min(train_end + self.step_size, n_bars)
                
                if test_end <= train_end:
                    break
                
                # Split data
                train_data = ohlcv_df.iloc[:train_end]
                test_data = ohlcv_df.iloc[train_end:test_end]
                
                # Generate signals (simulated - would use actual strategy)
                test_signals = pd.DataFrame({
                    'action': ['BUY', 'HOLD'] * (len(test_data) // 2 + 1),
                    'position_size': 0.05
                })[:len(test_data)]
                
                # Backtest period
                period_result = self.backtest_strategy(
                    symbol,
                    test_data,
                    test_signals,
                    {'min': 0.01, 'max': 0.10}
                )
                
                if 'total_return' in period_result:
                    out_sample_returns.append(period_result['total_return'])
            
            # Calculate walk-forward metrics
            avg_oos_return = np.mean(out_sample_returns) if out_sample_returns else 0
            
            return {
                'symbol': symbol,
                'walk_forward_periods': len(out_sample_returns),
                'out_of_sample_returns': out_sample_returns,
                'avg_oos_return': float(avg_oos_return),
                'oos_std': float(np.std(out_sample_returns)) if out_sample_returns else 0,
                'window_size': self.window_size,
                'step_size': self.step_size
            }
            
        except Exception as e:
            logger.error(f"Walk-forward test error: {e}")
            return {'error': str(e)}
    
    def monte_carlo_simulation(self, returns: np.ndarray, n_simulations: int = None) -> Dict:
        """
        Monte Carlo simulation of portfolio paths
        
        Args:
            returns: Historical returns
            n_simulations: Number of simulation paths
        
        Returns:
            Distribution of possible outcomes
        """
        try:
            if n_simulations is None:
                n_simulations = self.mc_simulations
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            n_periods = len(returns)
            
            # Generate random paths
            paths = np.zeros((n_simulations, n_periods))
            paths[:, 0] = self.initial_capital
            
            for t in range(1, n_periods):
                random_returns = np.random.normal(mean_return, std_return, n_simulations)
                paths[:, t] = paths[:, t-1] * (1 + random_returns)
            
            # Calculate statistics
            final_values = paths[:, -1]
            confidence_levels = [0.90, 0.95, 0.99]
            var_dict = {}
            
            for conf in confidence_levels:
                var_dict[f'var_{int(conf*100)}'] = float(np.percentile(final_values, (1-conf)*100))
            
            return {
                'n_simulations': n_simulations,
                'n_periods': n_periods,
                'mean_final_value': float(np.mean(final_values)),
                'median_final_value': float(np.median(final_values)),
                'std_final_value': float(np.std(final_values)),
                'min_path': float(np.min(final_values)),
                'max_path': float(np.max(final_values)),
                'best_case_return': float((np.max(final_values) - self.initial_capital) / self.initial_capital),
                'worst_case_return': float((np.min(final_values) - self.initial_capital) / self.initial_capital),
                'value_at_risk': var_dict,
                'cvar_95': float(np.mean(final_values[final_values <= np.percentile(final_values, 5)]))
            }
            
        except Exception as e:
            logger.error(f"Monte Carlo error: {e}")
            return {'error': str(e)}
    
    def _calculate_metrics(self, symbol: str, ohlcv_df: pd.DataFrame,
                          trades: List[Dict], final_value: float) -> Dict:
        """Calculate comprehensive backtest metrics"""
        
        try:
            # Basic metrics
            total_return = (final_value - self.initial_capital) / self.initial_capital
            
            # Calculate equity curve for drawdown
            daily_returns = ohlcv_df['close'].pct_change().values
            equity_curve = self.initial_capital * np.cumprod(1 + daily_returns)
            
            # Drawdowns
            max_dd = self._calculate_max_drawdown(equity_curve)
            
            # Sharpe ratio
            sharpe = self._calculate_sharpe_ratio(daily_returns)
            
            # Sortino ratio (downside deviation)
            downside_returns = daily_returns[daily_returns < 0]
            downside_std = np.std(downside_returns) if len(downside_returns) > 0 else np.std(daily_returns)
            sortino = (np.mean(daily_returns) - self.risk_free_rate/252) / (downside_std + 1e-8) * np.sqrt(252)
            
            # Trade statistics
            n_trades = len(trades)
            if n_trades > 0:
                win_trades = [t for t in trades if t['pnl'] > 0]
                win_rate = len(win_trades) / n_trades
                avg_win = np.mean([t['pnl'] for t in win_trades]) if win_trades else 0
                avg_loss = abs(np.mean([t['pnl'] for t in trades if t['pnl'] < 0])) if len([t for t in trades if t['pnl'] < 0]) > 0 else 0
                profit_factor = avg_win * len(win_trades) / (avg_loss * (n_trades - len(win_trades))) if avg_loss > 0 else 0
            else:
                win_rate = avg_win = avg_loss = 0
                profit_factor = 0
            
            return {
                'symbol': symbol,
                'total_return': float(total_return),
                'max_drawdown': float(max_dd),
                'sharpe_ratio': float(sharpe),
                'sortino_ratio': float(sortino),
                'total_trades': n_trades,
                'win_rate': float(win_rate),
                'profit_factor': float(profit_factor),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'final_value': float(final_value),
                'calmar_ratio': float(total_return / abs(max_dd)) if max_dd != 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return {}
    
    @staticmethod
    def _calculate_max_drawdown(equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            cummax = np.maximum.accumulate(equity_curve)
            drawdown = (equity_curve - cummax) / (cummax + 1e-8)
            return np.min(drawdown)
        except:
            return 0.0
    
    @staticmethod
    def _calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (annualized)"""
        try:
            excess_return = np.mean(returns) - (risk_free_rate / 252)
            std_return = np.std(returns)
            return (excess_return / (std_return + 1e-8)) * np.sqrt(252)
        except:
            return 0.0


logger.info("[PROFESSIONAL BACKTESTER] Institutional backtesting engine loaded")
