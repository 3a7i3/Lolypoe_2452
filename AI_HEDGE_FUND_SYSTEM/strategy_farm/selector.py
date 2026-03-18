class StrategySelector:
    def select(self, strategies, scores, top=10, min_winrate=0.3):
        # Remove duplicates (by string representation)
        seen = set()
        filtered = []
        for s, score in zip(strategies, scores):
            key = str(s)
            if key not in seen:
                seen.add(key)
                filtered.append((s, score))
        # Sort by score
        ranked = sorted(filtered, key=lambda x: x[1], reverse=True)
        # Optionally filter by winrate if present
        selected = []
        for s, score in ranked:
            # If winrate is encoded in score, skip; else, always select
            selected.append(s)
            if len(selected) >= top:
                break
        return selected
