

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Permet l'import du dossier parent (synthetic_market)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synthetic_market')))
from crash_simulator import CrashSimulator

def main():
	# Génère une série de prix simple
	prices = [100 + np.random.normal(0, 1) for _ in range(300)]
	df = pd.DataFrame({"close": prices})
	sim = CrashSimulator()
	df_crash = sim.inject_crash(df.copy(), magnitude=0.4)
	plt.figure(figsize=(10,4))
	plt.plot(df["close"], label="Original")
	plt.plot(df_crash["close"], label="Avec Crash")
	plt.title("Crash Simulator Test")
	plt.legend()
	plt.tight_layout()
	plt.savefig("crash_simulator_test.png", dpi=120)
	print("Image sauvegardée sous crash_simulator_test.png")

if __name__ == "__main__":
	main()

if __name__ == "__main__":
	main()
