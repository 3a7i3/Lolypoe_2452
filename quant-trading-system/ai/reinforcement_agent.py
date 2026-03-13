"""
Reinforcement Learning Agent - Q-Learning based trading agent
"""

import logging
from typing import Dict, Tuple
import numpy as np
import config

logger = logging.getLogger(__name__)

class ReinforcementAgent:
    """Q-Learning based reinforcement learning agent"""
    
    def __init__(self, state_size: int = 10, action_size: int = 3):
        self.state_size = state_size
        self.action_size = action_size  # BUY, HOLD, SELL
        self.q_table = {}
        self.epsilon = 1.0
        self.gamma = config.RL_GAMMA
        self.epsilon_decay = config.RL_EPSILON_DECAY
        self.learning_rate = 0.1
        logger.info("✓ Reinforcement Agent initialized")
    
    def get_action(self, state: Tuple) -> int:
        """
        Get action using epsilon-greedy policy
        Returns: action (0=BUY, 1=HOLD, 2=SELL)
        """
        try:
            # Epsilon-greedy exploration
            if np.random.random() < self.epsilon:
                return np.random.choice([0, 1, 2])
            
            # Exploit best action
            state_key = str(state)
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(self.action_size)
            
            return np.argmax(self.q_table[state_key])
            
        except Exception as e:
            logger.error(f"Action selection error: {e}")
            return 1  # Default to HOLD
    
    def learn(self, state: Tuple, action: int, reward: float, next_state: Tuple, done: bool):
        """
        Learn from experience
        """
        try:
            state_key = str(state)
            next_state_key = str(next_state)
            
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(self.action_size)
            if next_state_key not in self.q_table:
                self.q_table[next_state_key] = np.zeros(self.action_size)
            
            # Q-Learning update
            current_q = self.q_table[state_key][action]
            max_next_q = np.max(self.q_table[next_state_key])
            
            new_q = current_q + self.learning_rate * (reward + self.gamma * max_next_q - current_q)
            self.q_table[state_key][action] = new_q
            
            # Decay epsilon
            if done:
                self.epsilon = max(0.01, self.epsilon * self.epsilon_decay)
            
        except Exception as e:
            logger.error(f"Learning error: {e}")
    
    def get_state(self, market_data: Dict) -> Tuple:
        """
        Convert market data to state representation
        Returns: state tuple
        """
        try:
            # Simplified state: (price_trend, volume_trend, volatility)
            price = market_data.get('price', 0)
            volume = market_data.get('volume', 0)
            change = market_data.get('change', 0)
            
            # Discretize
            price_trend = 0 if change < -0.01 else (1 if change > 0.01 else 0)
            volume_trend = 0 if volume < 1000 else 1
            volatility = 0 if abs(change) < 0.01 else 1
            
            return (price_trend, volume_trend, volatility)
            
        except Exception as e:
            logger.error(f"State creation error: {e}")
            return (0, 0, 0)
    
    def get_reward(self, position_pnl: float, action: int) -> float:
        """
        Calculate reward for action
        Returns: reward value
        """
        try:
            if action == 0:  # BUY
                return max(position_pnl, -1.0)
            elif action == 1:  # HOLD
                return position_pnl / 2
            else:  # SELL
                return position_pnl
            
        except Exception as e:
            logger.error(f"Reward calculation error: {e}")
            return 0.0
    
    def reset(self):
        """Reset agent state"""
        self.epsilon = 1.0
        self.q_table.clear()
        logger.info("Agent reset")
