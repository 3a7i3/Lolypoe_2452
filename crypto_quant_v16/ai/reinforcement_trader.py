"""
Reinforcement Learning Trader Agent – Learns optimal trading actions
Agent that learns to trade through simulated experience
"""

import random
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class RLTrader:
    """Reinforcement Learning agent for trading"""

    def __init__(self, name: str = "RLTrader", learning_rate: float = 0.1, 
                 discount_factor: float = 0.95):
        """Initialize RL agent"""
        self.name = name
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table = {}
        self.actions = ["BUY", "SELL", "HOLD"]
        self.epsilon = 0.3  # Exploration rate
        self.trades = []

    def state_encoding(self, rsi: float, macd: float, trend: float) -> tuple:
        """Encode market state as tuple"""
        rsi_bin = "HIGH" if rsi > 70 else ("LOW" if rsi < 30 else "NEUTRAL")
        macd_bin = "POSITIVE" if macd > 0 else "NEGATIVE"
        trend_bin = "UP" if trend > 0 else "DOWN"
        
        return (rsi_bin, macd_bin, trend_bin)

    def choose_action(self, state: tuple) -> str:
        """Choose action using epsilon-greedy"""
        if random.random() < self.epsilon:
            # Explore
            action = random.choice(self.actions)
        else:
            # Exploit
            if state not in self.q_table:
                self.q_table[state] = {a: 0 for a in self.actions}
            
            action = max(self.q_table[state], 
                        key=self.q_table[state].get)
        
        return action

    def learn(self, state: tuple, action: str, reward: float, next_state: tuple):
        """Update Q-table (Q-learning)"""
        if state not in self.q_table:
            self.q_table[state] = {a: 0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0 for a in self.actions}
        
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state].values())
        
        new_value = old_value + self.learning_rate * (
            reward + self.discount_factor * next_max - old_value
        )
        
        self.q_table[state][action] = new_value

    async def act(self, market_state: Dict) -> str:
        """Make trading decision"""
        state = self.state_encoding(
            market_state.get('rsi', 50),
            market_state.get('macd', 0),
            market_state.get('trend', 0)
        )
        
        action = self.choose_action(state)
        logger.debug(f"🤖 {self.name} action: {action} (state: {state})")
        
        return action

    def execute_trade(self, action: str, symbol: str, 
                     current_price: float, quantity: float = 1.0) -> Dict:
        """Execute trade based on action"""
        trade = {
            'symbol': symbol,
            'action': action,
            'price': current_price,
            'quantity': quantity,
            'pnl': 0,
            'timestamp': pd.Timestamp.now()
        }
        
        self.trades.append(trade)
        logger.info(f"🤖 Trade executed: {action} {quantity} {symbol} @ {current_price}")
        
        return trade

    def get_performance(self) -> Dict[str, Any]:
        """Calculate RL agent performance metrics"""
        if not self.trades:
            return {'total_trades': 0, 'win_rate': 0}
        
        winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
        total_trades = len(self.trades)
        
        return {
            'total_trades': total_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_pnl': sum(t['pnl'] for t in self.trades),
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table)
        }
