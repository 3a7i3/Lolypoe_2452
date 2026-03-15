class MarketAnalystAI:
    """Analyse les marchés (volatilité, trend, volume, etc.)."""
    def analyze(self, market_data):
        report = {}
        report["volatility"] = market_data["close"].pct_change().std()
        report["trend"] = (
            market_data["close"].rolling(50).mean().iloc[-1]
            - market_data["close"].rolling(200).mean().iloc[-1]
        )
        # Ajoute d'autres analyses ici
        return report
