from __future__ import annotations
import re
from .config import RAD_IMPRESSION_HINTS, PROCEDURE_HINTS, LAB_HDR_HINTS, PHYS_LETTER_HINTS, SOAP_HEADINGS

def guess_doc_type(text: str) -> str:
    t = text.lower()

    # Physician letters -- check early since they may mention therapy/surgery
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in PHYS_LETTER_HINTS):
        return "Physician Letter"

    # Emergency dept -- check before radiology since ED notes mention imaging
    if "emergency department" in t or "ed course" in t or "triage" in t:
        return "Emergency Dept Note"

    # Therapy notes -- check before SOAP since therapy notes often use SOAP structure
    therapy_markers = [
        "therapy note", "therapy progress", "therapy evaluation",
        "pt eval", "treatment session", "therapeutic exercise",
        "neuromuscular re-education", "manual therapy",
        "physical therapy progress",
    ]
    if any(m in t for m in therapy_markers):
        return "Therapy Note"

    # Check SOAP -- SOAP notes often contain "assessment" which
    # would falsely trigger the radiology classifier
    has_soap = (
        re.search(r"(?:^|\n)\s*subjective\s*[:\-]", t, re.MULTILINE)
        or re.search(r"(?:^|\n)\s*objective\s*[:\-]", t, re.MULTILINE)
    )
    if has_soap and re.search(r"(?:^|\n)\s*(?:assessment|plan)\s*[:\-]", t, re.MULTILINE):
        return "Clinic/Progress Note (SOAP)"

    # Radiology -- require radiology-specific context, not just "impression"
    rad_specific = [
        r"\bradiology\b", r"\bimaging\b", r"\bx[- ]?ray\b", r"\bmri\b",
        r"\bct\s+(?:scan|cervical|lumbar|thoracic|head|abdomen)\b",
        r"\bultrasound\b", r"\bfluoroscopy\b", r"\bfindings\b.*\bimpression\b",
        r"\bexam\b.*\b(?:technique|indication)\b",
        r"\bradiology\s+report\b",
    ]
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in rad_specific):
        # Confirm with impression/conclusion section
        if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in RAD_IMPRESSION_HINTS):
            return "Radiology Report"

    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in PROCEDURE_HINTS):
        return "Operative/Procedure Note"
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in LAB_HDR_HINTS):
        return "Laboratory Report"

    if "discharge summary" in t or ("admission date" in t and "discharge date" in t):
        return "Admission/Discharge Summary"

    return "General Medical Record"