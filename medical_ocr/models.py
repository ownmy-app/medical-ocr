from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class OCRRecord:
    text: str
    date: Optional[str] = None
    source: Optional[str] = None
    doc_type: Optional[str] = None
    doc_id: Optional[str] = None

@dataclass
class TimelineEvent:
    date: Optional[datetime]
    title: str
    doc_type: str
    provider: Optional[str]
    facility: Optional[str]
    body_parts: List[str]
    diagnoses: List[str]
    icd_codes: List[str]
    cpt_codes: List[str]
    meds: List[str]
    plan: Optional[str]
    restrictions: List[str]
    raw_excerpt: str
    confidence: float = 0.75

@dataclass
class SummaryArtifacts:
    inconsistent_histories: List[str] = field(default_factory=list)
    referenced_missing_records: List[str] = field(default_factory=list)
    last_restrictions: Optional[str] = None
    last_visit: Optional[str] = None
    mmi_found: Optional[str] = None
    impairment_found: Optional[str] = None
    future_needs_snippets: List[str] = field(default_factory=list)
    abbreviations_used: Dict[str, str] = field(default_factory=dict)
    causation_statements: List[str] = field(default_factory=list)
    gaps_in_care_days: List[int] = field(default_factory=list)