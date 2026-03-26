from __future__ import annotations
from typing import List, Dict, Any
from dataclasses import asdict
from .models import OCRRecord
from .timeline import build_timeline
from .summary import craft_summary, attorney_faq

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