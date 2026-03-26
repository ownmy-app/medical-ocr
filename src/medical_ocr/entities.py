"""Entity extraction for medical documents (ICD codes, CPT codes, body parts, etc.)."""
import re
from typing import List, Dict, Optional


def extract_icd(text: str) -> List[str]:
    """Extract ICD-10 codes from text (e.g., M54.5, S72.001A)."""
    pattern = r"\b[A-TV-Z]\d{2}(?:\.\d{1,4})?[A-Z]?\b"
    return list(set(re.findall(pattern, text)))


# Keep the old alias for backward compatibility
extract_icd_codes = extract_icd


def extract_cpt(text: str) -> List[str]:
    """Extract CPT billing codes from text (5-digit numeric codes)."""
    pattern = r"\b\d{5}\b"
    candidates = re.findall(pattern, text)
    return [c for c in candidates if 10000 <= int(c) <= 99999]


extract_cpt_codes = extract_cpt


def extract_body_parts(text: str) -> List[str]:
    """Extract mentioned body parts from text."""
    body_parts = [
        "cervical", "thoracic", "lumbar", "spine", "shoulder", "knee",
        "hip", "ankle", "wrist", "elbow", "neck", "back", "head",
        "arm", "leg", "foot", "hand",
    ]
    found = []
    lower = text.lower()
    for bp in body_parts:
        if bp in lower:
            found.append(bp)
    return found


def extract_meds(text: str) -> List[Dict[str, Optional[str]]]:
    """Extract medication names, dosages, and frequencies from text."""
    medications = []
    pattern = r"([A-Za-z]+(?:\s[A-Za-z]+)?)\s+(\d+\s*(?:mg|mcg|ml|g|units?))"
    for m in re.finditer(pattern, text, re.IGNORECASE):
        medications.append({"name": m.group(1).strip(), "dosage": m.group(2).strip()})
    return medications


def extract_restrictions(text: str) -> List[str]:
    """Extract work/activity restrictions from text."""
    restrictions = []
    patterns = [
        r"(?:restrict(?:ed|ion)s?|limit(?:ed|ation)s?)\s*:\s*(.+?)(?:\n|$)",
        r"(?:no|avoid|cannot|should not)\s+(.+?)(?:\.|;|\n|$)",
    ]
    lower = text.lower()
    for p in patterns:
        for m in re.finditer(p, lower):
            restrictions.append(m.group(1).strip())
    return restrictions


def find_provider(text: str) -> Optional[str]:
    """Extract treating provider/doctor name from text."""
    patterns = [
        r"(?:Dr\.?|Doctor)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        r"(?:Provider|Physician|Treating)\s*:\s*(.+?)(?:\n|$)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None


def find_facility(text: str) -> Optional[str]:
    """Extract facility/clinic name from text."""
    patterns = [
        r"(?:Facility|Clinic|Hospital|Center)\s*:\s*(.+?)(?:\n|$)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def detect_mmi(text: str) -> Optional[bool]:
    """Detect Maximum Medical Improvement status."""
    lower = text.lower()
    if "maximum medical improvement" in lower or "mmi" in lower:
        if "reached" in lower or "has reached" in lower or "at mmi" in lower:
            return True
        if "not reached" in lower or "has not reached" in lower:
            return False
    return None


def detect_impairment(text: str) -> Optional[str]:
    """Extract impairment rating if present."""
    pattern = r"(\d+)\s*%?\s*(?:whole\s*person|impairment|wpi)"
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}%"
    return None


def extract_future_needs(text: str) -> List[str]:
    """Extract future medical care needs from text."""
    needs = []
    patterns = [
        r"(?:recommend(?:ed|ation)s?|future\s*(?:care|treatment|needs?))\s*:\s*(.+?)(?:\n|$)",
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            needs.append(m.group(1).strip())
    return needs


def extract_causation(text: str) -> Optional[str]:
    """Extract causation opinion from text."""
    patterns = [
        r"(?:caus(?:ed|ation)|result(?:ing|ed)\s*(?:from|of))\s*[:.]?\s*(.+?)(?:\.|;|\n|$)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extract_entities(text: str) -> Dict:
    """Extract all medical entities from text."""
    return {
        "icd_codes": extract_icd(text),
        "cpt_codes": extract_cpt(text),
        "body_parts": extract_body_parts(text),
        "medications": extract_meds(text),
        "restrictions": extract_restrictions(text),
        "provider": find_provider(text),
        "facility": find_facility(text),
        "mmi": detect_mmi(text),
        "impairment": detect_impairment(text),
        "future_needs": extract_future_needs(text),
        "causation": extract_causation(text),
    }
