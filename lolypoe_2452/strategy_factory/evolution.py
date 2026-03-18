import random

class Evolution:
    def evolve(self, strategies, scores):
        ranked = list(zip(strategies,scores))
        ranked.sort(key=lambda x:x[1], reverse=True)
        survivors = [s for s,_ in ranked[:20]]
        children = []
        for s in survivors:
            child = s.copy()
            if random.random() < 0.3:
                child["threshold"] *= random.uniform(0.9,1.1)
            children.append(child)
        return survivors + children
