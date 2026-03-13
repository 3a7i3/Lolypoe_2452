"""
Reinforcement Learning Trading Agent - Deep Q-Network for adaptive trading strategy
Learns optimal action selection from market observations
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque
import joblib

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Sequential
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

import config

logger = logging.getLogger(__name__)

class RLTradingAgent:
    """Deep Q-Network trading agent for cryptocurrency markets"""
    
    # Trading actions
    ACTIONS = ['BUY', 'HOLD', 'SELL']
    ACTION_MAP = {'BUY': 0, 'HOLD': 1, 'SELL': 2}
    
    def __init__(self):
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available - RL agent using mock mode")
        
        self.rl_config = config.ML_MODELS.get('RL_AGENT', {})
        self.state_dim = self.rl_config.get('state_dim', 20)  # Number of market features
        self.learning_rate = self.rl_config.get('learning_rate', 0.001)
        self.gamma = self.rl_config.get('gamma', 0.99)  # Discount factor
        self.epsilon = self.rl_config.get('epsilon', 0.1)  # Exploration rate
        self.epsilon_decay = self.rl_config.get('epsilon_decay', 0.995)
        self.epsilon_min = self.rl_config.get('epsilon_min', 0.01)
        self.memory_size = self.rl_config.get('memory_size', 10000)
        self.batch_size = self.rl_config.get('batch_size', 32)
        
        # Agent components
        self.q_network = None
        self.target_network = None
        self.memory = None
        self.agents = {}  # Per-symbol agents
        self.training_stats = {}
        
        self._initialize_networks()
        logger.info(f"✓ RL Trading Agent initialized (state_dim: {self.state_dim})")
    
    def _initialize_networks(self):
        """Initialize DQN networks"""
        if TENSORFLOW_AVAILABLE:
            self.q_network = self._build_network()
            self.target_network = self._build_network()
            self._update_target_network()
        
        self.memory = deque(maxlen=self.memory_size)
    
    def _build_network(self) -> Optional:
        """Build DQN network architecture"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        try:
            model = Sequential([
                layers.Dense(128, activation='relu', input_dim=self.state_dim),
                layers.Dropout(0.2),
                layers.Dense(128, activation='relu'),
                layers.Dropout(0.2),
                layers.Dense(64, activation='relu'),
                layers.Dropout(0.2),
                layers.Dense(len(self.ACTIONS))  # Output: Q-value for each action
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=self.learning_rate),
                loss='mse'
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Network building error: {e}")
            return None
    
    def _update_target_network(self):
        """Update target network weights"""
        if TENSORFLOW_AVAILABLE and self.target_network is not None:
            self.target_network.set_weights(self.q_network.get_weights())
    
    def select_action(self, state: np.ndarray, epsilon: Optional[float] = None) -> int:
        """
        Select action using epsilon-greedy strategy
        
        Args:
            state: Current market state (state_dim features)
            epsilon: Exploration rate (uses self.epsilon if not provided)
        
        Returns:
            Action index (0=BUY, 1=HOLD, 2=SELL)
        """
        if epsilon is None:
            epsilon = self.epsilon
        
        # Exploration
        if np.random.random() < epsilon:
            return np.random.randint(0, len(self.ACTIONS))
        
        # Exploitation
        if TENSORFLOW_AVAILABLE and self.q_network is not None:
            state_tensor = tf.convert_to_tensor([state], dtype=tf.float32)
            q_values = self.q_network.predict(state_tensor, verbose=0)
            return np.argmax(q_values[0])
        else:
            # Mock action selection
            return np.random.randint(0, len(self.ACTIONS))
    
    def store_experience(self, state: np.ndarray, action: int, reward: float,
                        next_state: np.ndarray, done: bool):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def train_on_batch(self) -> Optional[float]:
        """
        Train on a batch from replay memory
        
        Returns:
            Loss value or None
        """
        if len(self.memory) < self.batch_size:
            return None
        
        if not TENSORFLOW_AVAILABLE:
            return 0.01  # Mock loss
        
        try:
            # Sample batch
            batch_indices = np.random.choice(len(self.memory), self.batch_size)
            batch = [self.memory[i] for i in batch_indices]
            
            states = np.array([exp[0] for exp in batch])
            actions = np.array([exp[1] for exp in batch])
            rewards = np.array([exp[2] for exp in batch])
            next_states = np.array([exp[3] for exp in batch])
            dones = np.array([exp[4] for exp in batch])
            
            # Predict Q-values
            target_q_values = self.q_network.predict(states, verbose=0)
            
            # Predict Q-values for next states
            next_q_values = self.target_network.predict(next_states, verbose=0)
            
            # Update Q-values with Bellman equation
            for i in range(self.batch_size):
                if dones[i]:
                    target_q_values[i][actions[i]] = rewards[i]
                else:
                    target_q_values[i][actions[i]] = (
                        rewards[i] + self.gamma * np.max(next_q_values[i])
                    )
            
            # Train
            loss = self.q_network.train_on_batch(states, target_q_values)
            
            # Decay epsilon
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            
            return loss
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            return None
    
    def train_agent(self, symbol: str, state_history: List[np.ndarray],
                   action_history: List[int], reward_history: List[float],
                   episodes: int = 100) -> Dict:
        """
        Train agent on historical data
        
        Args:
            symbol: Cryptocurrency symbol
            state_history: List of market states
            action_history: List of taken actions
            reward_history: Resulting rewards
            episodes: Number of training episodes
        
        Returns:
            Training summary dict
        """
        try:
            start_time = datetime.now()
            training_losses = []
            
            # Store experiences
            for i in range(len(state_history) - 1):
                state = state_history[i]
                action = action_history[i]
                reward = reward_history[i]
                next_state = state_history[i + 1]
                done = i == len(state_history) - 2
                
                self.store_experience(state, action, reward, next_state, done)
            
            # Train episodes
            for episode in range(episodes):
                loss = self.train_on_batch()
                if loss is not None:
                    training_losses.append(loss)
                
                # Update target network periodically
                if episode % 10 == 0:
                    self._update_target_network()
                
                if episode % 20 == 0:
                    avg_loss = np.mean(training_losses[-20:]) if training_losses else 0
                    logger.debug(f"Episode {episode}: avg_loss={avg_loss:.6f}, epsilon={self.epsilon:.3f}")
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Store stats
            self.agents[symbol] = {
                'episodes': episodes,
                'avg_loss': np.mean(training_losses) if training_losses else 0,
                'final_epsilon': self.epsilon,
                'memory_size': len(self.memory),
                'trained_at': datetime.now().isoformat()
            }
            
            logger.info(f"✓ RL Agent trained for {symbol}: "
                       f"episodes={episodes}, avg_loss={self.agents[symbol]['avg_loss']:.6f}")
            
            return {
                'success': True,
                'symbol': symbol,
                'episodes': episodes,
                'avg_loss': float(self.agents[symbol]['avg_loss']),
                'final_epsilon': self.epsilon,
                'training_time_seconds': training_time
            }
            
        except Exception as e:
            logger.error(f"RL training error for {symbol}: {e}")
            return {'success': False, 'reason': str(e)}
    
    def generate_signal(self, state: np.ndarray, symbol: str,
                       confidence_boost: float = 1.0) -> Dict:
        """
        Generate trading signal from market state
        
        Args:
            state: Current market state
            symbol: Cryptocurrency symbol
            confidence_boost: Multiplier for signal confidence
        
        Returns:
            {
                'action': str (BUY/HOLD/SELL),
                'confidence': float (0-1),
                'q_values': dict,
                'reasoning': str
            }
        """
        try:
            # Select action (no exploration - use exploitation only)
            epsilon_backup = self.epsilon
            self.epsilon = 0  # Switch to greedy
            
            action_idx = self.select_action(state)
            action = self.ACTIONS[action_idx]
            
            self.epsilon = epsilon_backup  # Restore epsilon
            
            # Get Q-values for confidence
            if TENSORFLOW_AVAILABLE and self.q_network is not None:
                state_tensor = tf.convert_to_tensor([state], dtype=tf.float32)
                q_values_raw = self.q_network.predict(state_tensor, verbose=0)[0]
            else:
                q_values_raw = np.random.randn(len(self.ACTIONS))
            
            # Normalize Q-values to confidence (0-1)
            q_values_norm = (q_values_raw - q_values_raw.min()) / (q_values_raw.max() - q_values_raw.min() + 1e-8)
            confidence = float(q_values_norm[action_idx]) * confidence_boost
            confidence = min(1.0, confidence)
            
            # Position sizing based on confidence
            if action == 'BUY':
                position_size = 0.03 + (confidence * 0.07)  # 3-10%
            elif action == 'SELL':
                position_size = 0.03 + (confidence * 0.07)
            else:  # HOLD
                position_size = 0.0
            
            return {
                'symbol': symbol,
                'action': action,
                'confidence': float(confidence),
                'position_size': float(position_size),
                'q_values': {
                    action: float(val)
                    for action, val in zip(self.ACTIONS, q_values_raw)
                },
                'reasoning': f'RL-DQN optimal action with Q-value {q_values_raw[action_idx]:.4f}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.5,
                'position_size': 0.0,
                'reasoning': f'Error: {str(e)}'
            }
    
    def save_agent(self, filepath: str) -> bool:
        """Save agent to disk"""
        try:
            if TENSORFLOW_AVAILABLE and self.q_network is not None:
                self.q_network.save(f"{filepath}_q_network.h5")
                self.target_network.save(f"{filepath}_target_network.h5")
            
            joblib.dump(self.memory, f"{filepath}_memory.pkl")
            joblib.dump(self.agents, f"{filepath}_agents.pkl")
            
            logger.info(f"RL Agent saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def load_agent(self, filepath: str) -> bool:
        """Load agent from disk"""
        try:
            if TENSORFLOW_AVAILABLE:
                self.q_network = keras.models.load_model(f"{filepath}_q_network.h5")
                self.target_network = keras.models.load_model(f"{filepath}_target_network.h5")
            
            self.memory = joblib.load(f"{filepath}_memory.pkl")
            self.agents = joblib.load(f"{filepath}_agents.pkl")
            
            logger.info(f"RL Agent loaded: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Load error: {e}")
            return False
    
    def get_agent_summary(self) -> Dict:
        """Get summary of trained agents"""
        return {
            'total_agents': len(self.agents),
            'memory_size': len(self.memory),
            'epsilon_current': float(self.epsilon),
            'agents_trained': self.agents,
            'timestamp': datetime.now().isoformat()
        }


logger.info("[RL TRADING AGENT] Deep Q-Network agent loaded")
