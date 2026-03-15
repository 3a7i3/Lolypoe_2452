import random
from dna_schema import StrategyDNA

def crossover(dna1, dna2):
    return StrategyDNA(
        signal=random.choice([dna1.signal, dna2.signal]),
        filter=random.choice([dna1.filter, dna2.filter]),
        risk_model=random.choice([dna1.risk_model, dna2.risk_model]),
        position_model=random.choice([dna1.position_model, dna2.position_model]),
        timeframe=random.choice([dna1.timeframe, dna2.timeframe]),
        parameters={}
    )
