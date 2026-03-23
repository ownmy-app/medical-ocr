from __future__ import annotations

DATE_FORMATS = [
"%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%b-%Y", "%b %d, %Y",
"%d %b %Y", "%m/%d/%y", "%d-%m-%Y", "%Y/%m/%d"
]

COMMON_BODY_PARTS = [
"head","scalp","neck","cervical","shoulder","clavicle","arm","elbow","forearm",
"wrist","hand","finger","chest","thoracic","rib","abdomen","lumbar","back",
"hip","pelvis","groin","thigh","knee","leg","ankle","foot","toe"
]

ABBREV_MAP = {
"c/o": "complains of",
"h/o": "history of",
"s/p": "status post",
"R/O": "rule out",
"SOB": "shortness of breath",
"HTN": "hypertension",
"DM": "diabetes mellitus",
"OA": "osteoarthritis",
"ROM": "range of motion",
"TTP": "tender to palpation",
"WNL": "within normal limits",
"F/U": "follow-up",
"N/V": "nausea and vomiting",
"MMI": "maximum medical improvement",
}

WORK_RESTRICTION_PATTERNS = [
r"\bno\s+lifting\s*(?:over|greater than)?\s*\d+\s*(?:lb|pounds|kg)\b",
r"\boff\s+work\b",
r"\breturn(?:ed)?\s+to\s+work\b",
r"\blight\s+duty\b",
r"\brestricted\s+duty\b",
r"\bno\s+(?:overhead\s+)?reaching\b",
r"\bno\s+bending\b",
r"\bno\s+twisting\b",
r"\bno\s+prolonged\s+standing\b",
]

FUTURE_NEEDS_PATTERNS = [
r"\brecommend(?:ed|s|ing)?\b",
r"\bfollow\s*up\b",
r"\bf/u\b",
r"\bplanned\b",
r"\bconsider\b",
r"\bshould\s+undergo\b",
r"\bcontinue\b",
r"\bPT\b|\bphysical therapy\b",
r"\bMRI\b|\bCT\b|\bx[- ]?ray\b|\bultrasound\b",
r"\binjection\b|\bsurgery\b|\bDME\b|\bdurable medical equipment\b",
]

ICD_PATTERN = r"\b([A-TV-Z]\d{2}(?:\.\d{1,4})?)\b"
CPT_PATTERN = r"\b(\d{4,5})\b"
MED_PATTERN = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+))\s+\d+(?:\.\d+)?\s(?:mg|mcg|g|units)\b"

PROCEDURE_HINTS = [r"\bprocedure\b", r"\boperation\b", r"\boperative\b", r"\bsurgery\b"]
RAD_IMPRESSION_HINTS = [r"\bimpression\b", r"\bconclusion\b", r"\bassessment\b"]
LAB_HDR_HINTS = [r"\blaboratory\b", r"\blabs?\b", r"\bresults\b", r"\breference\s+range\b"]
PHYS_LETTER_HINTS = [r"^to:\s", r"^dear\s", r"\bon\s+behalf\s+of\b"]

SOAP_HEADINGS = {
"subjective": r"^\ssubjective\s[:\-]",
"objective": r"^\sobjective\s[:\-]",
"assessment": r"^\sassessment\s[:\-]",
"plan": r"^\splan\s[:\-]",
}