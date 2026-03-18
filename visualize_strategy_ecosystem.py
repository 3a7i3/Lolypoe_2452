import pandas as pd
import plotly.express as px

# Charger le CSV de population (adapter le chemin/génération si besoin)
df = pd.read_csv('results/pop_gen_19.csv')  # Modifier le numéro de génération si besoin

# Définir la couleur selon le type d'espèce (entry.type)
if 'entry.type' not in df.columns:
    # fallback si le nom de colonne diffère
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
    title='Strategy Ecosystem: Specialization by Environment',
    symbol=entry_type_col
)
fig.show()
