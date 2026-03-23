from __future__ import annotations
import re
from typing import Dict, Any, List
from config import SOAP_HEADINGS

def extract_soap_sections(text: str) -> Dict[str, str]:
    sections = {"subjective": "", "objective": "", "assessment": "", "plan": ""}
    lines = text.splitlines()
    current = None
    for line in lines:
        hit = None
        for key, pat in SOAP_HEADINGS.items():
            if re.search(pat, line, re.IGNORECASE):
                hit = key
                current = key
                sections[key] += re.sub(pat, "", line, flags=re.IGNORECASE).strip() + "\n"
                break
        if hit is None and current:
            sections[current] += line.strip() + "\n"
    for k in sections:
        sections[k] = sections[k].strip()
    return sections

def extract_radiology(text: str) -> Dict[str, str]:
    blocks = {}
    def block_after(label: str) -> str:
        pat = re.compile(rf"^\s*{label}\s*[:\-]\s*(.)$", re.IGNORECASE | re.MULTILINE)
        m = pat.search(text)
        if not m:
            return ""
        start = m.end()
        nxt = re.search(r"^\s[A-Z][A-Z ]{2,}[:\-]", text[start:], re.MULTILINE)
        return text[start:start + (nxt.start() if nxt else len(text[start:]))].strip()
    for lbl in ["Exam", "Technique", "Indication", "History", "Comparison", "Findings", "Impression", "Conclusion", "Assessment", "Opinion", "Follow-up"]:
        content = block_after(lbl) or block_after(lbl.upper())
        if content:
            blocks[lbl.lower()] = content
    return blocks

def extract_labs(text: str) -> Dict[str, Any]:
    abnormals = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if re.search(r"\b(H|L|high|low|abnormal|critical|panic|\u2191|\u2193)\b", ln, re.IGNORECASE):
            abnormals.append(ln)
        elif re.search(r"\b(\*|!|#)\b", ln) and re.search(r"\d", ln):
            abnormals.append(ln)
    return {"abnormal_lines": abnormals[:100]}

def extract_surgery(text: str) -> Dict[str, str]:
    def get_field(keys: List[str]) -> str:
        for k in keys:
            m = re.search(rf"{k}\s*[:\-]\s*(.*)", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""
    return {
    "procedure": get_field(["Procedure", "Operation", "Surgery"]),
    "indication": get_field(["Indication", "Clinical History", "History"]),
    "preop_dx": get_field(["Pre-operative Diagnosis", "Preop Diagnosis", "Preoperative Diagnosis"]),
    "postop_dx": get_field(["Post-operative Diagnosis", "Postop Diagnosis", "Postoperative Diagnosis"]),
    "anesthesia": get_field(["Anesthesia"]),
    "blood_loss": get_field(["Blood Loss", "EBL"]),
    "complications": get_field(["Complications"]),
    "findings": get_field(["Findings", "Impression"]),
    "implants": get_field(["Implants"]),
    "plan": get_field(["Plan", "Post-operative Plan"]),
}

def extract_physician_letter(text: str) -> Dict[str, str]:
    to_m = re.search(r"^\sTo\s:\s*(.)$", text, re.IGNORECASE | re.MULTILINE)
    subj_m = re.search(r"^\sRe\s*:\s*(.*)$", text, re.IGNORECASE | re.MULTILINE)
    return {
    "to": to_m.group(1).strip() if to_m else "",
    "re": subj_m.group(1).strip() if subj_m else "",
    "summary": " ".join(text.splitlines()[:120])[:2400],
    }