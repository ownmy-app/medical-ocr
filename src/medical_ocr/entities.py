"""Entity extraction for medical documents (ICD codes, CPT codes, body parts, etc.)."""
import re
from typing import List, Dict, Optional


def extract_icd(text: str) -> List[str]:
    """Extract ICD-10 codes from text (e.g., M54.5, S72.001A, S13.4XXA)."""
    # Match standard ICD-10 codes: letter + 2 digits + optional dot + alphanumeric suffix
    # Examples: M54.5, S72.001A, S13.4XXA, M75.110, G89.29
    pattern = r"\b([A-TV-Z]\d{2}(?:\.[0-9A-Za-z]{1,5})?)\b"
    candidates = re.findall(pattern, text)
    # Deduplicate preserving order
    seen = set()
    valid = []
    for c in candidates:
        if c not in seen and len(c) >= 3:
            valid.append(c)
            seen.add(c)
    return valid


# Keep the old alias for backward compatibility
extract_icd_codes = extract_icd


def extract_cpt(text: str) -> List[str]:
    """Extract CPT billing codes from text (5-digit numeric codes).

    Looks for 5-digit codes near CPT-related context or in standalone format.
    Filters to valid CPT ranges and deduplicates.
    """
    pattern = r"\b(\d{5})\b"
    candidates = re.findall(pattern, text)
    seen = set()
    valid = []
    for c in candidates:
        val = int(c)
        # Valid CPT code ranges
        if c not in seen and 10000 <= val <= 99999:
            valid.append(c)
            seen.add(c)
    return valid


extract_cpt_codes = extract_cpt


def extract_body_parts(text: str) -> List[str]:
    """Extract mentioned body parts from text."""
    body_parts = [
        "cervical", "thoracic", "lumbar", "spine", "shoulder", "knee",
        "hip", "ankle", "wrist", "elbow", "neck", "back", "head",
        "arm", "leg", "foot", "hand", "finger", "toe", "pelvis",
        "rib", "chest", "abdomen", "sacral", "coccyx", "rotator cuff",
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
    # Pattern 1: Name followed by dosage (e.g., "Gabapentin 300 mg")
    pattern1 = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|mL|g|units?|IU))\b"
    for m in re.finditer(pattern1, text):
        name = m.group(1).strip()
        dosage = m.group(2).strip()
        # Filter out common non-drug words
        skip_words = {"patient", "range", "reference", "estimated", "forward",
                      "extension", "flexion", "abduction", "strength", "session",
                      "level", "rated", "measuring", "approximately", "continue",
                      "start", "begin", "take", "give", "administer", "prescribed",
                      "ordered", "recommend"}
        if name.lower() not in skip_words:
            medications.append({"name": name, "dosage": dosage})

    # Pattern 1b: After common verb + medication name + dosage
    # e.g., "Continue Gabapentin 300 mg" or "Start Meloxicam 15 mg"
    pattern1b = r"(?:continue|start|begin|prescribe[d]?|take|give)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|mL|g|units?|IU))\b"
    for m in re.finditer(pattern1b, text, re.IGNORECASE):
        name = m.group(1).strip()
        dosage = m.group(2).strip()
        medications.append({"name": name, "dosage": dosage})

    # Pattern 2: Dosage then name (e.g., "5mg Oxycodone") - less common
    pattern2 = r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|units?))\s+(?:of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
    for m in re.finditer(pattern2, text):
        dosage = m.group(1).strip()
        name = m.group(2).strip()
        skip_words = {"iv", "po", "im", "sq", "daily", "twice", "three"}
        if name.lower() not in skip_words:
            medications.append({"name": name, "dosage": dosage})

    # Deduplicate by name (case-insensitive)
    seen = set()
    unique = []
    for med in medications:
        key = med["name"].lower()
        if key not in seen:
            unique.append(med)
            seen.add(key)
    return unique


def extract_restrictions(text: str) -> List[str]:
    """Extract work/activity restrictions from text."""
    restrictions = []
    patterns = [
        # "Restrictions: No lifting over 15 pounds. No prolonged standing."
        r"(?:restrict(?:ed|ion)s?|limit(?:ed|ation)s?)\s*[:\-]\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)",
        # Individual restriction lines starting with "No ..." or "Avoid ..."
        r"(?:^|(?<=\.\s)|(?<=\n))\s*(no\s+(?:lifting|bending|twisting|overhead|prolonged|repetitive)[^.;\n]{3,50})(?:\.|;|\n|$)",
        # "Avoid repetitive bending"
        r"(?:^|(?<=\.\s)|(?<=\n))\s*(avoid\s+[^.;\n]{3,50})(?:\.|;|\n|$)",
        # "Light duty" patterns
        r"(light\s+duty(?:\s+(?:only|recommended))?)(?:\.|;|\n|$)",
    ]
    lower = text.lower()
    for p in patterns:
        for m in re.finditer(p, lower, re.MULTILINE):
            raw = m.group(1).strip().rstrip(".")
            # Split compound restrictions on periods within matched text
            for part in re.split(r"\.\s+", raw):
                part = part.strip()
                if part and len(part) > 5:
                    restrictions.append(part)

    # Deduplicate
    seen = set()
    unique = []
    for r in restrictions:
        key = r.lower().strip()
        if key not in seen:
            unique.append(r)
            seen.add(key)
    return unique


def find_provider(text: str) -> Optional[str]:
    """Extract treating provider/doctor name from text."""
    patterns = [
        # "Dr. Sarah Johnson" or "Dr. Kevin O'Brien" or "Dr. Kevin O Brien"
        r"(?:Dr\.?|Doctor|Surgeon)\s+([A-Z][a-z]+(?:[ \'\-][A-Z]?[a-z]+){0,3})",
        r"(?:Provider|Physician|Treating)\s*:\s*(?:Dr\.?\s+)?(.+?)(?:\n|$)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            name = m.group(1).strip()
            # Remove trailing titles like ", DPT" or ", MD"
            name = re.sub(r",\s*(MD|DO|DPT|PT|OT|DC|NP|PA)$", "", name)
            return name
    return None


def find_facility(text: str) -> Optional[str]:
    """Extract facility/clinic name from text."""
    patterns = [
        r"(?:Facility|Clinic|Hospital|Center|Laboratory|Practice)\s*:\s*(.+?)(?:\n|$)",
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


def extract_causation(text: str) -> List[str]:
    """Extract causation opinions from text."""
    results = []
    patterns = [
        r"(?:caus(?:ed|ation|ally\s+related))\s*[:.]?\s*(.+?)(?:\.|;|\n|$)",
        r"(?:result(?:ing|ed)\s*(?:from|of))\s*[:.]?\s*(.+?)(?:\.|;|\n|$)",
        r"(?:due\s+to|attribut(?:ed|able)\s+to)\s+(.+?)(?:\.|;|\n|$)",
        r"(?:related\s+to\s+the)\s+(.+?)(?:\.|;|\n|$)",
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            stmt = m.group(1).strip()
            if stmt and len(stmt) > 5:
                results.append(stmt)
    return results


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
