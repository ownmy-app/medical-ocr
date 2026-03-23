"""
Enhanced legal and medical vocabulary for litigation-focused OCR optimization.
Based on analysis of demand letter and medical summary SOPs.
"""

import re
from typing import Set, Dict, List
from .injury_medical_vocabulary import ALL_INJURY_TERMS, INJURY_ABBREVIATIONS

# Legal terminology specific to injury litigation
LEGAL_LITIGATION_TERMS = {
    # Demand letter terms
    'demand letter', 'solicitor letter', 'lawyer letter', 'legal obligation',
    'contractual commitment', 'formal notice', 'deadline for action', 'litigation',
    'legal action', 'pleadings', 'court of law', 'goodwill', 'business parties',
    
    # Settlement and claims
    'settlement', 'claim', 'damages', 'compensation', 'liability', 'negligence',
    'fault', 'responsibility', 'reimbursement', 'payment', 'monetary relief',
    'punitive damages', 'general damages', 'special damages', 'economic losses',
    
    # Legal procedures
    'deposition', 'interrogatories', 'discovery', 'subpoena', 'affidavit',
    'sworn statement', 'testimony', 'witness', 'expert witness', 'evidence',
    'documentation', 'proof', 'burden of proof', 'preponderance', 'standard of care',
    
    # Legal professionals and entities
    'attorney', 'counsel', 'law firm', 'legal representative', 'paralegal',
    'court reporter', 'bailiff', 'clerk', 'judge', 'magistrate', 'mediator',
    'arbitrator', 'opposing counsel', 'defense attorney', 'plaintiff attorney',
    
    # Legal documents
    'complaint', 'summons', 'answer', 'counterclaim', 'cross-claim', 'motion',
    'brief', 'memorandum', 'order', 'judgment', 'verdict', 'decree', 'injunction',
    'restraining order', 'cease and desist', 'notice of intent', 'release',
    
    # Insurance and coverage
    'insurance policy', 'coverage limits', 'deductible', 'premium', 'adjuster',
    'claims adjuster', 'insurance company', 'carrier', 'underwriter', 'insured',
    'policyholder', 'beneficiary', 'exclusion', 'coverage denial', 'bad faith',
}

# Medical documentation terms from litigation context
MEDICAL_LITIGATION_TERMS = {
    # Medical record types mentioned in SOPs
    'medical records', 'medical record', 'emergency medical services', 'ems report',
    'emergency department', 'trauma center', 'intensive care', 'icu',
    'hospitalization', 'consultation', 'evaluation', 'follow-up',
    'progress notes', 'radiological reports', 'laboratory reports', 'lab results',
    'surgical reports', 'procedural reports', 'medication logs', 'prescription logs',
    
    # Medical summary components
    'medical summary', 'summary of injuries', 'initial status', 'current status',
    'maximum medical improvement', 'mmi', 'impairment rating', 'causation statements',
    'pre-existing conditions', 'substance abuse', 'mental health status',
    'vocational history', 'life expectancy factors', 'congenital conditions',
    
    # Medical professionals
    'attending physician', 'treating physician', 'consulting physician',
    'radiologist', 'pathologist', 'surgeon', 'specialist', 'primary care physician',
    'emergency physician', 'trauma surgeon', 'orthopedic surgeon', 'neurologist',
    'psychiatrist', 'psychologist', 'physical therapist', 'occupational therapist',
    
    # Medical procedures and treatments
    'emergency treatment', 'trauma care', 'surgical intervention', 'procedure',
    'operation', 'therapy', 'rehabilitation', 'physical therapy', 'occupational therapy',
    'diagnostic imaging', 'blood work', 'laboratory testing', 'biopsy',
    'injection', 'medication administration', 'prescription', 'dosage',
    
    # Medical conditions and symptoms
    'acute', 'chronic', 'progressive', 'degenerative', 'congenital', 'acquired',
    'primary', 'secondary', 'bilateral', 'unilateral', 'anterior', 'posterior',
    'superior', 'inferior', 'medial', 'lateral', 'proximal', 'distal',
    'superficial', 'deep', 'internal', 'external', 'benign', 'malignant',
}

# Document structure terms from legal medical context
DOCUMENT_STRUCTURE_TERMS = {
    # Report sections
    'introduction', 'background', 'history', 'summary', 'findings', 'conclusion',
    'recommendation', 'assessment', 'evaluation', 'analysis', 'opinion',
    'impression', 'plan', 'treatment plan', 'prognosis', 'diagnosis',
    
    # Document headers/footers
    'patient name', 'date of birth', 'dob', 'medical record number', 'mrn',
    'account number', 'claim number', 'policy number', 'case number',
    'provider', 'facility', 'department', 'service date', 'admission date',
    'discharge date', 'report date', 'dictated', 'transcribed', 'reviewed',
    
    # Legal document sections
    'statement of facts', 'legal basis', 'damages claimed', 'demand for payment',
    'notice of claim', 'reservation of rights', 'without prejudice',
    'settlement demand', 'time limit', 'response required', 'final demand',
}

# Financial and billing terms
FINANCIAL_BILLING_TERMS = {
    # Medical billing
    'medical bills', 'hospital bills', 'physician charges', 'facility fees',
    'professional fees', 'diagnostic charges', 'laboratory charges',
    'radiology charges', 'surgical fees', 'anesthesia fees', 'room charges',
    'pharmacy charges', 'durable medical equipment', 'ambulance charges',
    
    # Insurance and payments
    'copayment', 'copay', 'coinsurance', 'out-of-pocket', 'maximum',
    'allowed amount', 'usual and customary', 'reasonable charges',
    'explanation of benefits', 'eob', 'claim denied', 'claim approved',
    'payment', 'reimbursement', 'balance', 'outstanding', 'past due',
    
    # Legal costs
    'attorney fees', 'legal costs', 'court costs', 'filing fees',
    'expert witness fees', 'deposition costs', 'discovery costs',
    'settlement amount', 'judgment amount', 'award', 'verdict amount',
}

# Combined comprehensive vocabulary for legal medical OCR
LEGAL_MEDICAL_COMPREHENSIVE = (
    LEGAL_LITIGATION_TERMS |
    MEDICAL_LITIGATION_TERMS |
    DOCUMENT_STRUCTURE_TERMS |
    FINANCIAL_BILLING_TERMS |
    ALL_INJURY_TERMS
)

# Common abbreviations in legal medical context
LEGAL_MEDICAL_ABBREVIATIONS = {
    **INJURY_ABBREVIATIONS,
    
    # Legal abbreviations
    'P&S': 'Permanent and Stationary',
    'QME': 'Qualified Medical Examiner',
    'AME': 'Agreed Medical Examiner',
    'PQME': 'Panel Qualified Medical Examiner',
    'LC': 'Labor Code',
    'CCR': 'California Code of Regulations',
    'WPI': 'Whole Person Impairment',
    'PD': 'Permanent Disability',
    'TD': 'Temporary Disability',
    'DFEC': 'Date of First Entitlement to Compensation',
    'AOE/COE': 'Arising Out of Employment/Course of Employment',
    'C&R': 'Compromise and Release',
    'MSA': 'Medicare Set Aside',
    'WCAB': 'Workers Compensation Appeals Board',
    'DWC': 'Division of Workers Compensation',
    'SIF': 'Subsequent Injuries Fund',
    'SIBTF': 'Subsequent Injuries Benefits Trust Fund',
    
    # Medical record abbreviations
    'H&P': 'History and Physical',
    'SOAP': 'Subjective Objective Assessment Plan',
    'CC': 'Chief Complaint',
    'HPI': 'History of Present Illness',
    'PMH': 'Past Medical History',
    'PSH': 'Past Surgical History',
    'FH': 'Family History',
    'SH': 'Social History',
    'ROS': 'Review of Systems',
    'PE': 'Physical Examination',
    'A&P': 'Assessment and Plan',
    'D/C': 'Discharge',
    'F/U': 'Follow Up',
    'PRN': 'As Needed',
    'BID': 'Twice Daily',
    'TID': 'Three Times Daily',
    'QID': 'Four Times Daily',
    'HS': 'At Bedtime',
    'AC': 'Before Meals',
    'PC': 'After Meals',
    'NPO': 'Nothing by Mouth',
    'STAT': 'Immediately',
    'DNR': 'Do Not Resuscitate',
    'DNI': 'Do Not Intubate',
    'AMA': 'Against Medical Advice',
    'LOC': 'Loss of Consciousness',
    'GCS': 'Glasgow Coma Scale',
    'VSS': 'Vital Signs Stable',
    'NKDA': 'No Known Drug Allergies',
    'NKA': 'No Known Allergies',
    'WNL': 'Within Normal Limits',
    'NAD': 'No Acute Distress',
    'HEENT': 'Head, Eyes, Ears, Nose, Throat',
    'CV': 'Cardiovascular',
    'RESP': 'Respiratory',
    'GI': 'Gastrointestinal',
    'GU': 'Genitourinary',
    'MSK': 'Musculoskeletal',
    'NEURO': 'Neurological',
    'PSYCH': 'Psychiatric',
    'DERM': 'Dermatological',
}

# Common OCR errors in legal medical documents
LEGAL_MEDICAL_OCR_CORRECTIONS = {
    # Legal term corrections
    r'\blitigafion\b': 'litigation',
    r'\bnegligence\b': 'negligence',
    r'\bliabilitv\b': 'liability',
    r'\bsettlement\b': 'settlement',
    r'\bcompensafion\b': 'compensation',
    r'\bdamaqes\b': 'damages',
    r'\battornev\b': 'attorney',
    r'\bcounsel\b': 'counsel',
    r'\bdeposifion\b': 'deposition',
    r'\baffidavit\b': 'affidavit',
    r'\bsubpoena\b': 'subpoena',
    r'\bevidence\b': 'evidence',
    r'\btestimonv\b': 'testimony',
    r'\bwitness\b': 'witness',
    r'\bjudqment\b': 'judgment',
    r'\bverdict\b': 'verdict',
    r'\binsurance\b': 'insurance',
    r'\bpolicv\b': 'policy',
    r'\badjuster\b': 'adjuster',
    r'\bclairn\b': 'claim',
    r'\bclairns\b': 'claims',
    
    # Medical term corrections specific to records
    r'\brnedical\b': 'medical',
    r'\brecord\b': 'record',
    r'\brecords\b': 'records',
    r'\bhospital\b': 'hospital',
    r'\bemergencv\b': 'emergency',
    r'\btrauma\b': 'trauma',
    r'\bintensive\b': 'intensive',
    r'\bconsultafion\b': 'consultation',
    r'\bevaluafion\b': 'evaluation',
    r'\bphvsician\b': 'physician',
    r'\bsurqeon\b': 'surgeon',
    r'\btherapist\b': 'therapist',
    r'\btherapv\b': 'therapy',
    r'\brehabilitation\b': 'rehabilitation',
    r'\bradioloqical\b': 'radiological',
    r'\blaboratorv\b': 'laboratory',
    r'\bsurgical\b': 'surgical',
    r'\bprocedural\b': 'procedural',
    r'\bprescripfion\b': 'prescription',
    r'\brnedication\b': 'medication',
    r'\bdosaqe\b': 'dosage',
    r'\bdiagnosis\b': 'diagnosis',
    r'\bprognosis\b': 'prognosis',
    r'\bsymptoms\b': 'symptoms',
    r'\btreatrnent\b': 'treatment',
    r'\bproqress\b': 'progress',
    r'\bimproverment\b': 'improvement',
    
    # Financial/billing corrections
    r'\bbill\b': 'bill',
    r'\bbills\b': 'bills',
    r'\bcharqes\b': 'charges',
    r'\bfees\b': 'fees',
    r'\bpayment\b': 'payment',
    r'\breimbursement\b': 'reimbursement',
    r'\bbalance\b': 'balance',
    r'\bamount\b': 'amount',
    r'\bcost\b': 'cost',
    r'\bcosts\b': 'costs',
    r'\bexpenses\b': 'expenses',
}

# Patterns for legal medical document structure
LEGAL_MEDICAL_PATTERNS = {
    'case_number': [
        r'(?:case|claim|file)\s*(?:number|no\.?|#)[:\s]*([A-Z0-9\-]+)',
        r'(?:docket|matter)\s*(?:number|no\.?|#)[:\s]*([A-Z0-9\-]+)'
    ],
    'policy_number': [
        r'(?:policy|pol\.?)\s*(?:number|no\.?|#)[:\s]*([A-Z0-9\-]+)',
        r'(?:coverage|insurance)\s*(?:number|no\.?|#)[:\s]*([A-Z0-9\-]+)'
    ],
    'medical_record_number': [
        r'(?:medical record|mr|mrn)\s*(?:number|no\.?|#)[:\s]*([A-Z0-9\-]+)',
        r'(?:patient|account)\s*(?:number|no\.?|#)[:\s]*([A-Z0-9\-]+)'
    ],
    'settlement_amount': [
        r'(?:settlement|demand|claim)\s*(?:amount)?[:\s]*\$([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:damages|compensation)[:\s]*\$([0-9,]+(?:\.[0-9]{2})?)'
    ],
    'date_of_service': [
        r'(?:date of service|service date|dos)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'(?:treatment date|visit date)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'
    ],
    'provider_name': [
        r'(?:provider|physician|doctor|dr\.?)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'(?:attending|treating)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    ]
}

def get_legal_medical_vocabulary() -> Set[str]:
    """Get comprehensive legal medical vocabulary."""
    return LEGAL_MEDICAL_COMPREHENSIVE

def get_legal_medical_abbreviations() -> Dict[str, str]:
    """Get legal medical abbreviations dictionary."""
    return LEGAL_MEDICAL_ABBREVIATIONS

def get_legal_medical_corrections() -> Dict[str, str]:
    """Get legal medical OCR corrections dictionary."""
    return LEGAL_MEDICAL_OCR_CORRECTIONS

def get_legal_medical_patterns() -> Dict[str, List[str]]:
    """Get legal medical document patterns."""
    return LEGAL_MEDICAL_PATTERNS

def calculate_legal_medical_relevance(text: str) -> float:
    """Calculate relevance score for legal medical documents."""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count legal medical terms
    legal_medical_terms = sum(1 for word in words if word in LEGAL_MEDICAL_COMPREHENSIVE)
    
    # Bonus for legal patterns
    pattern_bonus = 0
    for pattern_group in LEGAL_MEDICAL_PATTERNS.values():
        for pattern in pattern_group:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_bonus += 0.1
    
    # Bonus for abbreviations
    abbrev_bonus = sum(0.05 for abbrev in LEGAL_MEDICAL_ABBREVIATIONS.keys() 
                      if abbrev in text)
    
    # Calculate base score
    if len(words) == 0:
        return 0.0
    
    base_score = legal_medical_terms / len(words)
    total_score = min(base_score + pattern_bonus + abbrev_bonus, 1.0)
    
    return total_score

def is_legal_medical_document(text: str, threshold: float = 0.15) -> bool:
    """Determine if text appears to be a legal medical document."""
    relevance_score = calculate_legal_medical_relevance(text)
    return relevance_score >= threshold
