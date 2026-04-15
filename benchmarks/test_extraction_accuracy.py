"""
Benchmark: field extraction accuracy.

Tests the entity extraction functions directly against synthetic text
with known ground truth. Measures precision and recall for each field type.
No OCR/tesseract/GPU needed -- tests regex extraction only.
"""
import sys
import os
import time
import json
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmarks.synthetic_documents import ALL_DOCUMENTS, GroundTruth
from medical_ocr.entities import (
    extract_icd, extract_cpt, extract_meds, extract_body_parts,
    find_provider, find_facility, extract_restrictions,
    detect_mmi, detect_impairment, extract_future_needs, extract_causation,
)
from medical_ocr.classify import guess_doc_type


def precision_recall(expected: list, extracted: list) -> Dict[str, float]:
    """Compute precision, recall, F1 for two lists (case-insensitive)."""
    if not expected and not extracted:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}

    expected_lower = {str(e).lower().strip() for e in expected}
    extracted_lower = {str(e).lower().strip() for e in extracted}

    tp = len(expected_lower & extracted_lower)
    fp = len(extracted_lower - expected_lower)
    fn = len(expected_lower - extracted_lower)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "tp": tp, "fp": fp, "fn": fn}


def benchmark_icd_extraction(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_icd(text)
    return precision_recall(gt.icd_codes, extracted)


def benchmark_cpt_extraction(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_cpt(text)
    return precision_recall(gt.cpt_codes, extracted)


def benchmark_medication_extraction(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_meds(text)
    extracted_names = [m["name"].lower() for m in extracted]
    expected_names = [m["name"].lower() for m in gt.medications]
    return precision_recall(expected_names, extracted_names)


def benchmark_body_parts(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_body_parts(text)
    return precision_recall(gt.body_parts, extracted)


def benchmark_provider(text: str, gt: GroundTruth) -> Dict:
    extracted = find_provider(text)
    if gt.provider is None:
        return {"match": extracted is None, "expected": None, "extracted": extracted}
    if extracted and gt.provider.lower() in extracted.lower():
        return {"match": True, "expected": gt.provider, "extracted": extracted}
    return {"match": False, "expected": gt.provider, "extracted": extracted}


def benchmark_facility(text: str, gt: GroundTruth) -> Dict:
    extracted = find_facility(text)
    if gt.facility is None:
        return {"match": extracted is None, "expected": None, "extracted": extracted}
    if extracted and gt.facility.lower() in extracted.lower():
        return {"match": True, "expected": gt.facility, "extracted": extracted}
    return {"match": False, "expected": gt.facility, "extracted": extracted}


def benchmark_restrictions(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_restrictions(text)
    return precision_recall(gt.restrictions, extracted)


def benchmark_mmi(text: str, gt: GroundTruth) -> Dict:
    detected = detect_mmi(text)
    return {"match": detected == gt.mmi, "expected": gt.mmi, "detected": detected}


def benchmark_impairment(text: str, gt: GroundTruth) -> Dict:
    detected = detect_impairment(text)
    if gt.impairment is None:
        return {"match": detected is None, "expected": None, "detected": detected}
    if detected and gt.impairment in detected:
        return {"match": True, "expected": gt.impairment, "detected": detected}
    return {"match": False, "expected": gt.impairment, "detected": detected}


def benchmark_doc_type(text: str, gt: GroundTruth) -> Dict:
    detected = guess_doc_type(text)
    return {"match": detected == gt.doc_type, "expected": gt.doc_type, "detected": detected}


def benchmark_future_needs(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_future_needs(text)
    # Fuzzy match: check if any expected need substring is in any extracted string
    if not gt.future_needs:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}
    matches = 0
    for expected in gt.future_needs:
        for ext in extracted:
            if expected.lower() in ext.lower() or ext.lower() in expected.lower():
                matches += 1
                break
    recall = matches / len(gt.future_needs) if gt.future_needs else 1.0
    precision = matches / len(extracted) if extracted else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def benchmark_causation(text: str, gt: GroundTruth) -> Dict:
    extracted = extract_causation(text)
    if gt.causation is None:
        is_empty = not extracted or (isinstance(extracted, list) and len(extracted) == 0)
        return {"match": is_empty, "expected": None, "extracted": extracted}
    # Check if any extracted causation statement contains the expected text
    if isinstance(extracted, list):
        for stmt in extracted:
            if gt.causation.lower() in stmt.lower() or stmt.lower() in gt.causation.lower():
                return {"match": True, "expected": gt.causation, "extracted": extracted}
    elif extracted and gt.causation.lower() in str(extracted).lower():
        return {"match": True, "expected": gt.causation, "extracted": extracted}
    return {"match": False, "expected": gt.causation, "extracted": extracted}


def run_all_benchmarks() -> Dict[str, Any]:
    """Run all extraction benchmarks across all synthetic documents."""
    results = {}
    aggregate = {
        "icd_codes": {"total_tp": 0, "total_fp": 0, "total_fn": 0},
        "cpt_codes": {"total_tp": 0, "total_fp": 0, "total_fn": 0},
        "medications": {"total_tp": 0, "total_fp": 0, "total_fn": 0},
        "body_parts": {"total_tp": 0, "total_fp": 0, "total_fn": 0},
        "restrictions": {"total_tp": 0, "total_fp": 0, "total_fn": 0},
        "provider": {"correct": 0, "total": 0},
        "facility": {"correct": 0, "total": 0},
        "mmi": {"correct": 0, "total": 0},
        "impairment": {"correct": 0, "total": 0},
        "doc_type": {"correct": 0, "total": 0},
        "causation": {"correct": 0, "total": 0},
    }

    overall_start = time.time()

    for doc_name, generator in ALL_DOCUMENTS.items():
        text, gt = generator()
        start = time.time()

        doc_results = {
            "icd_codes": benchmark_icd_extraction(text, gt),
            "cpt_codes": benchmark_cpt_extraction(text, gt),
            "medications": benchmark_medication_extraction(text, gt),
            "body_parts": benchmark_body_parts(text, gt),
            "provider": benchmark_provider(text, gt),
            "facility": benchmark_facility(text, gt),
            "restrictions": benchmark_restrictions(text, gt),
            "mmi": benchmark_mmi(text, gt),
            "impairment": benchmark_impairment(text, gt),
            "doc_type": benchmark_doc_type(text, gt),
            "future_needs": benchmark_future_needs(text, gt),
            "causation": benchmark_causation(text, gt),
            "processing_time_ms": round((time.time() - start) * 1000, 2),
        }
        results[doc_name] = doc_results

        # Aggregate precision/recall fields
        for field_name in ["icd_codes", "cpt_codes", "medications", "body_parts", "restrictions"]:
            r = doc_results[field_name]
            aggregate[field_name]["total_tp"] += r.get("tp", 0)
            aggregate[field_name]["total_fp"] += r.get("fp", 0)
            aggregate[field_name]["total_fn"] += r.get("fn", 0)

        # Aggregate match fields
        for field_name in ["provider", "facility", "mmi", "impairment", "doc_type", "causation"]:
            r = doc_results[field_name]
            aggregate[field_name]["total"] += 1
            if r.get("match", False):
                aggregate[field_name]["correct"] += 1

    # Compute aggregate precision/recall
    summary = {}
    for field_name in ["icd_codes", "cpt_codes", "medications", "body_parts", "restrictions"]:
        a = aggregate[field_name]
        tp, fp, fn = a["total_tp"], a["total_fp"], a["total_fn"]
        p = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        summary[field_name] = {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}

    for field_name in ["provider", "facility", "mmi", "impairment", "doc_type", "causation"]:
        a = aggregate[field_name]
        acc = a["correct"] / a["total"] if a["total"] > 0 else 0.0
        summary[field_name] = {"accuracy": round(acc, 4), "correct": a["correct"], "total": a["total"]}

    total_time = round((time.time() - overall_start) * 1000, 2)
    summary["total_processing_time_ms"] = total_time
    summary["documents_tested"] = len(ALL_DOCUMENTS)

    return {"per_document": results, "summary": summary}


def print_results(results: Dict[str, Any]):
    """Pretty-print benchmark results."""
    summary = results["summary"]

    print("=" * 70)
    print("MEDICAL-OCR EXTRACTION BENCHMARK RESULTS")
    print("=" * 70)
    print(f"Documents tested: {summary['documents_tested']}")
    print(f"Total processing time: {summary['total_processing_time_ms']}ms")
    print()

    print("--- Precision/Recall Fields ---")
    print(f"{'Field':<20} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 50)
    for field_name in ["icd_codes", "cpt_codes", "medications", "body_parts", "restrictions"]:
        s = summary[field_name]
        print(f"{field_name:<20} {s['precision']:>10.1%} {s['recall']:>10.1%} {s['f1']:>10.1%}")

    print()
    print("--- Accuracy Fields ---")
    print(f"{'Field':<20} {'Accuracy':>10} {'Correct':>10} {'Total':>10}")
    print("-" * 50)
    for field_name in ["provider", "facility", "mmi", "impairment", "doc_type", "causation"]:
        s = summary[field_name]
        print(f"{field_name:<20} {s['accuracy']:>10.1%} {s['correct']:>10} {s['total']:>10}")

    print()
    print("--- Per-Document Details ---")
    for doc_name, doc_results in results["per_document"].items():
        print(f"\n  {doc_name}:")
        for field_name in ["icd_codes", "cpt_codes", "medications", "body_parts", "restrictions"]:
            r = doc_results[field_name]
            status = "PASS" if r["f1"] >= 0.8 else ("PARTIAL" if r["f1"] > 0 else "FAIL")
            if r["tp"] == 0 and r["fp"] == 0 and r["fn"] == 0:
                status = "N/A"
            print(f"    {field_name:<18} P={r['precision']:.0%} R={r['recall']:.0%} F1={r['f1']:.0%} [{status}]")
        for field_name in ["provider", "facility", "mmi", "impairment", "doc_type"]:
            r = doc_results[field_name]
            status = "PASS" if r.get("match") else "FAIL"
            exp = r.get("expected", "")
            det = r.get("extracted", r.get("detected", ""))
            print(f"    {field_name:<18} {status} (expected={exp}, got={det})")


if __name__ == "__main__":
    results = run_all_benchmarks()
    print_results(results)
    # Save JSON results
    out_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")
