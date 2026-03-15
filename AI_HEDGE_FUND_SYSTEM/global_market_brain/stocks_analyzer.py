class StocksAnalyzer:
    def analyze(self, data):
        # Analyse les tendances actions
        if data.get('bull_market'):
            return 'bullish'
        if data.get('crash_risk'):
            return 'bearish'
        return 'neutral'
