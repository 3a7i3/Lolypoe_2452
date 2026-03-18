import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
MasterCoordinator = None  # Test désactivé : module absent
ResearchNode = None  # Test désactivé : module absent
AlphaVault = None  # Test désactivé : module absent
BacktestingLab = None  # Test désactivé : module absent

def test_supercluster():
    nodes = [ResearchNode() for _ in range(3)]
    master = MasterCoordinator(nodes)
    df = {"close": [1,2,3,4,5,6,7,8,9,10]}  # Dummy data
    results = master.distribute_research(df)
    print("Total strategies found:", len(results))
    # Backtest all strategies
    backtester = BacktestingLab()
    backtested = backtester.evaluate(results, df)
    # Store in alpha vault
    vault = AlphaVault()
    for s in backtested:
        vault.store(s["strategy_id"], s)
    best = vault.get_best(2)
    print("Top strategies:")
    for sid, stats in best:
        print(f"  {sid}: score={stats['score']} sharpe={stats['sharpe']} drawdown={stats['drawdown']}")
        assert len(results) == 300, f"Expected 300 strategies, got {len(results)}"
    assert len(best) == 2
    print("Test passed: Supercluster pipeline runs.")

    # --- Persistence ---
    AlphaVaultPersistence = None  # Test désactivé : module absent
    persistence = AlphaVaultPersistence("alpha_vault_test.json")
    persistence.save(vault.vault)
    loaded = persistence.load()
    assert loaded, "Persistence failed."

    # --- Collective Evolution ---
    CollectiveEvolution = None  # Test désactivé : module absent
    node_strategies = [master.nodes[i].run_research(df) for i in range(3)]
    evolution = CollectiveEvolution()
    new_generation = evolution.evolve(node_strategies)
    assert new_generation, "Collective evolution failed."

    # --- Meta-Learner ---
    MetaLearner = None  # Test désactivé : module absent
    meta = MetaLearner()
    meta_stats = meta.analyze(new_generation)
    assert meta_stats is not None

    # --- Monitoring ---
    MonitoringBrain = None  # Test désactivé : module absent
    monitor = MonitoringBrain()
    sys_stats = monitor.report()
    assert "cpu" in sys_stats and "memory" in sys_stats
    print("Test passed: Persistence, CollectiveEvolution, MetaLearner, Monitoring work.")

    # --- Collective Evolution ---
    CollectiveEvolution = None  # Test désactivé : module absent
    node_strategies = [master.nodes[i].run_research(df) for i in range(3)]
    evolution = CollectiveEvolution()
    new_generation = evolution.evolve(node_strategies)
    assert new_generation, "Collective evolution failed."

    # --- Meta-Learner ---
    MetaLearner = None  # Test désactivé : module absent
    meta = MetaLearner()
    meta_stats = meta.analyze(new_generation)
    assert meta_stats is not None
    print("Test passed: CollectiveEvolution and MetaLearner work.")

if __name__ == "__main__":
    test_supercluster()
