import streamlit as st
import pandas as pd
import glob
import matplotlib.pyplot as plt
import os
from PIL import Image

# Charger le dernier CSV d'equity curves
def load_latest_equity_csv():
    files = glob.glob("results/equity_curves_gen_*.csv")
    if not files:
        st.error("Aucun CSV d'equity curves trouvé.")
        st.stop()
    files.sort()
    return files[-1]

csv_path = load_latest_equity_csv()
df = pd.read_csv(csv_path)

# Debug : aperçu du DataFrame et des marchés/génomes
st.subheader("Debug : Aperçu du CSV chargé")
st.write(df.head(10))
st.write(f"Marchés disponibles : {sorted(df['market'].unique())}")
st.write(f"Génomes disponibles : {sorted(df['id'].unique())}")

st.title("Equity Curve Explorer (multi-marchés, multi-génomes)")

markets = sorted(df['market'].unique())
ids = sorted(df['id'].unique())

selected_markets = st.multiselect("Sélectionner les marchés:", markets, default=markets)
selected_ids = st.multiselect("Sélectionner les génomes:", ids, default=ids[:3])

if selected_markets and selected_ids:
    st.subheader("Courbes d'equity sélectionnées")
    fig, ax = plt.subplots(figsize=(14,8))
    for market in selected_markets:
        for genome_id in selected_ids:
            curve = df[(df['market'] == market) & (df['id'] == genome_id)]
            if not curve.empty:
                ax.plot(curve['step'], curve['capital'], label=f"{market} | id={genome_id[:6]}")
    ax.set_xlabel('Step')
    ax.set_ylabel('Capital')
    ax.set_title('Equity curves overlay')
    ax.legend()
    st.pyplot(fig)
else:
    st.info("Sélectionnez au moins un marché et un génome.")

st.header("Visualisations avancées (auto-générées)")

def show_png_if_exists(path, caption=None):
    if os.path.exists(path):
        st.image(Image.open(path), caption=caption, use_column_width=True)
    else:
        st.info(f"Image non trouvée : {path}")

col1, col2 = st.columns(2)
with col1:
    show_png_if_exists("results/strategy_distribution.png", "Distribution des stratégies")
    show_png_if_exists("results/fitness_landscape.png", "Paysage de fitness")
with col2:
    show_png_if_exists("results/strategy_clusters.png", "Clusters (espèces)")
    show_png_if_exists("results/strategy_diversity_evolution.png", "Évolution de la diversité")
show_png_if_exists("results/best_fitness_evolution.png", "Évolution du meilleur fitness")
