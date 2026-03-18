# Architecture ULTIME – AI Quant Strategy Lab

```
                    ┌─────────────────────┐
                    │   Market Data Hub   │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │ Feature Engineering │
                    └─────────┬───────────┘
                              │
               ┌──────────────▼──────────────┐
               │ Strategy Discovery Engine   │
               └──────────────┬──────────────┘
                              │
               ┌──────────────▼──────────────┐
               │ Strategy Evolution Engine   │
               └──────────────┬──────────────┘
                              │
                 ┌────────────▼────────────┐
                 │ Massive Backtesting Lab │
                 └────────────┬────────────┘
                              │
                     ┌────────▼────────┐
                     │ Strategy Score  │
                     └────────┬────────┘
                              │
                ┌─────────────▼─────────────┐
                │ Strategy Database (Alpha) │
                └─────────────┬─────────────┘
                              │
               ┌──────────────▼──────────────┐
               │ Portfolio Allocation Engine │
               └──────────────┬──────────────┘
                              │
                 ┌────────────▼────────────┐
                 │ Execution / Sniper Bot  │
                 └────────────┬────────────┘
                              │
       ┌───────────────┬───────────────┬───────────────┐
       ▼               ▼               ▼
 Dashboard        Telegram Bot     Alert System
```

## Description des modules

- **Market Data Hub** : collecte toutes les données de marché (prix, volume, orderbook, funding, liquidations, whale, social).
- **Feature Engineering** : transforme les données en signaux mathématiques (100+ features).
- **Strategy Discovery Engine** : génère automatiquement des stratégies (momentum, mean reversion, arbitrage, etc).
- **Strategy Evolution Engine** : améliore les stratégies par mutation, combinaison, sélection (algorithme génétique).
- **Massive Backtesting Lab** : teste massivement les stratégies sur 10 ans, 1000 stratégies, 10 marchés.
- **Strategy Score Engine** : score chaque stratégie selon Sharpe, winrate, drawdown, etc.
- **Strategy Database (Alpha Vault)** : base de données des stratégies, permet amélioration, recombinaison, réutilisation.
- **Portfolio Allocation Engine** : alloue le capital selon performance, risque, regime.
- **Execution / Sniper Bot** : exécute les trades (paper/live), gère slippage, frais, position sizing.
- **Memecoin Hunter** : détecte les nouveaux tokens, hype, wallets, volume.
- **Market Regime Detection** : détecte bull/bear/sideways/high vol, adapte les stratégies.
- **Social Alpha Engine** : analyse Twitter, Reddit, Telegram pour signaux sociaux.
- **Monitoring & Control** : dashboard web, bot Telegram, alertes multi-canal.

## Orchestration
- pipeline_ultime.py orchestre chaque étape, injecte AlertManager, supervise tout le flux.
- Chaque module est testable, remplaçable, extensible.

## Extension
- Modules avancés (memecoin, social, regime) activables à la demande.
- Prêt pour CI/CD, monitoring, et déploiement cloud.
