
from scenario_runner import ScenarioRunner
import matplotlib.pyplot as plt

# Génère un marché synthétique bull avec manipulations, crises et crash
runner = ScenarioRunner()
df = runner.run(regime="bull", with_crash=True)

print(df.head())
print("\nDernier prix:", df['close'].iloc[-1])

# Visualisation de la série de prix (batch mode)
plt.figure(figsize=(12,4))
plt.plot(df['close'])
plt.title('Synthetic Bull Market with Whale, Liquidity Events & Crash')
plt.xlabel('Time')
plt.ylabel('Price')
plt.tight_layout()
plt.savefig('synthetic_market_bull.png', dpi=120)
print("Image sauvegardée sous synthetic_market_bull.png")
