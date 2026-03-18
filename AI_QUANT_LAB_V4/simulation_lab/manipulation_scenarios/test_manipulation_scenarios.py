

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Permet l'import du dossier parent (synthetic_market)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synthetic_market')))
from whale_manipulation import WhaleManipulation

def main():
	prices = [100 + np.random.normal(0, 1) for _ in range(300)]
	df = pd.DataFrame({"close": prices})
	sim = WhaleManipulation()
	df_manip = sim.pump_dump(df.copy())
	plt.figure(figsize=(10,4))
	plt.plot(df["close"], label="Original")
	plt.plot(df_manip["close"], label="Avec Manipulation")
	plt.title("Whale Manipulation Simulator Test")
	plt.legend()
	plt.tight_layout()
	plt.savefig("manipulation_scenarios_test.png", dpi=120)
	print("Image sauvegardée sous manipulation_scenarios_test.png")

if __name__ == "__main__":
	main()

if __name__ == "__main__":
	main()	