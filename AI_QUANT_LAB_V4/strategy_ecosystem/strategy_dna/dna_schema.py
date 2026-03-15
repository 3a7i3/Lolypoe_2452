from dataclasses import dataclass

@dataclass
class StrategyDNA:
    signal: str
    filter: str
    risk_model: str
    position_model: str
    timeframe: str
    parameters: dict
