class AlphaRanker:
    def rank(self, alpha_scores):
        ranked = sorted(
            alpha_scores.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return ranked
