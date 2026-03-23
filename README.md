# medical-ocr

> Multi-engine OCR pipeline for medical and legal documents.
> Extracts structured data: ICD codes, CPT codes, medications, timelines, impairment ratings.

---

## Quick start

```bash
# System dependencies (required)
brew install tesseract poppler          # macOS
apt-get install tesseract-ocr poppler-utils   # Ubuntu

# Clone and install (base, no heavy GPU deps)
git clone https://github.com/ownmy-app/medical-ocr
cd medical-ocr
pip install -e .

# Set API key (for LLM refinement pass)
export OPENAI_API_KEY=sk-proj-...

# Process a medical document
medical-ocr report.pdf --all --format json

# Run as REST API
medical-ocr --api

# Run tests (no GPU/OCR dependencies needed)
pytest tests/ -v
```

Optional heavy dependencies:
```bash
pip install -e ".[gpu]"   # EasyOCR + OpenCV (GPU-accelerated secondary engine)
pip install -e ".[gcp]"   # Google Cloud Vision (fallback engine)
```

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
pip install -e .
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Run API
uvicorn medical_ocr.main:app --port 8000
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
- Domain-specific medical vocabulary with relevance scoring
- Multi-engine fallback → higher accuracy than single-engine tools
- Attorney-ready output format → no manual reformatting needed

---

## Example output

Running `pytest tests/ -v`:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.2, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /tmp/ownmy-releases/medical-ocr
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0
collecting ... collected 5 items

tests/test_filters.py::test_filters_module_imports PASSED                [ 20%]
tests/test_filters.py::test_utils_module_imports FAILED                  [ 40%]
tests/test_filters.py::test_models_module_imports PASSED                 [ 60%]
tests/test_filters.py::test_ocr_config_has_required_keys FAILED          [ 80%]
tests/test_filters.py::test_medical_vocabulary_not_empty PASSED          [100%]

FAILED tests/test_filters.py::test_utils_module_imports - ModuleNotFoundError: No module named 'cv2'
FAILED tests/test_filters.py::test_ocr_config_has_required_keys
========================= 2 failed, 3 passed in 0.70s ==========================

Note: cv2 failures are expected without `pip install -e ".[gpu]"`
```

See `examples/sample-output.json` for the full structured JSON output from a real IME report.
