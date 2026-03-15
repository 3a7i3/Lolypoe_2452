# Synthetic Market Simulation Lab

Ce dossier contient un pipeline complet pour simuler des marchés financiers synthétiques avec différents régimes, manipulations, crises de liquidité et crashs.

## Modules principaux
- `market_generator.py` : Génère une série de prix de base (GBM).
- `regime_simulator.py` : Définit les paramètres de régimes (bull, bear, sideways).
- `whale_manipulation.py` : Simule des manipulations de type pump & dump.
- `liquidity_simulator.py` : Simule des crises de liquidité.
- `crash_simulator.py` : Injecte des crashs de marché.
- `scenario_runner.py` : Orchestration complète d'un scénario.
- `test_synthetic_market.py` : Test batch, génère un marché, sauvegarde la courbe de prix.

## Utilisation rapide

```bash
python -m synthetic_market.test_synthetic_market
```

- Génère un marché bull avec manipulations, crise de liquidité et crash.
- Sauvegarde la courbe de prix sous `synthetic_market_bull.png`.

## Améliorations possibles
- Ajouter des tests pour les autres régimes (`bear`, `sideways`).
- Ajouter des métriques de volatilité, drawdown, etc.
- Générer des scénarios multiples pour analyse statistique.
