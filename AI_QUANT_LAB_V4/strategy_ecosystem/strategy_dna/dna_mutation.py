import random

def mutate_dna(dna):
    attribute = random.choice([
        "signal",
        "filter",
        "risk_model",
        "position_model",
        "timeframe"
    ])
    mutations = {
        "signal": ["momentum", "rsi_reversion", "breakout"],
        "filter": ["none", "volatility_low", "volume_spike"],
        "risk_model": ["fixed_risk", "atr_risk"],
        "position_model": ["fixed_size", "risk_parity"],
        "timeframe": ["5m", "15m", "1h"]
    }
    setattr(dna, attribute, random.choice(mutations[attribute]))
    return dna
