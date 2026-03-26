from __future__ import annotations
import re
from .config import RAD_IMPRESSION_HINTS, PROCEDURE_HINTS, LAB_HDR_HINTS, PHYS_LETTER_HINTS, SOAP_HEADINGS

def guess_doc_type(text: str) -> str:
    t = text.lower()
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in RAD_IMPRESSION_HINTS):
        return "Radiology Report"
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in PROCEDURE_HINTS):
        return "Operative/Procedure Note"
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in LAB_HDR_HINTS):
        return "Laboratory Report"
    if "therapy" in t or "physical therapy" in t or "occupational therapy" in t or "chiropractic" in t or "speech" in t:
        return "Therapy Note"
    if "emergency department" in t or "ed course" in t or "triage" in t:
        return "Emergency Dept Note"
    if "discharge summary" in t or ("admission date" in t and "discharge date" in t):
        return "Admission/Discharge Summary"
    if any(re.search(h, t, re.IGNORECASE | re.MULTILINE) for h in PHYS_LETTER_HINTS):
        return "Physician Letter"
    # SOAP-like structure?
    if re.search(SOAP_HEADINGS["subjective"], t, re.MULTILINE):
        return "Clinic/Progress Note (SOAP)"
    return "General Medical Record"