import random
from dna_schema import StrategyDNA

signals = ["momentum", "rsi_reversion", "breakout", "volatility_expansion"]
filters = ["none", "volatility_low", "volume_spike"]
risk_models = ["fixed_risk", "atr_risk", "volatility_risk"]
position_models = ["fixed_size", "risk_parity"]
timeframes = ["5m", "15m", "1h", "4h"]

def generate_random_dna():
    return StrategyDNA(
        signal=random.choice(signals),
        filter=random.choice(filters),
        risk_model=random.choice(risk_models),
        position_model=random.choice(position_models),
        timeframe=random.choice(timeframes),
        parameters={}
    )
