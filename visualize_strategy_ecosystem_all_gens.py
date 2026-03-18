import pandas as pd
import plotly.express as px
import glob
import os

# Cherche tous les fichiers de population générés
csv_files = sorted(glob.glob('results/pop_gen_*.csv'))

for csv_path in csv_files:
    gen = os.path.splitext(os.path.basename(csv_path))[0].split('_')[-1]
    df = pd.read_csv(csv_path)
    required_cols = {'fitness_trend', 'fitness_range', 'fitness_crash'}
    if not required_cols.issubset(df.columns):
        print(f"[GEN {gen}] Colonnes manquantes pour visualisation avancée. Fichier ignoré : {csv_path}")
        continue
    if 'entry.type' not in df.columns:
        entry_type_col = [c for c in df.columns if 'entry.type' in c][0]
    else:
        entry_type_col = 'entry.type'
    fig = px.scatter_3d(
        df,
        x='fitness_trend',
        y='fitness_range',
        z='fitness_crash',
        color=entry_type_col,
        hover_data=df.columns,
        title=f'Strategy Ecosystem (Gen {gen})',
        symbol=entry_type_col
    )
    fig.show()
    input(f"Appuyez sur Entrée pour passer à la génération suivante ({gen})...")
