import random

class StrategyMutation:
    def mutate(self, strategy):
        strat = strategy.copy()
        # Muter la taille de position
        if "position_size" in strat and random.random() < 0.5:
            strat["position_size"] *= random.uniform(0.95, 1.1)
            strat["position_size"] = min(max(strat["position_size"], 0.01), 1.0)
        # Muter la logique
        if "logic" in strat and random.random() < 0.2:
            strat["logic"] = "AND" if strat["logic"] == "OR" else "OR"
        # Muter les conditions
        if "conditions" in strat:
            conds = [c.copy() for c in strat["conditions"]]
            for c in conds:
                if random.random() < 0.5:
                    c["threshold"] *= random.uniform(0.95, 1.1)
                    c["threshold"] = min(max(c["threshold"], 0.01), 1.0)
                if "operator" in c and random.random() < 0.2:
                    c["operator"] = random.choice([">", "<", ">=", "<="])
            # Ajout/suppression condition
            if random.random() < 0.15 and len(conds) < 4:
                conds.append(random.choice(conds))
            if random.random() < 0.15 and len(conds) > 1:
                conds.pop(random.randint(0, len(conds)-1))
            strat["conditions"] = conds
        return strat
