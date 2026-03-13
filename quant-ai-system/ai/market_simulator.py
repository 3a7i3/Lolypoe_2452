"""
AI Market Simulator V7.5
Simulates market environments for agent training and strategy development
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


@dataclass
class MarketState:
    """Current market state"""
    timestamp: datetime
    price: float
    volume: float
    volatility: float
    trend: float  # -1 to 1, negative=down, positive=up
    liquidity: float


class AIMarketSimulator:
    """
    Advanced Market Simulator
    Creates synthetic but realistic market environments for strategy training
    """
    
    def __init__(self, initial_price: float = 100.0, volatility: float = 0.02):
        """
        Initialize simulator
        Args:
            initial_price: Starting price
            volatility: Price volatility
        """
        self.initial_price = initial_price
        self.volatility = volatility
        self.price = initial_price
        self.time = datetime.now()
        
        # Market regimes
        self.regime = 'normal'  # normal, bull, bear, sideways, volatile
        self.regime_change_probability = 0.01
        
        # Market characteristics
        self.liquidity = 1.0  # 0-1
        self.trend_strength = 0.0  # -1 to 1
        
        # History
        self.price_history = [initial_price]
        self.volume_history = []
        self.state_history: List[MarketState] = []
        
        self.logger = logging.getLogger("AIMarketSimulator")
        self.logger.info(f"📊 AI Market Simulator initialized (price: ${initial_price:.2f})")
    
    def _update_regime(self):
        """Update market regime randomly"""
        if np.random.random() < self.regime_change_probability:
            regimes = ['normal', 'bull', 'bear', 'sideways', 'volatile']
            self.regime = np.random.choice(regimes)
            self.logger.warning(f"⚡ Market regime changed to: {self.regime.upper()}")
    
    def _calculate_market_dynamics(self) -> Dict[str, float]:
        """Calculate market movement based on regime"""
        regime_params = {
            'normal': {'drift': 0.0001, 'vol_mult': 1.0, 'trend': 0.0},
            'bull': {'drift': 0.0005, 'vol_mult': 0.8, 'trend': 0.3},
            'bear': {'drift': -0.0005, 'vol_mult': 1.2, 'trend': -0.3},
            'sideways': {'drift': 0.0, 'vol_mult': 0.5, 'trend': 0.0},
            'volatile': {'drift': 0.0, 'vol_mult': 2.0, 'trend': np.random.uniform(-0.5, 0.5)}
        }
        
        return regime_params.get(self.regime, regime_params['normal'])
    
    def step(self, agent_action: str = 'HOLD') -> MarketState:
        """
        Advance market one time step
        Args:
            agent_action: Action taken by trading agent (BUY/SELL/HOLD)
        Returns:
            New market state
        """
        # Update regime
        self._update_regime()
        
        # Get market dynamics
        dynamics = self._calculate_market_dynamics()
        
        # Generate price movement
        drift = dynamics['drift']
        vol = self.volatility * dynamics['vol_mult']
        
        # Geometric Brownian Motion
        random_shock = np.random.normal(0, vol)
        price_change_pct = drift + random_shock
        
        # Agent feedback (simple impact model)
        if agent_action == 'BUY':
            # Buying pressure increases price slightly
            price_change_pct += 0.0005
            # Decreases liquidity
            self.liquidity = max(0.1, self.liquidity - 0.05)
        elif agent_action == 'SELL':
            # Selling pressure decreases price
            price_change_pct -= 0.0005
            # Decreases liquidity
            self.liquidity = max(0.1, self.liquidity - 0.05)
        else:
            # Liquidity recovers when no action
            self.liquidity = min(1.0, self.liquidity + 0.02)
        
        # Update price
        self.price = max(0.01, self.price * (1 + price_change_pct))
        
        # Update trend
        self.trend_strength = dynamics['trend'] + np.random.normal(0, 0.05)
        self.trend_strength = np.clip(self.trend_strength, -1, 1)
        
        # Generate realistic volume
        volume = np.random.lognormal(mean=np.log(1000000), sigma=0.5)
        volume *= (1 + abs(self.trend_strength))  # Higher volume in trending markets
        
        # Update time
        self.time += timedelta(minutes=5)  # 5-minute candles
        
        # Create state
        state = MarketState(
            timestamp=self.time,
            price=self.price,
            volume=volume,
            volatility=vol,
            trend=self.trend_strength,
            liquidity=self.liquidity
        )
        
        # History
        self.price_history.append(self.price)
        self.volume_history.append(volume)
        self.state_history.append(state)
        
        return state
    
    def run_simulation(self, num_steps: int = 1000) -> List[MarketState]:
        """Run complete market simulation"""
        self.logger.info(f"🎬 Running market simulation for {num_steps} steps...")
        
        states = []
        for i in range(num_steps):
            state = self.step()
            states.append(state)
            
            if i % 100 == 0:
                self.logger.info(f"   Step {i}/{num_steps}: Price=${state.price:.2f}, Trend={state.trend:.2f}")
        
        self.logger.info(f"✅ Simulation complete")
        return states
    
    def get_market_features(self, lookback: int = 20) -> np.ndarray:
        """
        Get market features for ML model
        Returns state vector for agent input
        """
        if len(self.state_history) < lookback:
            return None
        
        recent_states = self.state_history[-lookback:]
        
        # Calculate technical indicators
        prices = np.array([s.price for s in recent_states])
        volumes = np.array([s.volume for s in recent_states])
        
        # Features: [price, MA5, MA20, volatility, trend, volume, liquidity, momentum]
        ma5 = np.mean(prices[-5:])
        ma20 = np.mean(prices) if len(prices) == lookback else np.mean(prices[:20])
        volatility = np.std(np.diff(prices) / prices[:-1])
        trend = recent_states[-1].trend
        volume = recent_states[-1].volume
        liquidity = recent_states[-1].liquidity
        momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        
        features = np.array([
            prices[-1],
            ma5,
            ma20,
            volatility,
            trend,
            volume / 1000000,  # Normalize
            liquidity,
            momentum
        ])
        
        return features
    
    def get_statistics(self) -> Dict[str, float]:
        """Get simulation statistics"""
        prices = np.array(self.price_history)
        returns = np.diff(prices) / prices[:-1]
        
        return {
            'start_price': self.price_history[0],
            'end_price': self.price_history[-1],
            'max_price': float(np.max(prices)),
            'min_price': float(np.min(prices)),
            'total_return': float((prices[-1] - prices[0]) / prices[0]),
            'daily_volatility': float(np.std(returns)),
            'sharpe_ratio': float(np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)),
            'num_steps': len(prices)
        }


class SimulatedTradingEnvironment:
    """Environment for agent training on simulated market"""
    
    def __init__(self, initial_capital: float = 100000):
        """Initialize environment"""
        self.simulator = AIMarketSimulator(initial_price=100.0)
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # Number of shares
        self.entry_price = 0
        self.pnl = 0
        
        self.trades = []
        self.logger = logging.getLogger("SimulatedEnvironment")
    
    def reset(self) -> Dict[str, Any]:
        """Reset environment"""
        self.simulator = AIMarketSimulator()
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.pnl = 0
        self.trades = []
        
        return {'state': self.simulator.get_market_features()}
    
    def step(self, action: str) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Execute action and return new state + reward
        Args:
            action: BUY, SELL, or HOLD
        Returns:
            (state, reward, done, info)
        """
        # Advance market
        market_state = self.simulator.step(agent_action=action)
        
        # Execute action
        current_price = market_state.price
        reward = 0
        
        if action == 'BUY' and self.position == 0:
            # Buy signal
            shares = (self.capital * 0.95) / current_price
            self.position = shares
            self.entry_price = current_price
            self.capital *= 0.05  # Keep cash
            
            self.logger.info(f"🟢 BUY: {shares:.2f} shares @ ${current_price:.2f}")
        
        elif action == 'SELL' and self.position > 0:
            # Sell signal
            sale_value = self.position * current_price
            self.capital += sale_value
            
            trade_pnl = sale_value - (self.position * self.entry_price)
            reward = trade_pnl / self.entry_price
            
            self.trades.append({
                'entry': self.entry_price,
                'exit': current_price,
                'shares': self.position,
                'pnl': trade_pnl
            })
            
            self.logger.info(f"🔴 SELL: {self.position:.2f} shares @ ${current_price:.2f}, PnL: ${trade_pnl:.2f}")
            
            self.position = 0
        
        # Update portfolio value
        portfolio_value = self.capital + (self.position * current_price)
        self.pnl = portfolio_value - self.initial_capital
        
        # Check if done
        done = len(self.simulator.state_history) >= 1000
        
        return (
            {'state': self.simulator.get_market_features()},
            reward,
            done,
            {
                'portfolio_value': portfolio_value,
                'pnl': self.pnl,
                'position': self.position,
                'price': current_price
            }
        )


# Demo: Train agent on simulated market
async def demo_market_simulator():
    """Demo market simulator and training"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Demo")
    
    logger.info("\n" + "🎯 "*30)
    logger.info("🎯 DEMO: AI Market Simulator V7.5")
    logger.info("🎯 "*30 + "\n")
    
    # Create simulator
    simulator = AIMarketSimulator(initial_price=100.0)
    
    # Run simulation
    logger.info("📊 Running 500-step market simulation...")
    states = simulator.run_simulation(num_steps=500)
    
    # Get statistics
    stats = simulator.get_statistics()
    logger.info(f"\n📈 Simulation Statistics:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value:.4f}")
    
    # Create trading environment
    logger.info(f"\n🎮 Testing trading environment...")
    env = SimulatedTradingEnvironment(initial_capital=100000)
    state = env.reset()
    
    # Simulate agent trading
    for i in range(100):
        action = np.random.choice(['BUY', 'SELL', 'HOLD'])
        next_state, reward, done, info = env.step(action)
        
        if i % 20 == 0:
            logger.info(f"   Step {i}: Action={action}, PnL=${info['pnl']:.2f}, Portfolio=${info['portfolio_value']:.2f}")
        
        if done:
            break
    
    logger.info(f"\n✅ Training simulation complete")


if __name__ == '__main__':
    import asyncio
    asyncio.run(demo_market_simulator())
