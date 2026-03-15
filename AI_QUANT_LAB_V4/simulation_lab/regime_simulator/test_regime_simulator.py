

import os
import sys
import matplotlib.pyplot as plt

# Permet l'import du dossier parent (synthetic_market)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synthetic_market')))
from regime_simulator import RegimeSimulator
from market_generator import MarketGenerator

def main():
    regimes = ["bull", "bear", "sideways"]
    gen = MarketGenerator()
    reg = RegimeSimulator()
    plt.figure(figsize=(10,5))
    for regime in regimes:
        params = reg.get_params(regime)
        df = gen.generate_price_series(drift=params["drift"], volatility=params["volatility"])
        plt.plot(df["close"], label=regime)
    plt.title("Regime Simulator Test")
    plt.legend()
    plt.tight_layout()
    plt.savefig("regime_simulator_test.png", dpi=120)
    print("Image sauvegardée sous regime_simulator_test.png")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
