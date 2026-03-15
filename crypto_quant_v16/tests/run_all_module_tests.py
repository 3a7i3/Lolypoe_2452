import pytest

def run_tests():
    print("🚀 Running all module tests...")
    pytest.main(["tests/"])
    print("✅ All tests executed!")

if __name__ == "__main__":
    run_tests()
