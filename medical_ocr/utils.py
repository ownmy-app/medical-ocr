from __future__ import annotations
import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None
import re
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from medical_ocr.config import DATE_FORMATS, ABBREV_MAP

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    s = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", s)
    if m:
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(m.group(1), fmt)
            except ValueError:
                continue
        return None

def normalize_ocr(text: str) -> str:
    if not text:
        return ""
    t = text
    # fix hyphenation across EOL
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)
    # collapse long duplicates
    t = re.sub(r"(.)\1{2,}", r"\1", t)

    def collapse_doubles(match: re.Match) -> str:
        word = match.group(0)
        if word.isupper() and len(word) <= 6:
            return word
        return re.sub(r"(.)\\1", r"\\1", word)

    t = re.sub(r"[A-Za-z]{3,}", lambda m: collapse_doubles(m), t)
    # common OCR confusions
    t = re.sub(r"(?<=\b[0-9])O\b", "0", t)
    t = re.sub(r"\bO(?=\\d)","0", t)
    t = re.sub(r"(?<=\b[0-9])l\b", "1", t)
    # punctuation/whitespace
    t = t.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'").replace("\u2013","-").replace("\u2014","-")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def expand_abbreviations_for_summary(text: str) -> Tuple[str, Dict[str, str]]:
    used = {}
    def rep(m: re.Match) -> str:
        token = m.group(0)
        exp = ABBREV_MAP.get(token, ABBREV_MAP.get(token.upper()))
        if exp:
            used[token.upper()] = exp
            return f"{exp} ({token})"
        return token
    pattern = r"\b(" + "|".join(map(re.escape, ABBREV_MAP.keys())) + r")\b"
    return (re.sub(pattern, rep, text), used)

def join_unique(items: List[str], sep: str = "; ", limit: int = 6) -> str:
    if not items: 
        return ""
    uniq = []
    seen = set()
    for it in items:
        t = it.strip(" .;")
        if t and t.lower() not in seen:
            uniq.append(t)
            seen.add(t.lower())
        if len(uniq) >= limit:
            break
    return sep.join(uniq)
def preprocess_image(img):
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    processed_image = cv2.adaptiveThreshold(
        resized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        65, # block size (after trial and error)
        13  # constant (after trial and error)
    )
    return processed_image