import pandas as pd
import glob
import os

# Analyse automatique des niches écologiques
# - Détecte les spécialistes trend/range/crash
# - Donne la proportion de chaque espèce (entry.type)
# - Affiche les meilleurs scores par environnement

def analyze_niches(csv_path=None):
    required_cols = {'fitness_trend', 'fitness_range', 'fitness_crash', 'entry.type'}
    if not csv_path:
        csv_files = sorted(glob.glob('results/pop_gen_*.csv'))[::-1]  # plus récent d'abord
        assert csv_files, "Aucun fichier CSV de population trouvé."
        for path in csv_files:
            df = pd.read_csv(path)
            if required_cols.issubset(df.columns):
                csv_path = path
                break
        else:
            print("\n[INFO] Aucun CSV de population avec toutes les colonnes requises trouvé.")
            print("Génère une nouvelle population avec le script run_strategy_factory.py pour activer l'analyse des niches écologiques.")
            return
    else:
        df = pd.read_csv(csv_path)
        assert required_cols.issubset(df.columns), f"Colonnes manquantes dans {csv_path}"
    df = pd.read_csv(csv_path)

    # Détection des spécialistes
    def classify(row):
        vals = [row['fitness_trend'], row['fitness_range'], row['fitness_crash']]
        max_env = ['trend', 'range', 'crash'][vals.index(max(vals))]
        return max_env
    df['specialist'] = df.apply(classify, axis=1)

    # Proportion par type d'espèce
    print("\nRépartition des types d'espèces (entry.type) :")
    print(df['entry.type'].value_counts(normalize=True).round(2))

    # Proportion de spécialistes par environnement
    print("\nRépartition des spécialistes par environnement :")
    print(df['specialist'].value_counts(normalize=True).round(2))


    # Meilleurs scores par environnement
    print("\nTop stratégies par environnement :")
    for env in ['trend', 'range', 'crash']:
        best = df.loc[df[f'fitness_{env}'].idxmax()]
        print(f"  {env.upper()} : id={best['id']} | entry.type={best['entry.type']} | score={best[f'fitness_{env}']:.3f}")

    # Visualisation 3D Plotly avec clustering réel (KMeans)
    try:
        import plotly.express as px
        from sklearn.cluster import KMeans
        X = df[["fitness_trend", "fitness_range", "fitness_crash"]].values
        n_clusters = 4  # Peut être ajusté
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        df['cluster'] = kmeans.fit_predict(X)
        fig = px.scatter_3d(
            df,
            x="fitness_trend",
            y="fitness_range",
            z="fitness_crash",
            color="specialist",
            symbol="cluster",
            hover_data=["entry.type", "fitness_trend", "fitness_range", "fitness_crash", "cluster"],
            title="🧬 Écosystème des Stratégies (Espèces + Environnements, Clustering KMeans)"
        )
        fig.show()
    except ImportError:
        print("[INFO] plotly ou scikit-learn n'est pas installé : pip install plotly scikit-learn pour la visualisation 3D avec clustering.")

if __name__ == "__main__":
    analyze_niches()
