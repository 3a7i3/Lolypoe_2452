import pandas as pd
import matplotlib.pyplot as plt
import glob

def load_latest_equity_csv():
    files = glob.glob("results/equity_curves_gen_*.csv")
    if not files:
        raise FileNotFoundError("Aucun CSV d'equity curves trouvé.")
    files.sort()
    return files[-1]

csv_path = load_latest_equity_csv()
df = pd.read_csv(csv_path)

# Visualisation : equity curves pour chaque marché
markets = df['market'].unique()
plt.figure(figsize=(14, 8))
for market in markets:
    market_df = df[df['market'] == market]
    # Affiche la courbe du meilleur génome (fitness max)
    best_id = market_df.groupby('id')['fitness'].mean().idxmax()
    best_curve = market_df[market_df['id'] == best_id]
    plt.plot(best_curve['step'], best_curve['capital'], label=f"{market} (best)")
plt.xlabel('Step')
plt.ylabel('Capital')
plt.title('Equity curves des meilleurs génomes par marché')
plt.legend()
plt.tight_layout()
plt.show()

# Visualisation : overlay de plusieurs génomes sur un marché
plt.figure(figsize=(14, 8))
for market in markets:
    market_df = df[df['market'] == market]
    # Prend les 3 meilleurs génomes
    top_ids = market_df.groupby('id')['fitness'].mean().nlargest(3).index
    for idx in top_ids:
        curve = market_df[market_df['id'] == idx]
        plt.plot(curve['step'], curve['capital'], label=f"{market} id={idx[:6]}")
plt.xlabel('Step')
plt.ylabel('Capital')
plt.title('Equity curves overlay (top 3 par marché)')
plt.legend()
plt.tight_layout()
plt.show()
