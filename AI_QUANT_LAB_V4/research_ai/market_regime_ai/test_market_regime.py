import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from regime_detector import MarketRegimeDetector
from regime_memory import RegimeMemory
from regime_router import RegimeRouter

# Génère un DataFrame de test (simule un bull market)
dates = pd.date_range(start="2024-01-01", periods=300, freq="h")
prices = np.cumsum(np.random.normal(0.05, 0.5, size=300)) + 100  # tendance haussière
volumes = np.random.randint(1000, 2000, size=300)
df = pd.DataFrame({"close": prices, "volume": volumes}, index=dates)

# Détection du régime
regime_detector = MarketRegimeDetector()
regime = regime_detector.detect(df)
print("Régime détecté:", regime)

# Mémoire des régimes
memory = RegimeMemory()
memory.record(regime)
print("Dernier régime enregistré:", memory.last())

# Routing des stratégies
router = RegimeRouter()
strategies = router.strategies_for(regime)
print("Stratégies activées:", strategies)
