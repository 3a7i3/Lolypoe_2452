"""
Test d'intégration automatisé pour l'architecture AI HEDGE FUND SYSTEM.
Ce test vérifie que chaque module principal peut être instancié et appelé sans erreur.
"""

import importlib
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MODULES = [
    ('data_layer', [
        'data_engine', 'data_cleaner', 'data_validator', 'market_microstructure',
        'orderbook_engine', 'data_lake', 'historical_data_store'
    ]),
    ('research_lab', [
        'research_ai', 'pattern_discovery', 'feature_discovery', 'hypothesis_engine',
        'market_behavior_models', 'research_memory'
    ]),
    ('strategy_ecosystem', [
        'strategy_dna', 'strategy_farm', 'strategy_evolution', 'hybrid_strategy_builder',
        'strategy_registry', 'strategy_scoring'
    ]),
    ('simulation_lab', [
        'synthetic_market_generator', 'crash_simulator', 'whale_manipulation_simulator',
        'liquidity_crisis_simulator', 'regime_simulator', 'scenario_runner'
    ]),
    ('risk_intelligence', [
        'bot_doctor', 'risk_engine', 'systemic_risk_monitor', 'crash_research_lab',
        'liquidation_risk_engine', 'stress_testing_engine'
    ]),
    ('portfolio_ai', [
        'portfolio_engine', 'capital_allocator', 'regime_adaptive_allocator',
        'diversification_engine', 'drawdown_control'
    ]),
    ('execution_system', [
        'paper_trading', 'live_trading', 'smart_order_router', 'slippage_monitor',
        'latency_tracker', 'trade_logger'
    ]),
    ('market_intelligence', [
        'market_regime_ai', 'sentiment_analyzer', 'macro_monitor', 'correlation_engine',
        'anomaly_detector'
    ]),
    ('supervision', [
        'director_dashboard', 'monitoring_system', 'strategy_reports', 'research_reports',
        'alert_system'
    ]),
    ('infrastructure', [
        'compute_cluster', 'distributed_backtesting', 'experiment_tracker', 'model_storage',
        'data_lake'
    ]),
]

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_module_imports():
    errors = []
    for block, modules in MODULES:
        for mod in modules:
            module_path = f"AI_HEDGE_FUND_SYSTEM.{block}.{mod}"
            try:
                m = importlib.import_module(module_path)
                class_name = ''.join([part.capitalize() for part in mod.split('_')])
                cls = getattr(m, class_name)
                instance = cls()
                print(f"[OK] {module_path}.{class_name}")
            except Exception as e:
                print(f"[FAIL] {module_path}: {e}")
                errors.append((module_path, str(e)))
    assert not errors, f"Des modules n'ont pas pu être importés ou instanciés: {errors}"

if __name__ == "__main__":
    test_module_imports()
    print("\nTest d'intégration: tous les modules principaux sont accessibles et instanciables.")
