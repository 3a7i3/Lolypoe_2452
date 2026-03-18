# Test unitaire du pipeline évolutif — Niveau 2
from pipeline_evolutif import run_evolution_pipeline

def test_evolution_pipeline():
    try:
        run_evolution_pipeline()
        print("[TEST] Pipeline évolutif: OK")
    except Exception as e:
        print("[TEST] Pipeline évolutif: FAIL", e)
        raise

if __name__ == "__main__":
    test_evolution_pipeline()
