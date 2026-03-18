import matplotlib.pyplot as plt
import pandas as pd

# --- ANALYSE AVANCÉE MULTI-MONDES ---
import os

RESULTS_DIR = "results"
WORLDS = ["trend", "range", "crash", "chaos"]
N_GEN = 30

for world in WORLDS:
    # Charger tous les CSV de ce monde
    dfs = []
    for gen in range(N_GEN):
        path = os.path.join(RESULTS_DIR, f"{world}_pop_gen_{gen}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["generation"] = gen
            dfs.append(df)
    if not dfs:
        continue
    df_all = pd.concat(dfs, ignore_index=True)

    # 1. Evolution des espèces (stacked area)
    species_counts = df_all.groupby(["generation", "species"]).size().unstack(fill_value=0)
    plt.figure(figsize=(10,5))
    species_counts.plot.area(ax=plt.gca(), colormap="Set2")
    plt.title(f"Evolution des espèces ({world})")
    plt.xlabel("Génération")
    plt.ylabel("Nombre d'individus")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f"species_evolution_{world}.png"))
    plt.close()

    # 2. Heatmap fitness par espèce/génération
    import seaborn as sns
    pivot = df_all.pivot_table(index="species", columns="generation", values="fitness", aggfunc="mean")
    plt.figure(figsize=(10,4))
    sns.heatmap(pivot, annot=False, cmap="viridis")
    plt.title(f"Fitness moyenne par espèce/génération ({world})")
    plt.xlabel("Génération")
    plt.ylabel("Espèce")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f"heatmap_fitness_{world}.png"))
    plt.close()

    # 3. Best fitness et robustesse
    best_fitness = df_all.groupby("generation")["fitness"].max()
    mean_fitness = df_all.groupby("generation")["fitness"].mean()
    plt.figure(figsize=(8,4))
    plt.plot(best_fitness, label="Best fitness")
    plt.plot(mean_fitness, label="Mean fitness")
    plt.title(f"Fitness max et moyenne ({world})")
    plt.xlabel("Génération")
    plt.ylabel("Fitness")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f"fitness_progress_{world}.png"))
    plt.close()


# --- ANALYSE TEXTUELLE AUTOMATIQUE ET ANIMATION ---
import numpy as np
from collections import Counter
import imageio

for world in WORLDS:
    # Recharger les données pour analyse
    dfs = []
    for gen in range(N_GEN):
        path = os.path.join(RESULTS_DIR, f"{world}_pop_gen_{gen}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["generation"] = gen
            dfs.append(df)
    if not dfs:
        continue
    df_all = pd.concat(dfs, ignore_index=True)

    # Analyse textuelle
    print(f"\n=== Analyse automatique du monde {world} ===")
    # Espèces dominantes par génération
    doms = []
    for gen, group in df_all.groupby("generation"):
        counts = Counter(group["species"])
        dom = counts.most_common(1)[0][0]
        doms.append(dom)
    dom_mode = Counter(doms).most_common(1)[0][0]
    print(f"Espèce dominante la plus fréquente : {dom_mode}")
    # Robustesse : nombre de générations où l'espèce dominante change
    switches = sum([doms[i] != doms[i-1] for i in range(1, len(doms))])
    print(f"Nombre de changements d'espèce dominante : {switches} sur {N_GEN} générations")
    # Diversité moyenne
    diversity = [len(set(group["species"])) for _, group in df_all.groupby("generation")]
    print(f"Diversité moyenne (espèces/génération) : {np.mean(diversity):.2f}")
    # Fitness max finale
    best_final = df_all[df_all["generation"]==N_GEN-1]["fitness"].max()
    print(f"Fitness max à la dernière génération : {best_final:.4f}")

    # Animation de l'évolution des espèces (stacked area)
    images = []
    species_counts = df_all.groupby(["generation", "species"]).size().unstack(fill_value=0)
    for last_gen in range(1, N_GEN+1):
        plt.figure(figsize=(8,4))
        species_counts.iloc[:last_gen].plot.area(ax=plt.gca(), colormap="Set2")
        plt.title(f"Evolution des espèces ({world}) - Génération {last_gen-1}")
        plt.xlabel("Génération")
        plt.ylabel("Nombre d'individus")
        plt.tight_layout()
        fname = os.path.join(RESULTS_DIR, f"tmp_anim_{world}_{last_gen}.png")
        plt.savefig(fname)
        plt.close()
        images.append(imageio.imread(fname))
    gif_path = os.path.join(RESULTS_DIR, f"species_evolution_{world}.gif")
    imageio.mimsave(gif_path, images, duration=0.25)
    # Nettoyage des images temporaires
    for last_gen in range(1, N_GEN+1):
        os.remove(os.path.join(RESULTS_DIR, f"tmp_anim_{world}_{last_gen}.png"))
    print(f"Animation GIF générée : {gif_path}")

print("\nAnalyse textuelle et animations GIF générées dans le dossier 'results'.")
