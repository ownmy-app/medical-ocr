from __future__ import annotations
from typing import Dict, Any

def to_markdown(result: Dict[str, Any]) -> str:
    s = ["# Medical Summary\n"]
    s.append(result["summary_text"])
    s.append("\n## Chronological Timeline")
    for e in result["timeline"]:
        dt = e.get("date") or "Undated"
        s.append(f"- {dt} — {e['doc_type']}: {e['title']}")
        if e.get("diagnoses"):
            s.append(f" - Dx: {', '.join(e['diagnoses'])}")
        if e.get("icd_codes"):
            s.append(f" - ICD: {', '.join(e['icd_codes'])}")
        if e.get("cpt_codes"):
            s.append(f" - CPT: {', '.join(e['cpt_codes'])}")
        if e.get("restrictions"):
            s.append(f" - Restrictions: {', '.join(e['restrictions'])}")
    return "\n".join(s)