# AI_QUANT_TEAM — Multi-Agent Quant Research Lab

## Agents et rôles

- **ChiefResearchAI** : Orchestrateur, coordonne le cycle complet, analyse les résultats, décide des priorités.
- **MarketAnalystAI** : Analyse la volatilité, trend, volume, liquidité, sentiment.
- **StrategyScientistAI** : Génère de nouvelles stratégies (mutation, crossover, feature discovery).
- **BacktestEngineerAI** : Teste les stratégies sur données historiques ou synthétiques.
- **RiskAnalystAI** : Analyse les risques (crash, sur-optimisation, clusters, etc.).
- **PortfolioManagerAI** : Optimise l'allocation du capital et la diversification.
- **ExecutionTraderAI** : Exécute les ordres en optimisant le slippage et la latence.

## Cycle de recherche

1. MarketAnalystAI → 2. ChiefResearchAI → 3. StrategyScientistAI → 4. BacktestEngineerAI → 5. RiskAnalystAI → 6. PortfolioManagerAI → 7. ExecutionTraderAI → ChiefResearchAI

Chaque agent est une classe Python indépendante dans ce dossier.

---

Prochaine étape : intégrer ces agents dans un pipeline de recherche automatisé (voir ChiefResearchAI pour l'orchestration).
