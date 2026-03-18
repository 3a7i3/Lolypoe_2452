# Test unitaire du pipeline IA — Niveau 3
from pipeline_ai import run_ai_pipeline

def test_ai_pipeline():
    try:
        run_ai_pipeline()
        print("[TEST] Pipeline IA: OK")
    except Exception as e:
        print("[TEST] Pipeline IA: FAIL", e)
        raise

if __name__ == "__main__":
    test_ai_pipeline()
