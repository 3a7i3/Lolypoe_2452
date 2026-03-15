class HypothesisGenerator:
    def __init__(self, patterns):
        self.patterns = patterns

    def generate(self):
        hypotheses = []
        # Volume breakout
        if self.patterns.get("volume_spike"):
            hypotheses.append(("volume_breakout_strategy", 0.8))
        # Volatility expansion
        if self.patterns.get("volatility_cluster", 0) > 0.05:
            hypotheses.append(("volatility_expansion_strategy", 0.7))
        # Liquidation cluster
        if self.patterns.get("liquidation_cluster"):
            hypotheses.append(("liquidation_squeeze_strategy", 0.9))
        # Whale activity
        if self.patterns.get("whale_activity"):
            hypotheses.append(("whale_following_strategy", 0.85))
        # Regime shift
        if self.patterns.get("regime_shift"):
            hypotheses.append(("regime_shift_strategy", 0.75))
        # Anomaly
        if self.patterns.get("anomaly"):
            hypotheses.append(("anomaly_reversal_strategy", 0.6))
        # Prioritisation par score
        hypotheses.sort(key=lambda x: x[1], reverse=True)
        # On ne garde que le nom pour la suite
        return [h[0] for h in hypotheses]
