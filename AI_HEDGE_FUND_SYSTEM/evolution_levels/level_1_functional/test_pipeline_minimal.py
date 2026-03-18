# Test unitaire du pipeline minimal — Niveau 1
from pipeline_minimal import run_pipeline

def test_pipeline():
    try:
        run_pipeline()
        print("[TEST] Pipeline minimal: OK")
    except Exception as e:
        print("[TEST] Pipeline minimal: FAIL", e)
        raise

if __name__ == "__main__":
    test_pipeline()
