# medical-ocr

> Multi-engine OCR pipeline for medical and legal documents.
> Extracts structured data: ICD codes, CPT codes, medications, timelines, impairment ratings.

⚠️ **PRIVATE — Do not open source this repository.**
The `injury_medical_vocabulary.py` and `legal_medical_vocabulary.py` domain models
represent significant proprietary IP. This is a standalone B2B SaaS product.

---

## What it does

1. **OCR** — Three-engine pipeline: Tesseract (primary) → EasyOCR (secondary) → Google Cloud Vision (fallback)
2. **Classify** — Identifies 8 medical document types (treatment records, prescriptions, imaging, IME reports, etc.)
3. **Extract** — Pulls structured data per document:
   - ICD-10 diagnosis codes
   - CPT billing codes
   - Medications (name + dosage + frequency)
   - Body parts affected
   - Work restrictions
   - MMI (Maximum Medical Improvement) status
   - Impairment ratings
4. **Timeline** — Builds chronological treatment timeline across all records
5. **Summary** — Generates attorney-ready structured summary (demand letter format)
6. **Export** — DOCX or Markdown output

---

## Architecture

```
POST /process-document   →  upload file (PDF/image)
                         →  OCR (Tesseract → EasyOCR → GCV fallback)
                         →  classify document type
                         →  extract structured fields
                         →  update timeline
                         →  return JSON

POST /generate-summary   →  takes all processed documents for a case
                         →  builds chronological timeline
                         →  generates attorney summary
                         →  returns DOCX + JSON

GET  /health
```

---

## Setup

```bash
# System dependencies
brew install tesseract          # macOS
apt-get install tesseract-ocr   # Ubuntu

# Python
pip install -r requirements.txt
cp .env.example .env

# Run
uvicorn src.main:app --port 8000
```

---

## Docker

```bash
docker build -t medical-ocr .
docker run -p 8000:8000 --env-file .env medical-ocr
```

---

## Immediate next steps (to productionise as B2B SaaS)
1. Add `POST /cases/{case_id}/documents` batch endpoint
2. Add per-document confidence scores to the API response
3. Add PDF ingestion (currently image/scan input only)
4. Add HIPAA-compliant storage (S3 + KMS encryption)
5. Build a simple React UI for law firm case managers
6. Cold-email 10 personal injury law firms with a free trial offer

---

## Pricing model
- **Per document**: $0.50–2.00 per processed document
- **Monthly flat**: $200–500/mo for up to 500 docs
- **Enterprise**: custom pricing for high volume

## Target market
- Personal injury law firms (workers' comp, auto accidents)
- Medical malpractice attorneys
- Independent Medical Examiners (IME companies)
- Medical billing companies

## Competitive advantage
- `injury_medical_vocabulary.py`: domain-specific term lists with relevance scoring
  → keeps this IP **closed source**
- Multi-engine fallback → higher accuracy than single-engine tools
- Attorney-ready output format → no manual reformatting needed
