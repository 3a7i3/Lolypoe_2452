"""
Reinforcement Learning Agent
DQN-based trading agent for continuous strategy optimization
"""

import numpy as np
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from collections import deque
import random


@dataclass
class Experience:
    """Single experience for replay buffer"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class RLTradingAgent:
    """Reinforcement Learning trading agent using DQN"""
    
    # Action space
    ACTIONS = {
        0: 'HOLD',
        1: 'BUY',
        2: 'SELL'
    }
    
    def __init__(self, state_size: int = 10, learning_rate: float = 0.001, 
                 gamma: float = 0.95, epsilon: float = 1.0):
        """
        Initialize RL agent
        Args:
            state_size: Number of state features
            learning_rate: Learning rate for Q-learning
            gamma: Discount factor for future rewards
            epsilon: Exploration rate
        """
        self.state_size = state_size
        self.action_size = len(self.ACTIONS)
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        
        # Q-table (simple implementation, replace with neural network for production)
        self.q_table = {}
        
        # Replay buffer
        self.replay_buffer = deque(maxlen=1000)
        
        # Training history
        self.episode_rewards = []
        self.episode_actions = []
    
    def get_state_key(self, state: np.ndarray) -> str:
        """Convert state to hashable key for Q-table"""
        return tuple(np.round(state, 2))
    
    def choose_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Choose action using epsilon-greedy policy
        Args:
            state: Current market state
            training: Whether in training mode (exploration)
        Returns:
            Action index (0=HOLD, 1=BUY, 2=SELL)
        """
        state_key = self.get_state_key(state)
        
        if training and random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, self.action_size - 1)
        else:
            # Exploit: best known action
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(self.action_size)
            
            q_values = self.q_table[state_key]
            return np.argmax(q_values)
    
    def remember(self, state: np.ndarray, action: int, reward: float,
                next_state: np.ndarray, done: bool):
        """Store experience in replay buffer"""
        self.replay_buffer.append(Experience(state, action, reward, next_state, done))
    
    def replay(self, batch_size: int = 32):
        """Train on mini-batch from replay buffer"""
        if len(self.replay_buffer) < batch_size:
            return
        
        # Sample batch
        batch = random.sample(self.replay_buffer, batch_size)
        
        # Train
        for experience in batch:
            state_key = self.get_state_key(experience.state)
            next_state_key = self.get_state_key(experience.next_state)
            
            # Initialize Q-values if not seen before
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(self.action_size)
            if next_state_key not in self.q_table:
                self.q_table[next_state_key] = np.zeros(self.action_size)
            
            # Q-learning update
            target = experience.reward
            if not experience.done:
                target += self.gamma * np.max(self.q_table[next_state_key])
            
            # Update Q-value
            old_q = self.q_table[state_key][experience.action]
            self.q_table[state_key][experience.action] = \
                old_q + self.learning_rate * (target - old_q)
        
        # Decay exploration rate
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def train_episode(self, states: List[np.ndarray], rewards: List[float],
                     batch_size: int = 32) -> float:
        """
        Train agent for one episode
        Args:
            states: List of states in episode
            rewards: List of rewards in episode
            batch_size: Mini-batch size for replay
        Returns:
            Total episode reward
        """
        total_reward = 0
        self.episode_actions = []
        
        for i in range(len(states) - 1):
            state = states[i]
            next_state = states[i + 1]
            reward = rewards[i]
            done = (i == len(states) - 2)
            
            # Choose action
            action = self.choose_action(state, training=True)
            self.episode_actions.append(self.ACTIONS[action])
            
            # Remember experience
            self.remember(state, action, reward, next_state, done)
            
            total_reward += reward
        
        # Train on batch
        self.replay(batch_size)
        
        # Store episode reward
        self.episode_rewards.append(total_reward)
        
        return total_reward
    
    def get_q_values(self, state: np.ndarray) -> Dict[str, float]:
        """Get Q-values for all actions"""
        state_key = self.get_state_key(state)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_size)
        
        q_values = self.q_table[state_key]
        
        return {
            self.ACTIONS[i]: float(q_values[i])
            for i in range(self.action_size)
        }
    
    def calculate_sharpe_reward(self, returns: List[float], rf_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio reward"""
        if len(returns) < 2:
            return 0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - rf_rate / 252
        
        if np.std(excess_returns) == 0:
            return 0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        # Cap Sharpe to prevent extreme values
        return np.clip(sharpe, -5, 5)
    
    def calculate_win_rate_reward(self, returns: List[float]) -> float:
        """Calculate win rate reward"""
        if len(returns) == 0:
            return 0
        
        wins = sum(1 for r in returns if r > 0)
        return (wins / len(returns)) if len(returns) > 0 else 0
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        if not self.episode_rewards:
            return {}
        
        rewards = np.array(self.episode_rewards)
        
        return {
            'episodes': len(self.episode_rewards),
            'avg_reward': float(np.mean(rewards)),
            'max_reward': float(np.max(rewards)),
            'min_reward': float(np.min(rewards)),
            'std_reward': float(np.std(rewards)),
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table)
        }


# Convenience functions
_agent = RLTradingAgent()


def train_episode(states: List[np.ndarray], rewards: List[float],
                 batch_size: int = 32) -> float:
    """Train agent for one episode"""
    return _agent.train_episode(states, rewards, batch_size)


def get_action(state: np.ndarray, training: bool = False) -> str:
    """Get recommended action"""
    action_idx = _agent.choose_action(state, training)
    return _agent.ACTIONS[action_idx]


def get_agent_stats() -> Dict[str, Any]:
    """Get agent training statistics"""
    return _agent.get_training_stats()


def reset_agent():
    """Reset agent"""
    global _agent
    _agent = RLTradingAgent()
