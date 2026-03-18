# Niveau 2 — Organisme évolutif

## Objectif
Le système s'améliore seul grâce à l'évolution génétique : mutation, crossover, sélection multi-générations.

## Pipeline
```
generate → test → select → mutate → new generation
```

## Modules clés
- EvolutionEngine (mutation, crossover, sélection)
- Walk-forward testing

## Améliorations
- Génération de plusieurs générations de stratégies
- Sélection des meilleurs
- Mutation/crossover pour créer la nouvelle génération
- Walk-forward testing pour éviter l'overfitting

## Prochaines étapes
- Scaffold EvolutionEngine
- Pipeline évolutif minimal
- Test unitaire du cycle évolutif
