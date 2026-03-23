from __future__ import annotations
import re
from typing import List, Tuple
from datetime import datetime
from models import TimelineEvent, SummaryArtifacts

def compute_gaps(events: List[TimelineEvent]) -> List[int]:
    dates = [e.date for e in events if e.date]
    gaps = []
    for a, b in zip(dates, dates[1:]):
        gaps.append((b - a).days)
    return gaps

def find_inconsistent_histories(history_sections: List[str]) -> List[str]:
    mech_hits = []
    for s in history_sections:
        ctx = re.findall(r"(?:injur(?:y|ed)|accident|fall|collision|MVC|work|gym|sports|assault).{0,80}", s, re.IGNORECASE)
        if ctx:
            mech_hits.append(" ... ".join(ctx))
    # naive divergence heuristic
    uniq = set(mech_hits)
    if len(uniq) > 3:
        return list(uniq)[:6]
    return []

def detect_referenced_missing(records_texts: List[str]) -> List[str]:
# If text mentions a specific test (e.g., MRI 05/05/24) but doc type timeline has no such exam.
    mentions = []
    for t in records_texts:
        for m in re.finditer(r"\b(MRI|CT|X-?ray|Ultrasound|EMG|NCV|EEG)\b.*?(\d{1,2}/\d{1,2}/\d{2,4})?", t, re.IGNORECASE):
            frag = m.group(0)
            mentions.append(frag[:120])
    # This function only lists mentions; caller should cross-check against actual events.
    uniq = []
    seen = set()
    for m in mentions:
        k = m.lower()
        if k not in seen:
            uniq.append(m)
            seen.add(k)
    return uniq[:20]