import multiprocessing as mp
import random
from mpl_toolkits.mplot3d import Axes3D

# --- ESPACE DES GÈNES (métier) ---
GENE_SPACE = {
    "entry.type": ["trend", "mean_reversion", "breakout"],
    "entry.rsi_period": (5, 30),
    "entry.rsi_buy": (10, 40),
    "entry.rsi_sell": (60, 90),
    "exit.tp": (0.5, 5.0),
    "exit.sl": (0.3, 3.0),
    "risk.risk_per_trade": (0.001, 0.03),
}

class Genome:
    def __init__(self, genes):
        self.genes = genes  # dict de paramètres
        self.fitness = 0.0


# --- LOGIQUE D'ÉVALUATION (fitness métier) ---
def evaluate_fitness(genome):
    """
    Fitness combinant :
    - capital final
    - stabilité (drawdown)
    - régularité (Sharpe)
    """
    # Ces fonctions doivent être définies ailleurs dans ton code
    def generate_trend_market():
        # Dummy: à remplacer par ta génération de marché
        return [100 + i + random.gauss(0, 1) for i in range(100)]
    def generate_range_market():
        return [100 + 5 * np.sin(i/10) + random.gauss(0, 1) for i in range(100)]
    def generate_crash_market():
        return [100 - min(i, 50) + random.gauss(0, 1) for i in range(100)]
    def backtest(genome, prices):
        # Dummy: à remplacer par ton vrai backtest
        # Retourne une courbe d'equity (ici, random walk)
        eq = [100.0]
        for _ in prices:
            eq.append(eq[-1] * (1 + random.uniform(-0.01, 0.01)))
        return eq
    def compute_drawdown(equity):
        peak = equity[0]
        max_dd = 0
        for x in equity:
            if x > peak:
                peak = x
            dd = (peak - x) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd
    def compute_sharpe(equity):
        returns = np.diff(equity) / equity[:-1]
        if returns.std() == 0:
            return 0
        return returns.mean() / returns.std() * np.sqrt(252)

    markets = [generate_trend_market(), generate_range_market(), generate_crash_market()]
    scores = []
    for prices in markets:
        equity = backtest(genome, prices)
        final_return = equity[-1] - equity[0]
        max_dd = compute_drawdown(equity)
        sharpe = compute_sharpe(equity)
        score = final_return * 0.5 + sharpe * 0.3 - max_dd * 0.7
        scores.append(score)
    genome.fitness = sum(scores) / len(scores)
    return genome

def evaluate_one(genome):
    evaluate_fitness(genome)
    return genome

def evaluate_population_parallel(population, n_workers=None):
    if n_workers is None:
        n_workers = mp.cpu_count()
    with mp.Pool(n_workers) as pool:
        population = pool.map(evaluate_one, population)
    return population


# --- UNIFORM CROSSOVER (gène par gène) ---
def crossover(parent1, parent2):
    child_genes = {}
    for key in parent1.genes:
        if random.random() < 0.5:
            child_genes[key] = parent1.genes[key]
        else:
            child_genes[key] = parent2.genes[key]
    return Genome(child_genes)

# --- MUTATION AVEC CONTRAINTES ---
def mutate(genome, mutation_rate=0.2, intensity=0.1):
    new_genes = genome.genes.copy()
    for key in new_genes:
        if random.random() < mutation_rate:
            space = GENE_SPACE[key]
            if isinstance(space, tuple):  # valeur continue
                delta = (space[1] - space[0]) * intensity
                new_val = new_genes[key] + random.uniform(-delta, delta)
                new_genes[key] = max(space[0], min(space[1], new_val))
            elif isinstance(space, list):  # choix discret
                new_genes[key] = random.choice(space)
    return Genome(new_genes)


# --- CRÉATION DE POPULATION ALÉATOIRE SELON GENE_SPACE ---
def create_population(size):
    pop = []
    for _ in range(size):
        genes = {}
        for key, space in GENE_SPACE.items():
            if isinstance(space, tuple):
                genes[key] = random.uniform(space[0], space[1])
            elif isinstance(space, list):
                genes[key] = random.choice(space)
        pop.append(Genome(genes))
    return pop


# --- ÉVOLUTION AVEC ÉLITISME, REPRODUCTION, MUTATION ---
def evolve(population, elite_fraction=0.2, n_workers=None):
    # 1. Évaluer fitness (parallèle)
    population = evaluate_population_parallel(population, n_workers=n_workers)
    # 2. Trier par fitness
    population.sort(key=lambda g: g.fitness, reverse=True)
    # 3. Garder les élites
    survivors = population[:int(len(population) * elite_fraction)]
    # 4. Reproduction + mutation pour remplir la population
    new_population = survivors.copy()
    while len(new_population) < len(population):
        p1, p2 = random.sample(survivors, 2)
        child = crossover(p1, p2)
        child = mutate(child)
        new_population.append(child)
    return new_population
def plot_3d_population(df):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    x = df["exit.tp"]
    y = df["exit.sl"]
    z = df["fitness"]
    ax.scatter(x, y, z, alpha=0.7)
    ax.set_xlabel("Take Profit")
    ax.set_ylabel("Stop Loss")
    ax.set_zlabel("Fitness")
    plt.title("3D Strategy Landscape")
    plt.tight_layout()
    plt.show()

def plot_3d_colored(df):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    x = df["exit.tp"]
    y = df["exit.sl"]
    z = df["fitness"]
    scatter = ax.scatter(x, y, z, c=z, cmap="viridis", alpha=0.8)
    fig.colorbar(scatter, label="Fitness")
    ax.set_xlabel("TP")
    ax.set_ylabel("SL")
    ax.set_zlabel("Fitness")
    plt.title("3D Fitness Landscape")
    plt.tight_layout()
    plt.show()

def plot_3d_clusters(df):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    x = df["exit.tp"]
    y = df["exit.sl"]
    z = df["fitness"]
    c = df["cluster"] if "cluster" in df else None
    scatter = ax.scatter(x, y, z, c=c, cmap="tab10", alpha=0.8)
    if c is not None:
        fig.colorbar(scatter, label="Cluster")
    ax.set_xlabel("TP")
    ax.set_ylabel("SL")
    ax.set_zlabel("Fitness")
    plt.title("3D Strategy Species (Clusters)")
    plt.tight_layout()
    plt.show()

def animate_3d(history):
    plt.ion()
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    for i, df in enumerate(history):
        ax.clear()
        x = df["exit.tp"]
        y = df["exit.sl"]
        z = df["fitness"]
        scatter = ax.scatter(x, y, z, c=z, cmap="viridis", alpha=0.8)
        ax.set_xlabel("TP")
        ax.set_ylabel("SL")
        ax.set_zlabel("Fitness")
        ax.set_title(f"3D Fitness Landscape - Gen {i+1}")
        plt.pause(0.3)
    plt.ioff()
    plt.show()

# --- Imports standards ---
import os
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# --- Imports Plotly PRO ---
import plotly.express as px

# --- Visualisations interactives Plotly PRO ---
def plotly_3d_population(df):
    """Vue 3D interactive de la population (fitness en couleur)"""
    fig = px.scatter_3d(
        df,
        x="exit.tp",
        y="exit.sl",
        z="fitness",
        color="fitness",
        hover_data=df.columns,
        title="🌍 Strategy Fitness Landscape"
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        scene=dict(
            xaxis_title="Take Profit",
            yaxis_title="Stop Loss",
            zaxis_title="Fitness"
        )
    )
    fig.show()

def plotly_3d_clusters(df):
    """Vue 3D interactive par clusters/espèces (colonne 'cluster' requise)"""
    fig = px.scatter_3d(
        df,
        x="exit.tp",
        y="exit.sl",
        z="fitness",
        color="cluster",
        hover_data=df.columns,
        title="🧬 Strategy Species (Clusters)"
    )
    fig.update_traces(marker=dict(size=5))
    fig.show()

def plotly_top_strategies(df, top_n=50):
    """Vue 3D interactive des top stratégies (taille = fitness)"""
    top_df = df.sort_values("fitness", ascending=False).head(top_n)
    fig = px.scatter_3d(
        top_df,
        x="exit.tp",
        y="exit.sl",
        z="fitness",
        color="fitness",
        size="fitness",  # Upgrade PRO: taille par fitness
        title=f"🏆 Top {top_n} Strategies"
    )
    fig.show()

def plotly_animation(history):
    """Animation 3D de l'évolution des stratégies (history = liste de DataFrames par génération)"""
    full_df = []
    for i, df in enumerate(history):
        temp = df.copy()
        temp["generation"] = i
        full_df.append(temp)
    full_df = pd.concat(full_df)
    fig = px.scatter_3d(
        full_df,
        x="exit.tp",
        y="exit.sl",
        z="fitness",
        color="fitness",
        size="fitness",  # Upgrade PRO: taille par fitness
        animation_frame="generation",
        title="🧬 Evolution of Strategies"
    )
    fig.show()

# --- Visualisation avancée pour stratégies évolutives ---
def population_to_df(population):
    data = []
    for g in population:
        row = g.genes.copy()
        row["fitness"] = g.fitness
        data.append(row)
    return pd.DataFrame(data)

def plot_best_equity(genome, prices, backtest_fn):
    equity = backtest_fn(genome, prices)
    plt.figure(figsize=(10, 4))
    plt.plot(equity, color="dodgerblue")
    plt.title("Best Strategy Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.show()

def plot_diversity(history):
    diversity = [df.drop_duplicates(subset=["exit.tp", "exit.sl"]).shape[0] for df in history]
    plt.figure(figsize=(8, 4))
    plt.plot(diversity, marker="x", color="orange")
    plt.title("Strategy Diversity Evolution")
    plt.xlabel("Generation")
    plt.ylabel("Unique Strategies")
    plt.grid(True)
    plt.show()

def load_generation_data(results_dir="."):
    print(f"[INFO] Recherche des fichiers de génération dans : {results_dir}")
    files = sorted([f for f in os.listdir(results_dir) if f.startswith("gen_") and f.endswith(".json")],
                   key=lambda x: int(x.split('_')[1].split('.')[0]))
    print(f"[INFO] Fichiers trouvés : {files}")
    generations = []
    avg_scores = []
    max_scores = []
    min_scores = []
    all_params = []
    for fname in files:
        try:
            with open(os.path.join(results_dir, fname), "r") as f:
                data = json.load(f)
                # Ne garder que les individus avec un champ 'score' numérique
                valid = [d for d in data if isinstance(d, dict) and "score" in d and isinstance(d["score"], (int, float))]
                if not valid:
                    print(f"[WARN] Fichier {fname} sans individus valides (champ 'score' manquant ou non numérique)")
                    continue
                scores = [d["score"] for d in valid]
                print(f"[GEN] {fname} : {len(valid)} individus valides | Score min={min(scores):.4f} | max={max(scores):.4f} | moy={sum(scores)/len(scores):.4f}")
                generations.append(fname)
                avg_scores.append(sum(scores)/len(scores))
                max_scores.append(max(scores))
                min_scores.append(min(scores))
                all_params.extend(valid)
        except Exception as e:
            print(f"[ERROR] Lecture de {fname} : {e}")
            continue
    print(f"[INFO] Générations valides : {len(generations)}")
    if generations:
        print(f"[INFO] Score global : min={min(min_scores):.4f} | max={max(max_scores):.4f} | moy={sum(avg_scores)/len(avg_scores):.4f}")
    print(f"[INFO] Nombre total d'individus analysés : {len(all_params)}")
    # Si aucune génération valide, retourner des listes vides mais cohérentes
    if not generations:
        print("[ERROR] Aucune génération valide trouvée dans le dossier.")
    return generations, avg_scores, max_scores, min_scores, all_params

def plot_evolution(generations, avg_scores, max_scores, min_scores):
    plt.figure(figsize=(10,6))
    plt.plot(generations, avg_scores, label="Score moyen")
    plt.plot(generations, max_scores, label="Score max")
    plt.plot(generations, min_scores, label="Score min")
    plt.xlabel("Génération")
    plt.ylabel("Score")
    plt.title("Évolution des scores par génération")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("evolution_scores.png")
    print("Figure sauvegardée sous evolution_scores.png")
    plt.show()

def plot_param_distribution(all_params):
    import pandas as pd
    df = pd.DataFrame(all_params)
    print("DataFrame pour distribution:")
    print(df.head())
    if df.empty:
        print("Aucune donnée à afficher pour la distribution.")
        return
    plt.figure(figsize=(12,6))
    # Paramètres du moteur génétique actuel
    param_cols = ["entry.rsi_period", "entry.rsi_buy", "exit.tp", "exit.sl", "risk.risk_per_trade", "fitness"]
    for col in param_cols:
        if col in df:
            plt.hist(df[col], bins=20, alpha=0.6, label=col)
    plt.xlabel("Valeur")
    plt.ylabel("Fréquence")
    plt.title("Distribution des paramètres sur toutes les générations")
    plt.legend()
    plt.tight_layout()
    plt.savefig("param_distribution.png")
    print("Figure sauvegardée sous param_distribution.png")
    plt.show()

def plot_heatmap(all_params):
    import pandas as pd
    import seaborn as sns
    df = pd.DataFrame(all_params)
    print("DataFrame pour heatmap:")
    print(df.head())
    if df.empty:
        print("Aucune donnée à afficher pour la heatmap.")
        return
    plt.figure(figsize=(8,6))
    # Heatmap fitness vs entry.rsi_period/entry.rsi_buy
    if set(["entry.rsi_period", "entry.rsi_buy", "fitness"]).issubset(df.columns):
        pivot = df.pivot_table(index="entry.rsi_period", columns="entry.rsi_buy", values="fitness", aggfunc="mean")
        if pivot.empty:
            print("Pivot table vide, heatmap non générée.")
            return
        sns.heatmap(pivot, cmap="viridis")
        plt.title("Heatmap fitness vs rsi_period/rsi_buy")
        plt.tight_layout()
        plt.savefig("param_heatmap.png")
        print("Figure sauvegardée sous param_heatmap.png")
        plt.show()

def export_csv(all_params):
    import pandas as pd
    df = pd.DataFrame(all_params)
    df.to_csv("evolution_params.csv", index=False)
    print("CSV exporté sous evolution_params.csv")



if __name__ == "__main__":
    # Protection Windows/Mac pour multiprocessing
    pop_size = 50
    generations = 10
    n_workers = 4  # Ajuste selon ta machine
    pop = create_population(pop_size)
    for generation in range(generations):
        pop = evolve(pop, elite_fraction=0.2, n_workers=n_workers)
        best = max(pop, key=lambda g: g.fitness)
        print(f"Gen {generation} | Best fitness: {best.fitness:.4f} | Genes: {best.genes}")

    # Conversion DataFrame pour analyse/plots
    df = population_to_df(pop)
    print(df.head())

# --- Exemples d'utilisation pour visualisation avancée ---
# population = ...
# evolve_fn = ...
# prices = ...
# backtest_fn = ...
# df = population_to_df(population)
# plot_population(df)
# plot_fitness(df)
# df_clustered, kmeans = cluster_population(df, k=3)
# plot_clusters(df_clustered)
# history = track_evolution(population, evolve_fn, generations=20)
# plot_evolution_simple(history)
# plot_diversity(history)
# best_genome = ... # select best genome from population
# plot_best_equity(best_genome, prices, backtest_fn)
