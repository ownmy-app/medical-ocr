"""
Benchmark: processing speed.

Measures how fast the extraction pipeline processes text (no OCR, just
entity extraction + classification + timeline building).
"""
import sys
import os
import time
import statistics
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmarks.synthetic_documents import ALL_DOCUMENTS
from medical_ocr.entities import extract_entities
from medical_ocr.classify import guess_doc_type
from medical_ocr.models import OCRRecord
from medical_ocr.timeline import build_timeline


def benchmark_entity_extraction_speed(iterations: int = 100) -> Dict[str, Any]:
    """Benchmark entity extraction speed across all documents."""
    results = {}
    for doc_name, generator in ALL_DOCUMENTS.items():
        text, _ = generator()
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            extract_entities(text)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)

        results[doc_name] = {
            "mean_ms": round(statistics.mean(times), 3),
            "median_ms": round(statistics.median(times), 3),
            "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "iterations": iterations,
        }
    return results


def benchmark_classification_speed(iterations: int = 100) -> Dict[str, Any]:
    """Benchmark document classification speed."""
    results = {}
    for doc_name, generator in ALL_DOCUMENTS.items():
        text, _ = generator()
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            guess_doc_type(text)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        results[doc_name] = {
            "mean_ms": round(statistics.mean(times), 3),
            "median_ms": round(statistics.median(times), 3),
            "iterations": iterations,
        }
    return results


def benchmark_timeline_speed(iterations: int = 50) -> Dict[str, Any]:
    """Benchmark timeline building speed with multiple documents."""
    all_texts = []
    for _, generator in ALL_DOCUMENTS.items():
        text, _ = generator()
        all_texts.append(text)

    records = [
        OCRRecord(text=t, date="2024-03-15", source=f"doc_{i}")
        for i, t in enumerate(all_texts)
    ]

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        build_timeline(records)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    return {
        "num_records": len(records),
        "mean_ms": round(statistics.mean(times), 3),
        "median_ms": round(statistics.median(times), 3),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 3),
        "iterations": iterations,
    }


def run_speed_benchmarks() -> Dict[str, Any]:
    """Run all speed benchmarks."""
    print("Running entity extraction speed benchmark...")
    entity_results = benchmark_entity_extraction_speed()

    print("Running classification speed benchmark...")
    class_results = benchmark_classification_speed()

    print("Running timeline building speed benchmark...")
    timeline_results = benchmark_timeline_speed()

    return {
        "entity_extraction": entity_results,
        "classification": class_results,
        "timeline_building": timeline_results,
    }


def print_speed_results(results: Dict[str, Any]):
    """Pretty-print speed benchmark results."""
    print("=" * 70)
    print("MEDICAL-OCR PROCESSING SPEED BENCHMARKS")
    print("=" * 70)

    print("\n--- Entity Extraction (per document) ---")
    print(f"{'Document':<25} {'Mean':>10} {'Median':>10} {'P95':>10}")
    print("-" * 55)
    for name, r in results["entity_extraction"].items():
        print(f"{name:<25} {r['mean_ms']:>8.2f}ms {r['median_ms']:>8.2f}ms {r['p95_ms']:>8.2f}ms")

    print("\n--- Document Classification (per document) ---")
    print(f"{'Document':<25} {'Mean':>10} {'Median':>10}")
    print("-" * 45)
    for name, r in results["classification"].items():
        print(f"{name:<25} {r['mean_ms']:>8.2f}ms {r['median_ms']:>8.2f}ms")

    print("\n--- Timeline Building ({} records) ---".format(
        results["timeline_building"]["num_records"]))
    t = results["timeline_building"]
    print(f"  Mean: {t['mean_ms']:.2f}ms, Median: {t['median_ms']:.2f}ms, P95: {t['p95_ms']:.2f}ms")


if __name__ == "__main__":
    results = run_speed_benchmarks()
    print_speed_results(results)
