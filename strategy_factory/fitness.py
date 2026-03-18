class FitnessEvaluator:
    def score(self, trades):
        pnl = sum(trades)
        wins = sum(1 for t in trades if t > 0)
        winrate = wins / len(trades) if trades else 0
        score = pnl * winrate
        return score
