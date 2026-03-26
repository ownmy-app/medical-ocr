"""Parser for extracting prescription/medication data from OCR text."""
import re
from typing import Dict, List, Optional


class PrescriptionParser:
    """Extract medication names, dosages, and frequencies from OCR'd prescriptions."""

    def parse(self, text: str) -> List[Dict[str, Optional[str]]]:
        """Extract medications from text. Returns list of {name, dosage, frequency}."""
        medications = []
        lines = text.split("\n")
        for line in lines:
            med = self._parse_medication_line(line)
            if med:
                medications.append(med)
        return medications

    def _parse_medication_line(self, line: str) -> Optional[Dict[str, Optional[str]]]:
        pattern = r"([A-Za-z]+(?:\s[A-Za-z]+)?)\s+(\d+\s*(?:mg|mcg|ml|g|units?))\s*(?:,?\s*(.+))?"
        m = re.search(pattern, line, re.IGNORECASE)
        if m:
            return {
                "name": m.group(1).strip(),
                "dosage": m.group(2).strip(),
                "frequency": m.group(3).strip() if m.group(3) else None,
            }
        return None
