from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from .models import OCRRecord
from .timeline import build_timeline
from .summary import craft_summary, attorney_faq


def _calculate_page_confidence(page_text: str) -> float:
    """
    Estimate per-page OCR confidence from text characteristics.

    When Tesseract confidence data is not directly available in the pipeline
    records, we use heuristics: word length distribution, non-alpha ratio,
    and dictionary-word ratio as a proxy for OCR quality.
    """
    if not page_text or not page_text.strip():
        return 0.0

    words = page_text.split()
    if not words:
        return 0.0

    score = 0.0

    # Factor 1: ratio of reasonably-sized words (3+ chars, alpha)
    complete_words = sum(1 for w in words if len(w) >= 3 and w.isalpha())
    word_ratio = complete_words / len(words) if words else 0
    score += word_ratio * 0.4

    # Factor 2: non-garbage character ratio
    alpha_chars = sum(1 for c in page_text if c.isalpha() or c.isspace())
    char_ratio = alpha_chars / max(len(page_text), 1)
    score += char_ratio * 0.3

    # Factor 3: average word length (very short = likely garbled)
    avg_len = sum(len(w) for w in words) / len(words)
    if avg_len >= 4:
        score += 0.2
    elif avg_len >= 2:
        score += 0.1

    # Factor 4: text length (very short pages are less reliable)
    if len(page_text) >= 200:
        score += 0.1
    elif len(page_text) >= 50:
        score += 0.05

    return min(round(score, 4), 1.0)


def _calculate_document_confidence(
    page_confidences: List[float],
) -> float:
    """Average of per-page confidence scores."""
    if not page_confidences:
        return 0.0
    return round(sum(page_confidences) / len(page_confidences), 4)


def generate_summary(ocr_records: List[Dict[str, Any]], target_chars: int = 2000) -> Dict[str, Any]:
    records = []
    for i, r in enumerate(ocr_records):
        records.append(OCRRecord(
        text=r.get("text","") or "",
        date=r.get("date"),
        source=r.get("source"),
        doc_type=r.get("doc_type"),
        doc_id=r.get("doc_id") or f"doc_{i+1}"
        ))
    timeline, artifacts = build_timeline(records)
    summary_text = craft_summary(timeline, artifacts, max_chars=target_chars)
    metrics = {
        "num_records": len(records),
        "num_events": len(timeline),
        "num_radiology": sum(1 for e in timeline if e.doc_type == "Radiology Report"),
        "num_procedures": sum(1 for e in timeline if e.doc_type == "Operative/Procedure Note"),
        "num_labs": sum(1 for e in timeline if e.doc_type == "Laboratory Report"),
    }

    faq = attorney_faq(timeline, artifacts)

    # Convert dates to strings for JSON safety
    timeline_out = []
    for e in timeline:
        d = asdict(e)
        d["date"] = e.date.strftime("%Y-%m-%d") if e.date else None
        timeline_out.append(d)

    return {
        "summary_text": summary_text,
        "timeline": timeline_out,
        "metrics": metrics,
        "artifacts": asdict(artifacts),
        "faq": faq
    }


def generate_summary_with_confidence(
    ocr_records: List[Dict[str, Any]],
    target_chars: int = 2000,
    page_metrics: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Same as generate_summary but adds confidence scoring to the output.

    If *page_metrics* is provided (from extractor.OCR metadata), the
    per-page Tesseract/engine confidence is used directly.  Otherwise,
    heuristic confidence is calculated from the text content.

    Returns the standard summary dict plus a ``confidence`` key:
    {
        ...standard fields...,
        "confidence": {
            "overall": 0.85,
            "per_record": [
                {"record_index": 0, "source": "page_1.pdf", "confidence": 0.87},
                ...
            ]
        }
    }
    """
    # Build the standard summary first
    result = generate_summary(ocr_records, target_chars=target_chars)

    # Compute per-record confidence
    per_record_confidence: List[Dict[str, Any]] = []
    page_conf_values: List[float] = []

    for i, r in enumerate(ocr_records):
        text = r.get("text", "") or ""
        source = r.get("source") or f"record_{i + 1}"

        # Prefer engine-reported confidence from page_metrics
        conf: Optional[float] = None
        if page_metrics:
            # Try matching by page number (keys are "1", "2", ...)
            pm = page_metrics.get(str(i + 1))
            if pm:
                conf = pm.get("confidence")

        if conf is None:
            conf = _calculate_page_confidence(text)

        conf = round(conf, 4)
        page_conf_values.append(conf)
        per_record_confidence.append({
            "record_index": i,
            "source": source,
            "confidence": conf,
        })

    overall = _calculate_document_confidence(page_conf_values)

    result["confidence"] = {
        "overall": overall,
        "per_record": per_record_confidence,
    }

    return result