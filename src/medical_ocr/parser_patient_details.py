"""Parser for extracting patient details from OCR text."""
import re
from typing import Dict, Optional


class PatientDetailsParser:
    """Extract patient demographics from OCR'd medical documents."""

    def parse(self, text: str) -> Dict[str, Optional[str]]:
        """Extract patient name, DOB, and ID from text."""
        return {
            "patient_name": self._extract_name(text),
            "date_of_birth": self._extract_dob(text),
            "patient_id": self._extract_id(text),
        }

    def _extract_name(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:Patient|Name)\s*:\s*(.+?)(?:\n|$)",
            r"(?:Pt|PT)\s*:\s*(.+?)(?:\n|$)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_dob(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:DOB|Date of Birth|D\.O\.B\.?)\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_id(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:Patient ID|MRN|Medical Record)\s*[:#]?\s*(\S+)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None
