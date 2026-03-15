import unittest
import os
import sys

TESTS_DIR = os.path.join(os.path.dirname(__file__), 'tests')

if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover(TESTS_DIR)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\n====================")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {len(result.successes) if hasattr(result, 'successes') else 'N/A'}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("====================\n")
    if result.failures or result.errors:
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()
