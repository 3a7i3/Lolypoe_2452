import matplotlib.pyplot as plt
def migrate(populations, migration_rate=0.1):
    # populations: dict {monde: [population]}
    # migration_rate: fraction d'individus à migrer
    keys = list(populations.keys())
    migrants = {k: [] for k in keys}
    for k in keys:
        pop = populations[k]
        n_mig = max(1, int(len(pop) * migration_rate))
        migrants[k] = random.sample(pop, n_mig)
    # Envoie les migrants dans le monde suivant (anneau)
    for i, k in enumerate(keys):
        next_k = keys[(i+1)%len(keys)]
        populations[next_k].extend(migrants[k])
        # Retire les migrants de leur monde d'origine
        populations[k] = [g for g in populations[k] if g not in migrants[k]]
    return populations
from collections import Counter

# --- ENVIRONNEMENT CHAOTIQUE ---
ENV_OPTIONS = ["trend", "range", "crash"]
def get_random_environment():
    return random.choice(ENV_OPTIONS)

# --- EXTINCTION D'ESPÈCES ---
def apply_extinction(population, min_species_size=5):
    counts = Counter(g.genes["entry.type"] for g in population)
    return [g for g in population if counts[g.genes["entry.type"]] >= min_species_size]

# --- REPRODUCTION PAR ESPÈCE ---
def select_parents(survivors):
    parent1 = random.choice(survivors)
    species = parent1.genes["entry.type"]
    same_species = [g for g in survivors if g.genes["entry.type"] == species]
    if len(same_species) > 1:
        parent2 = random.choice(same_species)
    else:
        parent2 = random.choice(survivors)
    return parent1, parent2

# --- EVOLVE AGGRESSIVE ---
def evolve_aggressive(population):
    current_env = get_random_environment()

    # Fitness par environnement courant uniquement
    for g in population:
        if current_env == "trend":
            g.fitness = float(score_env_trend(g))
        elif current_env == "range":
            g.fitness = float(score_env_range(g))
        elif current_env == "crash":
            g.fitness = float(score_env_crash(g))

    population.sort(key=lambda g: g.fitness, reverse=True)
    survivors = population[:max(1, int(len(population)*0.08))]
    survivors = apply_extinction(survivors)

    # Si extinction totale, on relâche la pression pour éviter le crash
    if not survivors:
        # On prend les 3 meilleurs de la population pour relancer
        survivors = population[:min(3, len(population))]
        print("[⚠️ EXTINCTION TOTALE] Relance avec les meilleurs survivants!")

    new_population = survivors.copy()
    while len(new_population) < len(population) - 2:
        if len(survivors) == 0:
            p1 = p2 = random.choice(population)
        else:
            p1, p2 = select_parents(survivors)
        child = crossover(p1, p2)
        child = mutate(child, mutation_rate=0.3, intensity=0.2)
        if current_env == "trend":
            child.fitness = float(score_env_trend(child))
        elif current_env == "range":
            child.fitness = float(score_env_range(child))
        elif current_env == "crash":
            child.fitness = float(score_env_crash(child))
        new_population.append(child)
    # Ajout de 2 individus random (seed/migration)
    for _ in range(2):
        g = Genome()
        if current_env == "trend":
            g.fitness = float(score_env_trend(g))
        elif current_env == "range":
            g.fitness = float(score_env_range(g))
        elif current_env == "crash":
            g.fitness = float(score_env_crash(g))
        new_population.append(g)
    return new_population, current_env

# --- SCORE PAR ENVIRONNEMENT ---
def score_env_trend(g):
    prices = generate_trend_market()
    equity = backtest(g, prices)
    final_return = equity[-1]
    drawdown = compute_drawdown(equity)
    sharpe = compute_sharpe(equity)
    return final_return * 0.4 + sharpe * 0.4 - drawdown * 0.6

def score_env_range(g):
    prices = generate_range_market()
    equity = backtest(g, prices)
    final_return = equity[-1]
    drawdown = compute_drawdown(equity)
    sharpe = compute_sharpe(equity)
    return final_return * 0.4 + sharpe * 0.4 - drawdown * 0.6

def score_env_crash(g):
    prices = generate_crash_market()
    equity = backtest(g, prices)
    final_return = equity[-1]
    drawdown = compute_drawdown(equity)
    sharpe = compute_sharpe(equity)
    return final_return * 0.4 + sharpe * 0.4 - drawdown * 0.6
# === Générateurs de marchés multiples ===

def generate_trend_market(length=500):
    prices = [100.0]
    for _ in range(length):
        change = np.random.normal(0.05, 1)  # biais haussier
        prices.append(prices[-1] * (1 + change * 0.01))
    return np.array(prices)


def generate_range_market(length=500):
    prices = [100.0]
    for _ in range(length):
        change = np.random.normal(0, 0.5)
        prices.append(prices[-1] * (1 + change * 0.01))
    return np.array(prices)


def generate_crash_market(length=500):
    prices = [100.0]
    for i in range(length):
        if i > length // 2:
            change = np.random.normal(-0.2, 1)
        else:
            change = np.random.normal(0, 1)
        prices.append(prices[-1] * (1 + change * 0.01))
    return np.array(prices)

# === Algorithme évolutif standalone (Step 1+2) ===
import random
import uuid
import numpy as np

# 1. GeneSpace (l'univers des gènes)

# Ajout des gènes MA crossover
GENE_SPACE = {
    "entry.type": ["trend", "mean_reversion", "hybrid"],
    "entry.rsi_period": (5, 30),
    "entry.rsi_buy": (30, 70),
    "ma_short": (5, 50),   # période de la moyenne mobile courte
    "ma_long": (20, 200),  # période de la moyenne mobile longue
    "ma_signal": ["cross_over", "cross_under"],
    "exit.tp": (0.5, 5.0),
    "exit.sl": (0.3, 3.0),
    "risk.risk_per_trade": (0.001, 0.03)
}
# 7b. MA crossover
def ma_signal(prices, short, long, signal_type="cross_over"):
    ma_s = np.convolve(prices, np.ones(int(short))/int(short), mode='valid')
    ma_l = np.convolve(prices, np.ones(int(long))/int(long), mode='valid')
    min_len = min(len(ma_s), len(ma_l))
    ma_s = ma_s[-min_len:]
    ma_l = ma_l[-min_len:]
    if signal_type == "cross_over":
        return np.where(np.diff((ma_s > ma_l).astype(int)) == 1)[0] + 1
    else:
        return np.where(np.diff((ma_s < ma_l).astype(int)) == 1)[0] + 1

# 1b. Clamp gene (bornes)
def clamp_gene(key, value):
    space = GENE_SPACE[key]
    if isinstance(space, tuple):
        return max(space[0], min(space[1], value))
    return value

# 2. Classe Genome

class Genome:
    def __init__(self, genes=None):
        self.id = str(uuid.uuid4())[:8]  # ID unique court
        self.genes = genes if genes else self.random_genome()
        self.fitness: float = 0.0
        self.fitness_trend: float = 0.0
        self.fitness_range: float = 0.0
        self.fitness_crash: float = 0.0
        self.parent_ids = []  # Tracking lignée

    def random_genome(self):
        genome = {}
        for key, val in GENE_SPACE.items():
            if isinstance(val, tuple):
                genome[key] = random.uniform(*val)
            elif isinstance(val, list):
                genome[key] = random.choice(val)
        return genome

    def copy(self):
        return Genome(self.genes.copy())

    def get(self, key, default=None):
        return self.genes.get(key, default)

# 3. Mutation
def mutate(genome, mutation_rate=0.2, intensity=0.1):
    new_genes = genome.genes.copy()
    for key in new_genes:
        if random.random() < mutation_rate:
            space = GENE_SPACE[key]
            if isinstance(space, tuple):
                current = new_genes[key]
                delta = (space[1] - space[0]) * intensity
                new_val = current + random.uniform(-delta, delta)
                new_genes[key] = clamp_gene(key, new_val)
            elif isinstance(space, list):
                new_genes[key] = random.choice(space)
    return Genome(new_genes)

# 4. Crossover
def crossover(parent1, parent2):
    child_genes = {}
    for key in parent1.genes:
        if random.random() < 0.5:
            child_genes[key] = parent1.genes[key]
        else:
            child_genes[key] = parent2.genes[key]
        child_genes[key] = clamp_gene(key, child_genes[key])
    child = Genome(child_genes)
    child.parent_ids = [parent1.id, parent2.id]
    return child

# 5. Population initiale
def create_population(size=50):
    return [Genome() for _ in range(size)]

# 6. Génération de prix simulés (marché)
def generate_price_series(length=500):
    prices = []
    prices.append(float(100))
    for _ in range(length):
        change = np.random.normal(0, 1)
        prices.append(prices[-1] * (1 + change * 0.01))
    return np.array(prices)

# 7. RSI
def compute_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = -np.minimum(deltas, 0)
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    return rsi


# 8. Backtest avec equity curve
def backtest(genome, prices):
    tp = genome.get("exit.tp") / 100
    sl = genome.get("exit.sl") / 100
    capital = 1.0
    equity_curve = [capital]
    position = None
    entry_price = 0
    entry_type = genome.get("entry.type")

    # RSI params
    rsi_period = int(genome.get("entry.rsi_period"))
    rsi_buy = genome.get("entry.rsi_buy")
    rsi = compute_rsi(prices, rsi_period)

    # MA params
    ma_short = int(genome.get("ma_short", 10))
    ma_long = int(genome.get("ma_long", 30))
    ma_sig = genome.get("ma_signal", "cross_over")
    ma_idx = ma_signal(prices, ma_short, ma_long, ma_sig)
    ma_idx_set = set(ma_idx)

    # Align all signals to the same index base
    min_len = min(len(rsi), len(prices)-1)
    for i in range(min_len):
        price = prices[i + 1]
        signal = False
        if entry_type == "mean_reversion":
            if rsi[i] < rsi_buy:
                signal = True
        elif entry_type == "trend":
            if i in ma_idx_set:
                signal = True
        elif entry_type == "hybrid":
            if (rsi[i] < rsi_buy) and (i in ma_idx_set):
                signal = True
        if position is None and signal:
            position = "long"
            entry_price = price
        elif position == "long":
            change = (price - entry_price) / entry_price
            if change >= tp or change <= -sl:
                capital *= (1 + change)
                position = None
        equity_curve.append(capital)
    return equity_curve

# 9b. Drawdown
def compute_drawdown(equity_curve):
    equity = np.array(equity_curve)
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    max_dd = np.min(drawdown)
    return abs(max_dd)

# 9c. Sharpe ratio
def compute_sharpe(equity_curve):
    equity = np.array(equity_curve)
    returns = np.diff(equity) / equity[:-1]
    if np.std(returns) == 0:
        return 0
    sharpe = np.mean(returns) / np.std(returns)
    return sharpe

# 9. Fitness réel

# 10. Fitness composite

def evaluate_fitness(genome):
    # Spécialisation par environnement
    trend_prices = generate_trend_market()
    range_prices = generate_range_market()
    crash_prices = generate_crash_market()

    def score_env(prices):
        equity = backtest(genome, prices)
        final_return = equity[-1]
        drawdown = compute_drawdown(equity)
        sharpe = compute_sharpe(equity)
        score = (
            final_return * 0.4 +
            sharpe * 0.4 -
            drawdown * 0.6
        )
        return score

    genome.fitness_trend = score_env(trend_prices)
    genome.fitness_range = score_env(range_prices)
    genome.fitness_crash = score_env(crash_prices)
    genome.fitness = (genome.fitness_trend + genome.fitness_range + genome.fitness_crash) / 3

# 10. Cycle évolution
def evolve(population):
    for g in population:
        evaluate_fitness(g)
    population.sort(key=lambda x: x.fitness, reverse=True)
    survivors = population[:max(1, int(len(population)*0.2))]
    new_population = []
    for s in survivors:
        if s.fitness is None:
            evaluate_fitness(s)
        new_population.append(s)
    while len(new_population) < len(population):
        p1 = random.choice(survivors)
        p2 = random.choice(survivors)
        child = crossover(p1, p2)
        child = mutate(child)
        evaluate_fitness(child)
        new_population.append(child)
    return new_population

# 11. Test rapide
if __name__ == "__main__":
    import pandas as pd
    history = []
    # --- GOD MODE ---
    TRACKED_ID = None  # Renseignez un ID pour suivre une stratégie
    # --- MONDES PARALLÈLES ---
    N_WORLDS = 4
    WORLD_NAMES = ["trend", "range", "crash", "chaos"]
    POP_SIZE = 100
    N_GEN = 100  # Accélération temporelle (ex: 100 générations)
    MIGRATION_FREQ = 5
    MIGRATION_RATE = 0.1

    # Initialisation des mondes
    populations = {w: create_population(POP_SIZE) for w in WORLD_NAMES}
    envs = {w: w for w in WORLD_NAMES}
    histories = {w: [] for w in WORLD_NAMES}

    for generation in range(N_GEN):
        for w in WORLD_NAMES:
            # Pour chaque monde, évolution dans son environnement
            def evolve_world(pop, env):
                # Monde chaotique : environnement aléatoire à chaque génération
                if env == "chaos":
                    current_env = get_random_environment()
                else:
                    current_env = env
                for g in pop:
                    if current_env == "trend":
                        g.fitness = float(score_env_trend(g))
                    elif current_env == "range":
                        g.fitness = float(score_env_range(g))
                    elif current_env == "crash":
                        g.fitness = float(score_env_crash(g))
                pop.sort(key=lambda g: g.fitness, reverse=True)
                survivors = pop[:max(1, int(len(pop)*0.08))]
                survivors = apply_extinction(survivors)
                if not survivors:
                    survivors = pop[:min(3, len(pop))]
                new_pop = survivors.copy()
                while len(new_pop) < len(pop) - 2:
                    if len(survivors) == 0:
                        p1 = p2 = random.choice(pop)
                    else:
                        p1, p2 = select_parents(survivors)
                    child = crossover(p1, p2)
                    child = mutate(child, mutation_rate=0.3, intensity=0.2)
                    if current_env == "trend":
                        child.fitness = float(score_env_trend(child))
                    elif current_env == "range":
                        child.fitness = float(score_env_range(child))
                    elif current_env == "crash":
                        child.fitness = float(score_env_crash(child))
                    new_pop.append(child)
                # Ajout de 2 random
                for _ in range(2):
                    g = Genome()
                    if current_env == "trend":
                        g.fitness = float(score_env_trend(g))
                    elif current_env == "range":
                        g.fitness = float(score_env_range(g))
                    elif current_env == "crash":
                        g.fitness = float(score_env_crash(g))
                    new_pop.append(g)
                return new_pop, current_env
            # On stocke l'environnement courant pour le monde chaotique
            if w == "chaos":
                populations[w], envs[w] = evolve_world(populations[w], w)
            else:
                populations[w] = evolve_world(populations[w], envs[w])[0]
        # Migration croisée
        if (generation+1) % MIGRATION_FREQ == 0:
            populations = migrate(populations, migration_rate=MIGRATION_RATE)
            print(f"\n🌐 MIGRATION entre mondes à la génération {generation+1}\n")
        # Logs et historique
        for w in WORLD_NAMES:
            pop = populations[w]
            pop_data = []
            for g in pop:
                row = {**g.genes, "fitness": g.fitness, "id": g.id, "environment": envs[w], "species": g.genes["entry.type"], "world": w, "parent_ids": ",".join(g.parent_ids) if hasattr(g, "parent_ids") else ""}
                pop_data.append(row)
            df = pd.DataFrame(pop_data)
            histories[w].append(df)
            species_counts = Counter(g.genes["entry.type"] for g in pop)
            best = max(pop, key=lambda g: g.fitness)
            print(f"""
            [MONDE: {w}] Gen {generation}
            🌍 Environment: {envs[w]}
            🧬 Best fitness: {best.fitness:.4f}
            🧠 Species: {best.genes['entry.type']}
            🦠 Species counts: {dict(species_counts)}
            🔗 Best ID: {best.id}
            🧬 Parents: {getattr(best, 'parent_ids', [])}
            """)
            if TRACKED_ID and best.id == TRACKED_ID:
                print("🔥 TRACKED STRATEGY SURVIVED")
            # Export CSV de la population
            df.to_csv(f"results/{w}_pop_gen_{generation}.csv", index=False)
            print(f"  CSV exporté : results/{w}_pop_gen_{generation}.csv")

    # --- VISUALISATION ---
    # Diversité des espèces et fitness moyenne par monde
    for w in WORLD_NAMES:
        generations = list(range(N_GEN))
        diversity = []
        mean_fitness = []
        for df in histories[w]:
            diversity.append(len(set(df['species'])))
            mean_fitness.append(df['fitness'].mean())
        plt.figure(figsize=(10,4))
        plt.subplot(1,2,1)
        plt.plot(generations, diversity, label='Diversité (espèces)')
        plt.title(f"Diversité des espèces - {w}")
        plt.xlabel("Génération")
        plt.ylabel("Nombre d'espèces")
        plt.subplot(1,2,2)
        plt.plot(generations, mean_fitness, label='Fitness moyenne')
        plt.title(f"Fitness moyenne - {w}")
        plt.xlabel("Génération")
        plt.ylabel("Fitness")
        plt.tight_layout()
        plt.savefig(f"results/plot_{w}.png")
        print(f"  Graphique exporté : results/plot_{w}.png")

    # === TIMELINE ÉVOLUTIVE CINÉMATIQUE ===
    import plotly.express as px
    # 1. Stockage history pour timeline
    history = []
    for gen in range(N_GEN):
        for w in WORLD_NAMES:
            df = histories[w][gen].copy()
            df["generation"] = gen
            df["environment"] = envs[w]
            history.append(df)
    # 2. Dataset global
    full_df = pd.concat(history, ignore_index=True)
    # 3. Visualisation GOD MODE
    def plot_god_mode(full_df, tracked_id=None):
        df = full_df.copy()
        if tracked_id:
            df["highlight"] = df["id"].apply(lambda x: "TRACKED" if x == tracked_id else "normal")
        else:
            df["highlight"] = "normal"
        fig = px.scatter_3d(
            df,
            x="exit.tp",
            y="exit.sl",
            z="fitness",
            color="species",
            symbol="highlight",
            animation_frame="generation",
            size="fitness",
            hover_data=["id", "environment", "parent_ids"],
            title="👁️ GOD MODE - Strategy Evolution"
        )
        fig.show()
    plot_god_mode(full_df, tracked_id=TRACKED_ID)
    # 4. Visualisation domination par espèce
    def plot_dominance(full_df):
        df = full_df.groupby(["generation", "species"]).size().reset_index(name="count")
        fig = px.area(
            df,
            x="generation",
            y="count",
            color="species",
            title="🌍 Species Domination Over Time"
        )
        fig.show()
    plot_dominance(full_df)
