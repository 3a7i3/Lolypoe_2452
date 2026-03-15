class CrashPatternAnalyzer:
    def __init__(self, df):
        self.df = df

    def detect_crash_risk(self):
        returns = self.df["close"].pct_change()
        vol = returns.rolling(10).std().iloc[-1]
        # Séquence de pré-crash : volatilité + volume + drawdown
        drawdown = (self.df["close"].cummax() - self.df["close"]) / self.df["close"].cummax()
        max_drawdown = drawdown.rolling(20).max().iloc[-1]
        # Liquidation cluster
        liq_cluster = False
        if "liquidations" in self.df.columns:
            liq_cluster = self.df["liquidations"].rolling(10).sum().iloc[-1] > self.df["liquidations"].mean() * 3
        # Whale selling
        whale_sell = False
        if "large_trades" in self.df.columns:
            whale_sell = self.df["large_trades"].iloc[-1] < 0  # Négatif = vente massive
        # Scoring de risque
        risk_score = 0
        if vol > 0.06:
            risk_score += 0.4
        if max_drawdown > 0.15:
            risk_score += 0.3
        if liq_cluster:
            risk_score += 0.2
        if whale_sell:
            risk_score += 0.1
        if risk_score >= 0.7:
            return "imminent_crash"
        elif risk_score >= 0.4:
            return "high_crash_risk"
        return "normal"
