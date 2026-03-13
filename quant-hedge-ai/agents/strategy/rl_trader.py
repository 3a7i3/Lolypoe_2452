from __future__ import annotations

import random


class RLTrader:
    """Minimal epsilon-greedy Q-learner for paper trading decisions."""

    def __init__(self, epsilon: float = 0.1, alpha: float = 0.2, gamma: float = 0.95) -> None:
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.q_table: dict[tuple[str, str], float] = {}
        self.actions = ["BUY", "SELL", "HOLD"]

    def choose_action(self, state: str) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        values = {a: self.q_table.get((state, a), 0.0) for a in self.actions}
        return max(values, key=lambda a: values[a])

    def update(self, state: str, action: str, reward: float, next_state: str) -> None:
        current = self.q_table.get((state, action), 0.0)
        max_next = max(self.q_table.get((next_state, a), 0.0) for a in self.actions)
        new_value = current + self.alpha * (reward + self.gamma * max_next - current)
        self.q_table[(state, action)] = new_value
