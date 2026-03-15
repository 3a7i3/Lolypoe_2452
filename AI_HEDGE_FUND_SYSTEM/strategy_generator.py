import pandas as pd
from AI_HEDGE_FUND_SYSTEM.alpha_mining.alpha_cluster import AlphaCluster
from AI_HEDGE_FUND_SYSTEM.alpha_mining.alpha_ranker import AlphaRanker
from AI_HEDGE_FUND_SYSTEM.alpha_discovery.alpha_backtester import AlphaBacktester

class StrategyGenerator:
    def __init__(self, min_score=0.05, max_strat=5):
        self.min_score = min_score
        self.max_strat = max_strat

    def generate(self, features, returns, df):
        """
        Génère automatiquement des stratégies à partir des features/mined signals.
        - features: dict ou DataFrame de features
        - returns: Series des rendements futurs
        - df: DataFrame de prix (pour le backtest)
        Retourne une liste de stratégies (dict: nom, signal, stats, equity)
        """
        cluster = AlphaCluster()
        mining_results = cluster.mine(features, returns)
        ranked = AlphaRanker().rank(mining_results)
        strategies = []
        for name, score in ranked:
            if abs(score) < self.min_score:
                continue
            signal = features[name] if isinstance(features, dict) else features[name]
            backtester = AlphaBacktester()
            bt_df, stats = backtester.run(df, signal)
            strategies.append({
                "name": name,
                "score": score,
                "signal": signal,
                "stats": stats,
                "equity": bt_df["equity"]
            })
            if len(strategies) >= self.max_strat:
                break
        return strategies
