def decode_dna(dna):
    strategy = {
        "signal": dna.signal,
        "filter": dna.filter,
        "risk_model": dna.risk_model,
        "position_model": dna.position_model,
        "timeframe": dna.timeframe
    }
    return strategy
