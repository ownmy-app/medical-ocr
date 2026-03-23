from __future__ import annotations
from typing import List, Callable
from medical_ocr.models import TimelineEvent

def by_doc_type(events: List[TimelineEvent], doc_type: str) -> List[TimelineEvent]:
    return [e for e in events if e.doc_type == doc_type]

def by_body_part(events: List[TimelineEvent], part: str) -> List[TimelineEvent]:
    return [e for e in events if part.lower() in [p.lower() for p in e.body_parts]]

def by_provider(events: List[TimelineEvent], provider_substr: str) -> List[TimelineEvent]:
    s = provider_substr.lower()
    return [e for e in events if e.provider and s in e.provider.lower()]

def with_restrictions(events: List[TimelineEvent]) -> List[TimelineEvent]:
    return [e for e in events if e.restrictions]

def imaging_only(events: List[TimelineEvent]) -> List[TimelineEvent]:
    return [e for e in events if e.doc_type == "Radiology Report"]

def procedures_only(events: List[TimelineEvent]) -> List[TimelineEvent]:
    return [e for e in events if e.doc_type == "Operative/Procedure Note"]