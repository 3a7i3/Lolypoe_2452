"""
PortfolioAllocator stub for QUANT_CORE
"""
class PortfolioAllocator:
    def __init__(self):
        self.max_assets = 10
        self.min_weight = 0.01
        self.max_weight = 0.25

    def allocate(self, data, features):
        """Optimise l’allocation du portefeuille selon les features et contraintes."""
        # Exemple : sélection des actifs avec meilleur momentum
        momentum = features['Momentum_10'] if 'Momentum_10' in features else data['Close'].pct_change(10)
        top_assets = momentum.nlargest(self.max_assets).index if hasattr(momentum, 'nlargest') else []
        allocation = {}
        for asset in top_assets:
            allocation[asset] = min(self.max_weight, max(self.min_weight, 1.0 / self.max_assets))
        # Normalisation
        total = sum(allocation.values())
        if total > 0:
            allocation = {k: v / total for k, v in allocation.items()}
        return {"allocation": allocation}
"""
PortfolioAllocator stub for QUANT_CORE
"""
class PortfolioAllocator:
    def __init__(self):
        self.max_assets = 10
        self.min_weight = 0.01
        self.max_weight = 0.25

    def allocate(self, data, features):
        """Optimise l’allocation du portefeuille selon les features et contraintes."""
        # Exemple : sélection des actifs avec meilleur momentum
        momentum = features['Momentum_10'] if 'Momentum_10' in features else data['Close'].pct_change(10)
        top_assets = momentum.nlargest(self.max_assets).index if hasattr(momentum, 'nlargest') else []
        allocation = {}
        for asset in top_assets:
            allocation[asset] = min(self.max_weight, max(self.min_weight, 1.0 / self.max_assets))
        # Normalisation
        total = sum(allocation.values())
        if total > 0:
            allocation = {k: v / total for k, v in allocation.items()}
        return {"allocation": allocation}
