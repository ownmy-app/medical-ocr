"""
Specialized vocabulary and patterns for injury-related medical records.
This module contains terms, patterns, and validation logic specific to injury documentation.
"""

from typing import Dict, List, Set, Tuple
import re
from datetime import datetime, timedelta

# Injury-specific medical terminology
INJURY_TYPES = {
    # Bone injuries
    'fracture', 'break', 'broken', 'fx', 'compound fracture', 'simple fracture', 
    'comminuted', 'displaced', 'non-displaced', 'greenstick', 'spiral fracture',
    
    # Soft tissue injuries
    'laceration', 'cut', 'wound', 'puncture', 'abrasion', 'scrape', 'bruise',
    'contusion', 'hematoma', 'swelling', 'edema', 'inflammation',
    
    # Joint/ligament injuries
    'sprain', 'strain', 'dislocation', 'subluxation', 'torn ligament', 'acl tear',
    'mcl tear', 'meniscus tear', 'rotator cuff', 'tennis elbow', 'golfers elbow',
    
    # Head injuries
    'concussion', 'tbi', 'traumatic brain injury', 'skull fracture', 'subdural',
    'epidural', 'intracranial', 'coup', 'contrecoup', 'post-concussion syndrome',
    
    # Spinal injuries
    'herniated disc', 'bulging disc', 'slipped disc', 'pinched nerve', 'sciatica',
    'whiplash', 'cervical strain', 'lumbar strain', 'spondylosis', 'stenosis',
    
    # Burn injuries
    'burn', 'first degree', 'second degree', 'third degree', 'thermal burn',
    'chemical burn', 'electrical burn', 'radiation burn', 'scald'
}

# Body parts commonly injured
BODY_PARTS = {
    # Head/neck
    'head', 'skull', 'brain', 'face', 'jaw', 'mandible', 'maxilla', 'nose', 'eye',
    'neck', 'cervical spine', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7',
    
    # Torso
    'chest', 'ribs', 'sternum', 'clavicle', 'collarbone', 'shoulder', 'scapula',
    'back', 'spine', 'lumbar', 'thoracic', 'l1', 'l2', 'l3', 'l4', 'l5',
    't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 't10', 't11', 't12',
    
    # Arms
    'arm', 'upper arm', 'forearm', 'elbow', 'wrist', 'hand', 'finger', 'thumb',
    'humerus', 'radius', 'ulna', 'metacarpal', 'phalanx', 'phalanges',
    
    # Legs
    'leg', 'thigh', 'knee', 'shin', 'calf', 'ankle', 'foot', 'toe', 'hip',
    'femur', 'tibia', 'fibula', 'patella', 'kneecap', 'achilles', 'heel'
}

# Common injury mechanisms
INJURY_MECHANISMS = {
    'motor vehicle accident', 'mva', 'car accident', 'auto accident', 'collision',
    'fall', 'slip and fall', 'trip and fall', 'fall from height', 'workplace injury',
    'workers compensation', 'workers comp', 'job injury', 'occupational injury',
    'sports injury', 'athletic injury', 'contact sport', 'non-contact injury',
    'assault', 'fight', 'altercation', 'domestic violence', 'gunshot wound', 'gsw',
    'stabbing', 'knife wound', 'blunt force trauma', 'penetrating trauma',
    'bicycle accident', 'motorcycle accident', 'pedestrian struck', 'hit by car'
}

# Medical procedures for injuries
INJURY_PROCEDURES = {
    'surgery', 'surgical repair', 'internal fixation', 'external fixation',
    'reduction', 'closed reduction', 'open reduction', 'orif', 'arthroscopy',
    'debridement', 'irrigation', 'sutures', 'stitches', 'staples', 'bandage',
    'cast', 'splint', 'brace', 'immobilization', 'traction', 'fusion',
    'joint replacement', 'amputation', 'skin graft', 'flap', 'reconstruction'
}

# Medications commonly used for injuries
INJURY_MEDICATIONS = {
    'pain medication', 'analgesic', 'nsaid', 'ibuprofen', 'naproxen', 'aspirin',
    'acetaminophen', 'tylenol', 'morphine', 'oxycodone', 'hydrocodone', 'codeine',
    'tramadol', 'fentanyl', 'lidocaine', 'novocaine', 'cortisone', 'steroid',
    'anti-inflammatory', 'muscle relaxant', 'cyclobenzaprine', 'flexeril',
    'antibiotics', 'tetanus', 'tetanus shot', 'vaccination'
}

# Legal/insurance terms
LEGAL_INSURANCE_TERMS = {
    'insurance claim', 'claim number', 'policy number', 'adjuster', 'liability',
    'premises liability', 'product liability', 'medical malpractice', 'negligence',
    'settlement', 'damages', 'pain and suffering', 'lost wages', 'disability',
    'permanent disability', 'temporary disability', 'return to work', 'light duty',
    'independent medical exam', 'ime', 'functional capacity evaluation', 'fce',
    'maximum medical improvement', 'mmi', 'permanent partial disability', 'ppd'
}

# Diagnostic terms
DIAGNOSTIC_TERMS = {
    'x-ray', 'radiograph', 'ct scan', 'cat scan', 'mri', 'magnetic resonance',
    'ultrasound', 'sonogram', 'bone scan', 'pet scan', 'emg', 'nerve conduction',
    'range of motion', 'rom', 'strength test', 'reflex test', 'sensation test',
    'neurological exam', 'orthopedic exam', 'physical therapy evaluation'
}

# Combine all injury-related terms
ALL_INJURY_TERMS = (
    INJURY_TYPES | BODY_PARTS | INJURY_MECHANISMS | INJURY_PROCEDURES |
    INJURY_MEDICATIONS | LEGAL_INSURANCE_TERMS | DIAGNOSTIC_TERMS
)

# Common injury record patterns
INJURY_PATTERNS = {
    'date_of_injury': [
        r'(?:date of (?:injury|accident|incident))[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'(?:injury date)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'(?:doi)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'
    ],
    'mechanism_of_injury': [
        r'(?:mechanism of injury|moi)[:\s]*(.*?)(?:\n|\.)',
        r'(?:how did (?:the )?injury occur)[:\s?]*(.*?)(?:\n|\.)',
        r'(?:cause of injury)[:\s]*(.*?)(?:\n|\.)'
    ],
    'chief_complaint': [
        r'(?:chief complaint|cc)[:\s]*(.*?)(?:\n|\.)',
        r'(?:presenting complaint)[:\s]*(.*?)(?:\n|\.)',
        r'(?:patient complains of)[:\s]*(.*?)(?:\n|\.)'
    ],
    'pain_scale': [
        r'(?:pain (?:scale|level|score))[:\s]*([0-9]{1,2})/10',
        r'(?:rates pain)[:\s]*([0-9]{1,2})/10',
        r'(?:pain)[:\s]*([0-9]{1,2})/10'
    ]
}

# ICD-10 injury code patterns
ICD10_INJURY_PATTERNS = [
    r'[STW][0-9]{2}\.[0-9]{1,3}[A-Z]?',  # Injury codes start with S, T, or W
    r'[VYZ][0-9]{2}\.[0-9]{1,3}[A-Z]?'   # External cause codes
]

# Common injury abbreviations and their full forms
INJURY_ABBREVIATIONS = {
    'MVA': 'Motor Vehicle Accident',
    'MVC': 'Motor Vehicle Collision', 
    'RTC': 'Road Traffic Collision',
    'TBI': 'Traumatic Brain Injury',
    'SCI': 'Spinal Cord Injury',
    'GSW': 'Gunshot Wound',
    'DOI': 'Date of Injury',
    'MOI': 'Mechanism of Injury',
    'ROM': 'Range of Motion',
    'ORIF': 'Open Reduction Internal Fixation',
    'ACL': 'Anterior Cruciate Ligament',
    'MCL': 'Medial Collateral Ligament',
    'PCL': 'Posterior Cruciate Ligament',
    'LCL': 'Lateral Collateral Ligament',
    'IME': 'Independent Medical Exam',
    'FCE': 'Functional Capacity Evaluation',
    'MMI': 'Maximum Medical Improvement',
    'PPD': 'Permanent Partial Disability',
    'PTD': 'Permanent Total Disability',
    'TTD': 'Temporary Total Disability',
    'TPD': 'Temporary Partial Disability',
    'WC': 'Workers Compensation',
    'LOC': 'Loss of Consciousness',
    'PTSD': 'Post Traumatic Stress Disorder',
    'EMG': 'Electromyography',
    'NCV': 'Nerve Conduction Velocity'
}

def calculate_injury_relevance_score(text: str) -> float:
    """
    Calculate how relevant the text is to injury documentation.
    Returns a score between 0.0 and 1.0.
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count injury-related terms
    injury_term_count = sum(1 for word in words if word in ALL_INJURY_TERMS)
    
    # Bonus for injury patterns
    pattern_bonus = 0
    for pattern_group in INJURY_PATTERNS.values():
        for pattern in pattern_group:
            if re.search(pattern, text_lower, re.IGNORECASE):
                pattern_bonus += 0.1
    
    # Bonus for ICD-10 codes
    icd_bonus = 0
    for pattern in ICD10_INJURY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            icd_bonus += 0.1
    
    # Bonus for abbreviations
    abbrev_bonus = sum(0.05 for abbrev in INJURY_ABBREVIATIONS.keys() 
                      if abbrev.lower() in text_lower)
    
    # Calculate base score
    if len(words) == 0:
        return 0.0
    
    base_score = injury_term_count / len(words)
    total_score = min(base_score + pattern_bonus + icd_bonus + abbrev_bonus, 1.0)
    
    return total_score

def extract_injury_structured_data(text: str) -> Dict[str, str]:
    """
    Extract structured injury data from OCR text.
    """
    extracted_data = {}
    
    # Extract dates
    for pattern in INJURY_PATTERNS['date_of_injury']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['date_of_injury'] = match.group(1)
            break
    
    # Extract mechanism of injury
    for pattern in INJURY_PATTERNS['mechanism_of_injury']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['mechanism_of_injury'] = match.group(1).strip()
            break
    
    # Extract chief complaint
    for pattern in INJURY_PATTERNS['chief_complaint']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['chief_complaint'] = match.group(1).strip()
            break
    
    # Extract pain scale
    for pattern in INJURY_PATTERNS['pain_scale']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data['pain_scale'] = match.group(1)
            break
    
    # Extract ICD-10 codes
    icd_codes = []
    for pattern in ICD10_INJURY_PATTERNS:
        codes = re.findall(pattern, text)
        icd_codes.extend(codes)
    if icd_codes:
        extracted_data['icd_codes'] = list(set(icd_codes))
    
    return extracted_data

def validate_injury_text_quality(text: str) -> Tuple[bool, List[str]]:
    """
    Validate if the extracted text makes sense for an injury record.
    Returns (is_valid, list_of_issues).
    """
    issues = []
    
    if not text or len(text.strip()) < 10:
        issues.append("Text too short for medical record")
        return False, issues
    
    # Check for minimum injury-related content
    relevance_score = calculate_injury_relevance_score(text)
    if relevance_score < 0.1:
        issues.append("Text doesn't appear to be injury-related")
    
    # Check for common OCR errors in medical context
    if re.search(r'[0-9]{10,}', text):  # Very long number sequences
        issues.append("Suspicious long number sequences (possible OCR error)")
    
    # Check for reasonable word/character ratio
    words = text.split()
    if len(words) > 0:
        avg_word_length = len(text) / len(words)
        if avg_word_length > 15 or avg_word_length < 2:
            issues.append("Unusual word length distribution")
    
    # Check for excessive special characters
    special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s\.\,\;\:\-\(\)]', text)) / len(text)
    if special_char_ratio > 0.3:
        issues.append("Too many special characters (possible OCR errors)")
    
    is_valid = len(issues) == 0 or (len(issues) == 1 and "injury-related" in issues[0])
    
    return is_valid, issues

def enhance_injury_ocr_text(text: str) -> str:
    """
    Post-process OCR text specifically for injury documentation.
    """
    if not text:
        return text
    
    # Expand common injury abbreviations
    enhanced_text = text
    for abbrev, full_form in INJURY_ABBREVIATIONS.items():
        # Replace standalone abbreviations
        pattern = r'\b' + re.escape(abbrev) + r'\b'
        enhanced_text = re.sub(pattern, f"{full_form} ({abbrev})", enhanced_text, flags=re.IGNORECASE)
    
    # Fix common injury-specific OCR errors
    injury_corrections = {
        r'\bfx\b': 'fracture',
        r'\bdx\b': 'diagnosis',
        r'\btx\b': 'treatment',
        r'\bsx\b': 'surgery',
        r'\bhx\b': 'history',
        r'\bc/o\b': 'complains of',
        r'\bs/p\b': 'status post',
        r'\bp/w\b': 'presented with',
        r'\bw/\b': 'with',
        r'\bw/o\b': 'without',
        r'\b(\d+)\s*yo\b': r'\1 year old',
        r'\b(\d+)\s*y/o\b': r'\1 year old',
    }
    
    for pattern, replacement in injury_corrections.items():
        enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
    
    # Standardize date formats
    date_patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', r'\1/\2/\3'),  # Standardize to MM/DD/YYYY
    ]
    
    for pattern, replacement in date_patterns:
        enhanced_text = re.sub(pattern, replacement, enhanced_text)
    
    # Clean up extra whitespace
    enhanced_text = re.sub(r'\s+', ' ', enhanced_text)
    enhanced_text = re.sub(r'\n+', '\n', enhanced_text)
    
    return enhanced_text.strip()

def get_injury_context_keywords() -> Set[str]:
    """
    Get all injury-related keywords for context-aware processing.
    """
    return ALL_INJURY_TERMS

def is_injury_medical_record(text: str, threshold: float = 0.15) -> bool:
    """
    Determine if the text appears to be an injury-related medical record.
    """
    relevance_score = calculate_injury_relevance_score(text)
    return relevance_score >= threshold

