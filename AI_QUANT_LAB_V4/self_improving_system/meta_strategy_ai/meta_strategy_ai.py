"""
MetaStrategyAI : combine dynamiquement les meilleures stratégies du laboratoire pour créer un portefeuille optimal.
"""

class MetaStrategyAI:
    def __init__(self):
        self.selected_strategies = []
        self.weights = []

    def select_strategies(self, strategies, performances, top_n=3):
        # Sélectionne les top_n stratégies selon la performance (ex: Sharpe)
        ranked = sorted(zip(strategies, performances), key=lambda x: x[1], reverse=True)
        self.selected_strategies = [s for s, _ in ranked[:top_n]]
        return self.selected_strategies

    def allocate_weights(self, performances):
        # Pondère les stratégies proportionnellement à leur performance
        total = sum(max(0, p) for p in performances)
        if total == 0:
            self.weights = [1/len(performances)] * len(performances) if performances else []
        else:
            self.weights = [max(0, p)/total for p in performances]
        return self.weights

    def combine_portfolio(self, strategies, weights):
        # Combine les signaux/positions des stratégies selon les poids
        # Version simplifiée : retourne la liste pondérée
        return list(zip(strategies, weights))

# Test minimal du module
if __name__ == '__main__':
    meta_ai = MetaStrategyAI()
    strategies = ['A', 'B', 'C', 'D']
    performances = [1.2, 0.5, -0.2, 0.9]
    selected = meta_ai.select_strategies(strategies, performances, top_n=2)
    weights = meta_ai.allocate_weights([1.2, 0.5])
    portfolio = meta_ai.combine_portfolio(selected, weights)
    print('Selected:', selected)
    print('Weights:', weights)
    print('Portfolio:', portfolio)
