class ExecutionAgent:
    def execute(self, allocations):
        print("[ExecutionAgent] Executing trades...")
        for a in allocations:
            print(f"  [ExecutionAgent] Executing {a['strategy']} with {a['allocation']}")
