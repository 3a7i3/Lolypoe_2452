import subprocess
import sys
import os

# Always run from project root
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Discover and run all tests with pytest if available, else fallback to unittest

def main():
    try:
        import pytest
        print("[INFO] Lancement des tests avec pytest...")
        code = subprocess.call([sys.executable, '-m', 'pytest'])
        sys.exit(code)
    except ImportError:
        print("[WARN] pytest non installé, fallback sur unittest...")
        # Découverte manuelle des tests en excluant supervision.dashboard et supervision.notifications
        import unittest
        loader = unittest.TestLoader()
        # Exclure explicitement les modules problématiques
        all_tests = loader.discover('.', pattern='test*.py')
        suite = unittest.TestSuite()
        for test_group in all_tests:
            for test_case in test_group:
                # Filtrer les cas de test par nom de module
                if not any(
                    skip in str(test_case)
                    for skip in ['supervision.dashboard', 'supervision.notifications']
                ):
                    suite.addTest(test_case)
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
