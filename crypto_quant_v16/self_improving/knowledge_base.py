class KnowledgeBase:
    def __init__(self):
        self.alpha_database = []
        self.feature_database = []
        self.strategy_database = []
        self.performance_history = []  # ✅ Historique complet
    def log_performance(self, strategy, score, allocation, pnl):
        import time
        self.performance_history.append({
            "strategy": strategy["name"],
            "score": score,
            "allocation": allocation,
            "pnl": pnl,
            "timestamp": time.time()
        })

    def store_strategy(self, strategy):
        self.strategy_database.append(strategy)

    def store_alpha(self, alpha):
        self.alpha_database.append(alpha)

    def store_feature(self, feature):
        self.feature_database.append(feature)
