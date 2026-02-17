#!/usr/bin/env python
"""Run all UAT tests sequentially."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from manual_test_runner import ManualTestRunner


def main() -> None:
    """Run all UAT tests in sequence."""
    spec_path = Path("tests/manual/manual_tests.json")
    output_dir = Path("tests/manual/results")
    
    runner = ManualTestRunner(spec_path, output_dir)
    tests = runner.load_tests()
    
    # Filter to UAT tests only
    uat_tests = [t for t in tests if t.test_id.startswith("uat_")]
    
    if not uat_tests:
        print("No UAT tests found.")
        return
    
    print(f"\n{'='*70}")
    print(f"Running {len(uat_tests)} UAT tests")
    print(f"{'='*70}\n")
    
    for i, test in enumerate(uat_tests, start=1):
        print(f"\n[{i}/{len(uat_tests)}] {test.title}")
        print(f"Test ID: {test.test_id}")
        try:
            runner.run(test)
        except KeyboardInterrupt:
            print(f"\n\nTest interrupted by user at {test.title}")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}\")\n")
    
    print(f"\n{'='*70}")
    print(f"All {len(uat_tests)} UAT tests completed")
    print(f"Results saved to: {output_dir} (from your current working directory)\")\n\"")
    print(f\"{'='*70}\")\n")


if __name__ == \"__main__\":
    main()
