"""
Détecteur de manipulation de marché : whales, pump & dump, liquidity traps.
"""


class MarketManipulationDetector:
    def __init__(self):
        self.alerts = []

    def detect_whale_activity(self, trades, threshold=100000):
        # Détecte les grosses transactions (whales)
        whales = [t for t in trades if abs(t.get('size', 0)) > threshold]
        if whales:
            for w in whales:
                self.alerts.append(f"Whale activity: size={w.get('size', 0)}")
        return whales

    def detect_pump_and_dump(self, prices, pct_threshold=0.5):
        # Détecte un pump & dump par variation rapide (ex: +X% puis -X%)
        if len(prices) < 3:
            return False
        up = (prices[-2] - prices[-3]) / max(1e-8, abs(prices[-3]))
        down = (prices[-1] - prices[-2]) / max(1e-8, abs(prices[-2]))
        if up > pct_threshold and down < -pct_threshold:
            self.alerts.append(f"Pump & dump detected: +{up*100:.1f}% / {down*100:.1f}%")
            return True
        return False

    def detect_liquidity_trap(self, orderbook, spread_threshold=5, depth_threshold=10000):
        # Détecte un piège de liquidité (spread large + faible profondeur)
        spread = orderbook.get('spread', 0)
        depth = orderbook.get('depth', 1e9)
        if spread > spread_threshold and depth < depth_threshold:
            self.alerts.append(f"Liquidity trap: spread={spread}, depth={depth}")
            return True
        return False

# Tests avancés du module
def test_market_manipulation_detector():
    detector = MarketManipulationDetector()
    # Cas 1 : whale simple
    trades = [{'size': 50000}, {'size': 200000}, {'size': 150000}]
    whales = detector.detect_whale_activity(trades)
    assert len(whales) == 2
    # Cas 2 : pump & dump classique
    prices = [100, 160, 70]
    pump = detector.detect_pump_and_dump(prices, pct_threshold=0.5)
    assert pump is True
    # Cas 3 : pas de pump & dump
    prices2 = [100, 120, 119]
    pump2 = detector.detect_pump_and_dump(prices2, pct_threshold=0.5)
    assert pump2 is False
    # Cas 4 : liquidity trap
    orderbook = {'spread': 10, 'depth': 5000}
    trap = detector.detect_liquidity_trap(orderbook, spread_threshold=5, depth_threshold=10000)
    assert trap is True
    # Cas 5 : pas de trap
    orderbook2 = {'spread': 2, 'depth': 20000}
    trap2 = detector.detect_liquidity_trap(orderbook2, spread_threshold=5, depth_threshold=10000)
    assert trap2 is False
    # Cas 6 : robustesse entrées vides
    assert detector.detect_whale_activity([]) == []
    assert detector.detect_pump_and_dump([1, 1, 1]) is False
    assert detector.detect_liquidity_trap({}) is False
    print('All advanced tests passed.')
    print('Alerts:', detector.alerts)

if __name__ == '__main__':
    test_market_manipulation_detector()
