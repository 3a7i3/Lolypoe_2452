class RiskAgent:
    def filter(self, strategies):
        print("[RiskAgent] Filtering strategies...")
        safe = []
        for s in strategies:
            if s.get("drawdown", 0) < 0.25:
                safe.append(s)
        print(f"  [RiskAgent] {len(safe)} strategies passed risk filter.")
        return safe
