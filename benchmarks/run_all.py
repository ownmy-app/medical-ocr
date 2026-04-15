#!/usr/bin/env python3
"""Run all benchmarks and produce a combined report."""
import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmarks.test_extraction_accuracy import run_all_benchmarks, print_results
from benchmarks.test_processing_speed import run_speed_benchmarks, print_speed_results
from benchmarks.test_engine_fallback import run_fallback_benchmarks


def main():
    print()
    print("#" * 70)
    print("#  MEDICAL-OCR FULL BENCHMARK SUITE")
    print("#" * 70)
    print()

    start = time.time()

    # 1. Extraction accuracy
    print("=" * 70)
    print("SECTION 1: EXTRACTION ACCURACY")
    print("=" * 70)
    accuracy_results = run_all_benchmarks()
    print_results(accuracy_results)

    # 2. Processing speed
    print()
    speed_results = run_speed_benchmarks()
    print_speed_results(speed_results)

    # 3. Engine fallback
    print()
    fallback_results = run_fallback_benchmarks()

    total_time = round(time.time() - start, 2)
    print()
    print("#" * 70)
    print(f"#  ALL BENCHMARKS COMPLETE ({total_time}s)")
    print("#" * 70)

    # Save combined results
    combined = {
        "extraction_accuracy": accuracy_results,
        "processing_speed": speed_results,
        "engine_fallback": fallback_results,
        "total_benchmark_time_s": total_time,
    }
    out_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(combined, f, indent=2, default=str)
    print(f"Combined results saved to {out_path}")


if __name__ == "__main__":
    main()
