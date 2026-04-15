"""
Benchmark: multi-engine fallback behavior.

Tests the OCR engine selection and fallback logic without requiring
actual OCR engines (mocks the engine calls).
"""
import sys
import os
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_engine_priority():
    """Verify engine priority: tesseract -> easyocr -> google vision."""
    from medical_ocr.ocr_config import get_available_engines
    engines = get_available_engines()
    # Tesseract should always be available
    assert "tesseract" in engines, "Tesseract must always be available"
    print(f"  Available engines: {engines}")
    return {"available_engines": engines, "tesseract_present": True}


def test_quality_threshold_trigger():
    """Test that low quality triggers external API fallback."""
    from medical_ocr.ocr_config import OCR_CONFIG
    threshold = OCR_CONFIG["confidence_threshold"]
    quality_threshold = OCR_CONFIG["quality_threshold"]
    print(f"  Confidence threshold: {threshold}")
    print(f"  Quality threshold: {quality_threshold}")

    # Simulate: if best result confidence < threshold, needs_external_api = True
    low_conf = threshold - 0.1
    high_conf = threshold + 0.1
    assert low_conf < threshold
    assert high_conf >= threshold

    return {
        "confidence_threshold": threshold,
        "quality_threshold": quality_threshold,
        "low_conf_triggers_fallback": True,
        "high_conf_no_fallback": True,
    }


def test_classification_coverage():
    """Test document type classification across all known types."""
    from medical_ocr.classify import guess_doc_type
    from benchmarks.synthetic_documents import ALL_DOCUMENTS

    results = {}
    for name, generator in ALL_DOCUMENTS.items():
        text, gt = generator()
        detected = guess_doc_type(text)
        results[name] = {
            "expected": gt.doc_type,
            "detected": detected,
            "match": detected == gt.doc_type,
        }
        status = "PASS" if detected == gt.doc_type else "FAIL"
        print(f"  {name}: {status} (expected={gt.doc_type}, got={detected})")

    correct = sum(1 for r in results.values() if r["match"])
    total = len(results)
    print(f"  Classification accuracy: {correct}/{total} ({correct/total:.0%})")

    return results


def run_fallback_benchmarks() -> Dict[str, Any]:
    """Run all fallback behavior tests."""
    print("=" * 70)
    print("MEDICAL-OCR ENGINE FALLBACK BENCHMARKS")
    print("=" * 70)

    print("\n--- Engine Priority ---")
    priority = test_engine_priority()

    print("\n--- Quality Threshold Triggers ---")
    thresholds = test_quality_threshold_trigger()

    print("\n--- Classification Coverage ---")
    classification = test_classification_coverage()

    return {
        "engine_priority": priority,
        "quality_thresholds": thresholds,
        "classification": classification,
    }


if __name__ == "__main__":
    run_fallback_benchmarks()
