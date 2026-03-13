"""
Reinforcement Agent - Q-Learning agent pour trading
"""

import numpy as np
from config import RL_EPSILON, RL_GAMMA, RL_LR
from utils.logger import logger

class RLAgent:
    """Q-Learning agent pour optimiser les trades."""
    
    def __init__(self, state_size=10, action_size=3):
        """
        action_size: 0=HOLD, 1=BUY, 2=SELL
        """
        self.state_size = state_size
        self.action_size = action_size
        
        # Q-table
        self.q_table = np.zeros((state_size, action_size))
        
        # Parametres
        self.epsilon = RL_EPSILON
        self.gamma = RL_GAMMA
        self.learning_rate = RL_LR
        
        self.episode_num = 0
    
    def get_action(self, state):
        """Retourne une action basee sur l'etat."""
        if np.random.random() < self.epsilon:
            return np.random.choice(self.action_size)  # Exploration
        else:
            return np.argmax(self.q_table[state])  # Exploitation
    
    def remember(self, state, action, reward, next_state, done):
        """Stocke l'experience."""
        target = reward
        if not done:
            target = reward + self.gamma * np.max(self.q_table[next_state])
        
        # Update Q-value
        self.q_table[state, action] += self.learning_rate * (target - self.q_table[state, action])
    
    def train(self, experiences):
        """Entraine l'agent."""
        for state, action, reward, next_state, done in experiences:
            self.remember(state, action, reward, next_state, done)
    
    def decay_epsilon(self):
        """Reduit epsilon pour moins d'exploration."""
        self.epsilon *= 0.9995
        self.episode_num += 1
    
    def get_strategy(self, states):
        """Retourne les actions pour une sequence d'etats."""
        actions = []
        for state in states:
            action = np.argmax(self.q_table[state])
            actions.append(action)
        return actions
