#!/usr/bin/env python3
"""Test runner for FoodLens AI backend.

Runs all test suites in sequence.
"""

import subprocess
import sys
import os

TESTS = [
    "tests/test_services.py",
    "tests/test_endpoints.py",
    "tests/test_report_translate.py",
]


def main():
    print("=" * 60)
    print("FoodLens AI Backend Test Runner")
    print("=" * 60)

    # Check if server is running for endpoint tests
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8000/api/health", timeout=2)
        server_running = True
    except Exception:
        server_running = False

    if not server_running:
        print("\n⚠️  Backend server not running on http://localhost:8000")
        print("   Start it with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("   Service tests will run, but endpoint tests will be skipped.\n")
        TESTS.remove("tests/test_endpoints.py")
        TESTS.remove("tests/test_report_translate.py")

    all_passed = True
    for test_file in TESTS:
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print("=" * 60)
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode != 0:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
