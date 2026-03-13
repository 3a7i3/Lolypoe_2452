"""
AI Strategy Generator
Automatically creates new trading strategies
"""

import random
from typing import Dict, List, Any
from dataclasses import dataclass


INDICATORS = [
    "SMA",
    "EMA", 
    "RSI",
    "MACD",
    "BOLLINGER",
    "ATR",
    "STOCHASTIC",
    "ADX",
    "CCI",
    "VWAP"
]

RULES = [
    "cross_above",
    "cross_below",
    "overbought",
    "oversold",
    "divergence",
    "breakout",
    "squeeze",
    "trend_confirmation",
    "mean_reversion",
    "momentum_shift"
]

PARAMETERS = {
    "SMA": {"period": [5, 10, 20, 50, 200]},
    "EMA": {"period": [5, 10, 20, 50, 200]},
    "RSI": {"period": [7, 14, 21], "threshold": [30, 40, 60, 70]},
    "MACD": {"fast": [8, 12], "slow": [17, 26], "signal": [5, 9]},
    "BOLLINGER": {"period": [10, 20, 30], "std_dev": [1, 2, 3]},
    "ATR": {"period": [7, 14, 21]},
}


@dataclass
class Strategy:
    """Strategy representation"""
    id: str
    indicators: List[str]
    rules: List[str]
    parameters: Dict[str, Any]
    entry_logic: str
    exit_logic: str
    timeframe: str
    risk_reward_ratio: float


class StrategyGenerator:
    """AI Strategy Generator"""
    
    def __init__(self):
        self.strategy_count = 0
    
    def generate_strategy(self, seed: int = None) -> Strategy:
        """Generate a random strategy"""
        if seed:
            random.seed(seed)
        
        self.strategy_count += 1
        
        # Select random indicators
        num_indicators = random.randint(2, 4)
        selected_indicators = random.sample(INDICATORS, num_indicators)
        
        # Select random rules
        num_rules = random.randint(1, 3)
        selected_rules = random.sample(RULES, num_rules)
        
        # Generate parameters
        parameters = {}
        for indicator in selected_indicators:
            if indicator in PARAMETERS:
                for param, values in PARAMETERS[indicator].items():
                    parameters[f"{indicator}_{param}"] = random.choice(values)
        
        # Generate entry and exit logic
        entry_logic = self._generate_logic(selected_indicators, "entry")
        exit_logic = self._generate_logic(selected_indicators, "exit")
        
        timeframe = random.choice(["5m", "15m", "1h", "4h", "1d"])
        risk_reward_ratio = round(random.uniform(1.5, 3.0), 2)
        
        strategy = Strategy(
            id=f"STRAT_{self.strategy_count:05d}",
            indicators=selected_indicators,
            rules=selected_rules,
            parameters=parameters,
            entry_logic=entry_logic,
            exit_logic=exit_logic,
            timeframe=timeframe,
            risk_reward_ratio=risk_reward_ratio
        )
        
        return strategy
    
    def _generate_logic(self, indicators: List[str], logic_type: str) -> str:
        """Generate entry/exit logic string"""
        if logic_type == "entry":
            return f"IF {indicators[0]} crosses above {indicators[1]} AND RSI > 30 THEN BUY"
        else:
            return f"IF {indicators[0]} crosses below {indicators[1]} OR RSI > 70 THEN SELL"
    
    def generate_population(self, size: int = 50) -> List[Strategy]:
        """Generate population of strategies"""
        return [self.generate_strategy() for _ in range(size)]


# Convenience functions
_generator = StrategyGenerator()

def generate_strategy() -> Dict[str, Any]:
    """Generate a single strategy"""
    strategy = _generator.generate_strategy()
    return {
        "id": strategy.id,
        "indicators": strategy.indicators,
        "rules": strategy.rules,
        "parameters": strategy.parameters,
        "entry_logic": strategy.entry_logic,
        "exit_logic": strategy.exit_logic,
        "timeframe": strategy.timeframe,
        "risk_reward_ratio": strategy.risk_reward_ratio
    }


def generate_population(size: int = 50) -> List[Dict[str, Any]]:
    """Generate population of strategies"""
    return [generate_strategy() for _ in range(size)]
