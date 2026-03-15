import subprocess
import os

def find_all_tests(root_dir):
    test_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.startswith("test_") and fname.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(dirpath, fname), root_dir)
                test_files.append(rel_path)
    return test_files

LAB_ROOT = os.path.dirname(__file__)
all_tests = find_all_tests(LAB_ROOT)

for rel_path in all_tests:
    test_path = os.path.join(LAB_ROOT, rel_path)
    print(f"\n=== Running {rel_path} ===")
    try:
        result = subprocess.run(["python", test_path], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("[stderr]", result.stderr)
    except Exception as e:
        print(f"Error running {rel_path}: {e}")
