import random
import copy

class StrategyEvolution:
    def __init__(self, genome_engine):
        self.genome_engine = genome_engine

    def fitness(self, strategy):
        # Placeholder: à remplacer par un vrai backtest
        # Ici, on simule la performance par un score aléatoire
        return random.uniform(-1, 2)

    def select(self, population, top_k=10):
        scored = [(self.fitness(s), s) for s in population]
        scored.sort(reverse=True, key=lambda x: x[0])
        return [s for _, s in scored[:top_k]]

    def mutate(self, strategy, mutation_rate=0.2):
        new_strategy = copy.deepcopy(strategy)
        if random.random() < mutation_rate:
            new_strategy["entry"] = random.choice(self.genome_engine.entry_signals)
        if random.random() < mutation_rate:
            new_strategy["filter"] = random.choice(self.genome_engine.filters)
        if random.random() < mutation_rate:
            new_strategy["exit"] = random.choice(self.genome_engine.exit_rules)
        return new_strategy

    def evolve(self, population, generations=5, top_k=10, mutation_rate=0.2):
        for gen in range(generations):
            selected = self.select(population, top_k)
            next_gen = []
            while len(next_gen) < len(population):
                parent = random.choice(selected)
                child = self.mutate(parent, mutation_rate)


                import random
                from typing import List, Dict
                import json
                import numpy as np
                import pandas as pd
                import matplotlib.pyplot as plt


                class StrategyEvolution:
                    def __init__(self, genome_engine, population_size=100, df=None, prices=None):
                        self.genome_engine = genome_engine
                        self.population_size = population_size
                        self.population = self.genome_engine.generate_population(population_size)
                        self.df = df
                        self.prices = prices
                        try:
                            from quant.backtester import Backtester
                            from strategy_backtest_integration import strategy_to_signal
                            self.backtester = Backtester()
                            self.strategy_to_signal = strategy_to_signal
                        except ImportError:
                            self.backtester = None
                            self.strategy_to_signal = None

                    # Évalue chaque stratégie avec un score fictif pour l'exemple
                    def evaluate_strategy(self, strategy: Dict) -> float:
                        # Utilise le backtester réel si disponible
                        if self.backtester and self.df is not None and self.prices is not None and self.strategy_to_signal:
                            try:
                                signals = self.strategy_to_signal(strategy, self.df)
                                result = self.backtester.backtest(self.prices, signals)
                                # Score = Sharpe + Total Return (pondéré)
                                score = float(result.get("sharpe", 0)) + 0.5 * float(result.get("total_return", 0))
                                return score
                            except Exception as e:
                                return -999
                        # Fallback aléatoire
                        return random.uniform(0, 1)

                    # Sélection des meilleures stratégies
                    def select_best(self, scored_population: List[Dict], top_n=20):
                        scored_population.sort(key=lambda x: x['score'], reverse=True)
                        return scored_population[:top_n]

                    # Croisement de deux stratégies
                    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
                        child = {}
                        for key in parent1.keys():
                            child[key] = random.choice([parent1[key], parent2[key]])
                        return child

                    # Mutation aléatoire d'une stratégie
                    def mutate(self, strategy: Dict, mutation_rate=0.1) -> Dict:
                        for key in strategy.keys():
                            if random.random() < mutation_rate:
                                # Remplace par une valeur aléatoire depuis le genome engine
                                if key == 'entry':
                                    strategy[key] = random.choice(self.genome_engine.entry_signals)
                                elif key == 'filter':
                                    strategy[key] = random.choice(self.genome_engine.filters)
                                elif key == 'exit':
                                    strategy[key] = random.choice(self.genome_engine.exit_rules)
                        return strategy

                    # Génération suivante
                    def next_generation(self, top_strategies: List[Dict]) -> List[Dict]:
                        new_population = []
                        while len(new_population) < self.population_size:
                            parent1, parent2 = random.sample(top_strategies, 2)
                            child = self.crossover(parent1, parent2)
                            child = self.mutate(child)
                            new_population.append(child)
                        return new_population

                    # Boucle d'évolution complète
                    def evolve(self, generations=10, top_n=20, save_json=True, visualize=True):
                        perf_history = []
                        for gen in range(generations):
                            scored_population = [{'strategy': s, 'score': self.evaluate_strategy(s)} for s in self.population]
                            scored_population = [{'score': s['score'], **s['strategy']} for s in scored_population]
                            top_strategies = self.select_best(scored_population, top_n=top_n)
                            print(f"Generation {gen+1} top score: {top_strategies[0]['score']:.4f}")
                            perf_history.append(top_strategies[0]['score'])
                            if save_json:
                                with open(f"top_strategies_gen{gen+1}.json", "w", encoding="utf-8") as f:
                                    json.dump(top_strategies, f, indent=2, ensure_ascii=False)
                            self.population = self.next_generation(top_strategies)
                        # Visualisation matplotlib
                        if visualize:
                            plt.figure(figsize=(10,5))
                            plt.plot(perf_history, marker='o')
                            plt.title("Top Score par Génération (Sharpe + Return)")
                            plt.xlabel("Génération")
                            plt.ylabel("Score")
                            plt.grid()
                            plt.show()
                        # Dashboard Panel
                        try:
                            import panel as pn
                            pn.extension('matplotlib')
                            def show_perf():
                                plt.figure(figsize=(10,5))
                                plt.plot(perf_history, marker='o')
                                plt.title("Top Score par Génération (Sharpe + Return)")
                                plt.xlabel("Génération")
                                plt.ylabel("Score")
                                plt.grid()
                                return plt.gcf()
                            dashboard = pn.Column(
                                pn.pane.Markdown("# Evolution Génétique des Stratégies\nSuivi du meilleur score à chaque génération."),
                                pn.pane.Matplotlib(show_perf, tight=True)
                            )
                            dashboard.servable()
                            if __name__ == "__main__":
                                pn.serve(dashboard, port=5028, show=True)
                        except ImportError:
                            pass
                        return self.population

                if __name__ == "__main__":
                    from strategy_genome_engine import StrategyGenomeEngine
                    import numpy as np
                    import pandas as pd
                    # Mock data (à remplacer par vos données réelles)
                    n = 300
                    np.random.seed(42)
                    prices = np.cumsum(np.random.randn(n)) + 100
                    volumes = np.random.normal(1000, 200, n)
                    df = pd.DataFrame({"close": prices, "volume": volumes})
                    genome_engine = StrategyGenomeEngine()
                    evolution_engine = StrategyEvolution(genome_engine, population_size=50, df=df, prices=prices)
                    final_population = evolution_engine.evolve(generations=5, top_n=10)
                    print(final_population[:3])  # affiche les 3 meilleures stratégies finales
