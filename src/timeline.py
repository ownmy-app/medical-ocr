from __future__ import annotations
from typing import List, Tuple
from dataclasses import asdict
from datetime import datetime
import re

from models import OCRRecord, TimelineEvent, SummaryArtifacts
from utils import normalize_ocr, parse_date
from classify import guess_doc_type
from sections import extract_soap_sections, extract_radiology, extract_labs, extract_surgery, extract_physician_letter
from entities import (
find_provider, find_facility, extract_icd, extract_cpt, extract_meds, extract_body_parts,
extract_restrictions, detect_mmi, detect_impairment, extract_future_needs, extract_causation
)
from qc import compute_gaps, find_inconsistent_histories, detect_referenced_missing

def build_timeline(records: List[OCRRecord]) -> Tuple[List[TimelineEvent], SummaryArtifacts]:
    events: List[TimelineEvent] = []
    artifacts = SummaryArtifacts()
    history_sections = []
    all_texts = []

    for rec in records:
        raw = normalize_ocr(rec.text or "")
        all_texts.append(raw)

        dtype = rec.doc_type or guess_doc_type(raw)
        provider = find_provider(raw)
        facility = find_facility(raw)
        icds = extract_icd(raw)
        cpts = extract_cpt(raw)
        meds = extract_meds(raw)
        parts = extract_body_parts(raw)
        restrictions = extract_restrictions(raw)
        if restrictions:
            artifacts.last_restrictions = restrictions[-1]

        mmi = detect_mmi(raw)
        if mmi: 
            artifacts.mmi_found = mmi
        imp = detect_impairment(raw)
        if imp: 
            artifacts.impairment_found = imp

        fneeds = extract_future_needs(raw)
        artifacts.future_needs_snippets.extend(fneeds)

        caus = extract_causation(raw)
        artifacts.causation_statements.extend(caus)

        title = dtype
        plan = None
        diagnoses: List[str] = []

        if dtype == "Clinic/Progress Note (SOAP)":
            soap = extract_soap_sections(raw)
            if soap.get("subjective"):
                history_sections.append(soap["subjective"])
            plan = soap.get("plan") or ""
            if soap.get("assessment"):
                di = re.split(r"[;\\n]", soap["assessment"])
                diagnoses = [d.strip(" -:") for d in di if d.strip()][:6]
        elif dtype == "Radiology Report":
            r = extract_radiology(raw)
            title = r.get("exam", "") or "Radiology Report"
            # Impression/Conclusion first for plan
            plan = r.get("impression","") or r.get("conclusion","") or r.get("assessment","")
            if r.get("impression"):
                diagnoses = [ln.strip(" -*.") for ln in r["impression"].splitlines() if ln.strip()][:6]
        elif dtype == "Laboratory Report":
            L = extract_labs(raw)
            plan = "Abnormal labs flagged: " + "; ".join(L["abnormal_lines"][:6]) if L["abnormal_lines"] else ""
        elif dtype == "Operative/Procedure Note":
            s = extract_surgery(raw)
            proc = s.get("procedure") or "Unspecified"
            title = f"Procedure: {proc}"
            plan = s.get("plan", "")
            if s.get("postop_dx"):
                diagnoses = [s["postop_dx"]]
        elif dtype == "Physician Letter":
            pl = extract_physician_letter(raw)
            plan = pl.get("summary", "")[:600]
            title = "Physician Letter"
        else:
            # general heuristic
            m_dx = re.search(r"\\bdiagnos(?:is|es)\\b[:\\-]\\s*(.*)", raw, re.IGNORECASE)
            if m_dx:
                diagnoses = [m_dx.group(1).strip().split("\\n")[0][:200]]
            m_plan = re.search(r"\\bplan\\b[:\\-]\\s*(.*)", raw, re.IGNORECASE)
            if m_plan:
                plan = m_plan.group(1).strip().split("\\n")[0][:400]

        ev = TimelineEvent(
            date=parse_date(rec.date),
            title=title,
            doc_type=dtype,
            provider=provider,
            facility=facility,
            body_parts=parts,
            diagnoses=diagnoses[:6],
            icd_codes=icds[:12],
            cpt_codes=cpts[:12],
            meds=meds[:12],
            plan=(plan or "")[:1000],
            restrictions=restrictions[:6],
            raw_excerpt=" ".join(raw.split()[:160]),
        )
        events.append(ev)

    # Sort
    events.sort(key=lambda e: (e.date or datetime.min))

    # Artifacts
    if events and events[-1].date:
        artifacts.last_visit = events[-1].date.strftime("%Y-%m-%d")

    # QC passes
    artifacts.gaps_in_care_days = compute_gaps(events)
    artifacts.inconsistent_histories = find_inconsistent_histories(history_sections)
    artifacts.referenced_missing_records = detect_referenced_missing(all_texts)

    # Dedup lists
    artifacts.future_needs_snippets = sorted(set(artifacts.future_needs_snippets))[:20]
    artifacts.causation_statements = sorted(set(artifacts.causation_statements))[:20]

    return events, artifacts