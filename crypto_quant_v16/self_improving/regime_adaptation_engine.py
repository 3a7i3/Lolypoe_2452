class RegimeAdaptationEngine:
    def __init__(self):
        self.market_regimes = {}

    def detect_regime(self, market_data):
        if market_data['return'] > 0:
            regime = "bull"
        else:
            regime = "bear"
        self.market_regimes = {"current": regime}
        return regime
