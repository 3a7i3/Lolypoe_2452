import panel as pn
import pandas as pd
import os
from glob import glob

pn.extension('plotly')

RESULTS_DIR = "results"
WORLDS = ["trend", "range", "crash", "chaos"]
N_GEN = 30

def load_df(world):
    dfs = []
    for gen in range(N_GEN):
        path = os.path.join(RESULTS_DIR, f"{world}_pop_gen_{gen}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["generation"] = gen
            dfs.append(df)
    if not dfs:
        return None
    return pd.concat(dfs, ignore_index=True)

# Tabs for each world
world_tabs = {}
for world in WORLDS:
    df = load_df(world)
    if df is None:
        continue
    # Evolution stacked area (species)
    import plotly.express as px
    species_counts = df.groupby(["generation", "species"]).size().unstack(fill_value=0)
    fig_area = px.area(species_counts, labels={"value": "Nombre d'individus", "generation": "Génération"}, title=f"Evolution des espèces ({world})")
    # Fitness progression
    best_fitness = df.groupby("generation")["fitness"].max()
    mean_fitness = df.groupby("generation")["fitness"].mean()
    fig_fitness = px.line(x=best_fitness.index, y=best_fitness.values, labels={"x": "Génération", "y": "Fitness"}, title="Fitness max")
    fig_fitness.add_scatter(x=mean_fitness.index, y=mean_fitness.values, mode='lines', name='Fitness moyenne')
    # GIF/MP4 if exists
    gif_path = os.path.join(RESULTS_DIR, f"species_evolution_{world}.gif")
    mp4_path = os.path.join(RESULTS_DIR, f"species_evolution_{world}.mp4")
    gif_panel = pn.pane.GIF(gif_path, width=500) if os.path.exists(gif_path) else pn.pane.Markdown("GIF non généré")
    mp4_panel = pn.pane.Video(mp4_path, width=500) if os.path.exists(mp4_path) else pn.pane.Markdown("MP4 non généré")
    # Layout
    world_tabs[world] = pn.Column(
        pn.pane.Markdown(f"## Monde : {world}"),
        pn.Row(fig_area, fig_fitness),
        pn.Row(gif_panel, mp4_panel),
        sizing_mode="stretch_width"
    )

tabs = pn.Tabs(*[(w, tab) for w, tab in world_tabs.items()])

pn.template.FastListTemplate(
    title="Evolution Darwinienne Multi-Mondes",
    main=[tabs],
    sidebar=[pn.pane.Markdown("# Résultats de l'évolution\n- Sélectionne un monde pour explorer la dynamique\n- Visualisation interactive Plotly, GIF, MP4")],
    accent_base_color="#0072B5"
).servable()
