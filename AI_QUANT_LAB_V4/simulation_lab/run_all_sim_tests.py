import subprocess
import os

TESTS = [
    os.path.join('crash_simulator', 'test_crash_simulator.py'),
    os.path.join('regime_simulator', 'test_regime_simulator.py'),
    os.path.join('liquidity_crisis_simulator', 'test_liquidity_crisis_simulator.py'),
    os.path.join('manipulation_scenarios', 'test_manipulation_scenarios.py'),
    os.path.join('synthetic_market', 'test_synthetic_market.py'),
]

if __name__ == "__main__":
    for test in TESTS:
        print(f"\n=== Running {test} ===")
        result = subprocess.run(["python", test], cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            print(f"[OK] {test}")
        else:
            print(f"[FAIL] {test}")
