import pandas as pd
import numpy as np
from AI_HEDGE_FUND_SYSTEM.feature_discovery.feature_lab import FeatureLab
from AI_HEDGE_FUND_SYSTEM.alpha_mining.alpha_generator import AlphaGenerator
from AI_HEDGE_FUND_SYSTEM.alpha_mining.alpha_cluster import AlphaCluster
from AI_HEDGE_FUND_SYSTEM.alpha_mining.alpha_ranker import AlphaRanker
import matplotlib.pyplot as plt
from AI_HEDGE_FUND_SYSTEM.strategy_generator import StrategyGenerator

# Ajout import pour l'optimisation
from AI_HEDGE_FUND_SYSTEM.hyperparameter_optimizer import HyperparameterOptimizer

# Génère des données simulées (ou chargez vos données réelles ici)
def generate_fake_data():
    data = {
        'close': pd.Series([100 + i + (i%5)*2 + np.random.normal(0, 1) for i in range(300)])
    }
    return pd.DataFrame(data)

def test_full_pipeline():
    df = generate_fake_data()
    print('Étape 1 : Feature Discovery...')
    features = FeatureLab().run(df)
    print(f"{len(features)} features générées.")
    # Convertit en DataFrame pour mining
    features_df = pd.DataFrame({k: v for k, v in features.items()})
    returns = df['close'].pct_change().shift(-1)
    print('Étape 2 : Alpha Mining...')
    cluster = AlphaCluster()
    mining_results = cluster.mine(features_df, returns)
    print(f"{len(mining_results)} signaux testés.")
    # Classement
    ranked = AlphaRanker().rank(mining_results)
    print('Top 5 signaux :')
    for name, score in ranked[:5]:
        print(f"{name}: {score:.4f}")
    # Visualisation
    names = [name for name, _ in ranked[:10]]
    scores = [score for _, score in ranked[:10]]
    plt.figure(figsize=(8,4))
    plt.bar(names, scores, color='purple')
    plt.title('Top 10 alpha signals (corrélation)')
    plt.ylabel('Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('feature_discovery_alpha_mining_top10.png', dpi=120)
    plt.show()

    # Génération automatique de stratégies
    print('\nÉtape 3 : Génération automatique de stratégies...')
    generator = StrategyGenerator(min_score=0.05, max_strat=3)
    strategies = generator.generate(features_df, returns, df)
    for strat in strategies:
        print(f"\nStratégie: {strat['name']}")
        print(f"Score: {strat['score']:.4f}")
        print(f"Stats: {strat['stats']}")
        plt.figure(figsize=(7,4))
        plt.plot(strat['equity'], label='Equity Curve')
        plt.title(f"Equity Curve - {strat['name']}")
        plt.xlabel('Index')
        plt.ylabel('Equity')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'strategy_equity_{strat['name']}.png', dpi=120)
        plt.show()

    # Étape 4 : Optimisation automatique des hyperparamètres avec Optuna
    print('\nÉtape 4 : Optimisation automatique des hyperparamètres (Optuna)...')
    param_space = {'min_score': (0.01, 0.2), 'max_strat': (1, 5)}
    optimizer = HyperparameterOptimizer(StrategyGenerator, n_trials=15, maximize_metric='sharpe')
    best_params, best_value, study = optimizer.optimize(features_df, returns, df, param_space)
    print(f"Meilleurs paramètres trouvés : {best_params}")
    print(f"Meilleur score (Sharpe) : {best_value}")
    # Affiche l'évolution de l'optimisation
    try:
        import optuna.visualization as vis
        fig = vis.plot_optimization_history(study)
        fig.show()
    except Exception as e:
        print(f"Visualisation Optuna non disponible : {e}")

    # Étape 5 : Génération de rapports détaillés (PDF/Markdown/HTML)
    print('\nÉtape 5 : Génération de rapports détaillés...')
    from AI_HEDGE_FUND_SYSTEM.supervision.strategy_reports import StrategyReports
    reporter = StrategyReports()
    # Génère les trois formats pour démonstration
    for fmt in ["pdf", "md", "html"]:
        print(f"Génération du rapport au format {fmt}...")
        reporter.generate(strategies, output_dir="reports", fmt=fmt)
    print("Rapports générés dans le dossier 'reports'.")

if __name__ == '__main__':
    test_full_pipeline()
