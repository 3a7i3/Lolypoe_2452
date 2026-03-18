# Pipeline Autonomous AI Quant Lab

```
┌─────────────────────────────┐
│       Data Engine           │
│  (Collecte prix, volume,    │
│   orderbook, funding rates) │
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│   Feature Engineering       │
│  (momentum, volatility,     │
│   orderbook imbalance, etc) │
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│ Strategy Discovery Engine   │
│  (génération + scoring      │
│   stratégies)               │
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│ Strategy Evolution Engine   │
│  (amélioration génétique)  │
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│ Bot Doctor                  │
│  (validation stratégies)    │
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│ Portfolio & Risk Engine     │
│  (allocation capital,       │
│   drawdown, taille position)│
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│ Execution Engine / Sniper   │
│  (paper/live trading,       │
│   slippage, frais)          │
└─────────────┬──────────────┘
			  │
┌─────────────▼──────────────┐
│ Dashboard Web / API         │
│ Telegram Bot                │
│ Alert Manager               │
└────────────────────────────┘
```

### Description du pipeline

1. **Data Engine** : collecte toutes les données de marché nécessaires (prix, volume, orderbook, funding).
2. **Feature Engineering** : calcule les indicateurs avancés (momentum, volatilité, etc).
3. **Strategy Discovery** : génère et score des stratégies candidates.
4. **Strategy Evolution** : améliore les stratégies par évolution génétique.
5. **Bot Doctor** : valide la robustesse et la conformité des stratégies.
6. **Portfolio & Risk Engine** : alloue le capital, gère le risque, applique les règles de drawdown.
7. **Execution Engine / Sniper** : exécute les ordres en mode paper ou live, gère le slippage et les frais.
8. **Dashboard / API / Telegram / AlertManager** : monitoring, alertes, supervision temps réel.

Voir `pipeline_autonome.py` pour l’orchestration complète.
# Architecture – AI Quant Lab V4

## Vue d’ensemble
- **ai/** : analyse avancée, stratégie, évolution
- **memecoin_alpha/** : détection memecoin, rug, sniper
- **core/** : execution_engine, portefeuille, risk
- **supervision/** : alert_manager, dashboard, telegram, API
- **tests/** : tests unitaires

## Orchestration
- AlertManager centralise toutes les alertes (Telegram, logs, web)
- Dashboard web (Streamlit) et API REST (FastAPI) pour monitoring
- Bot Telegram pour alertes et commandes
- Exécution configurable (paper/live, slippage, frais)

## Sécurité
- Credentials dans `config/credentials.env` (jamais versionnés)
- Chargement via python-dotenv

## Extensibilité
- Modules indépendants, testables, remplaçables
- Ajout facile de nouvelles stratégies, canaux d’alerte, endpoints API
