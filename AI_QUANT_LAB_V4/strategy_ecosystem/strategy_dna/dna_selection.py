import random

def score_dna(dna):
    # Exemple de scoring fictif basé sur les attributs
    score = 0
    if dna.signal == "momentum":
        score += 1
    if dna.filter == "volatility_low":
        score += 0.5
    if dna.risk_model == "fixed_risk":
        score += 0.3
    if dna.position_model == "risk_parity":
        score += 0.7
    if dna.timeframe == "1h":
        score += 0.2
    # Ajoute un bruit aléatoire pour simuler la variance du marché
    score += random.uniform(-0.2, 0.2)
    return score

def select_best(population, top_n=2):
    # Trie la population selon le score décroissant
    scored = [(dna, score_dna(dna)) for dna in population]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [dna for dna, score in scored[:top_n]]
