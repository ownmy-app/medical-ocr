# medical-ocr

<div align="center">

**[Nometria](https://nometria.com)** takes AI-built apps to production on AWS — secure, scalable, ready for real users.

<sub><i>A legal tech customer needed to extract structured data from medical records. We built this multi-engine OCR pipeline and it became its own product.</i></sub>

[![Deploy with Nometria](https://img.shields.io/badge/Deploy%20with-Nometria-111827?style=for-the-badge)](https://nometria.com)

</div>

---

> Multi-engine OCR pipeline for medical and legal documents.
> Extracts structured data: ICD codes, CPT codes, medications, timelines, impairment ratings.

---

## Quick start

```bash
# System dependencies (required)
brew install tesseract poppler          # macOS
apt-get install tesseract-ocr poppler-utils   # Ubuntu

# Clone and install (base, no heavy GPU deps)
git clone https://github.com/nometria/medical-ocr
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

### One-click Docker start

```bash
# Set your API key and launch
export OPENAI_API_KEY=sk-proj-...
docker compose up --build

# API is now available at http://localhost:8000
```

### Optional dependencies

```bash
pip install -e ".[gpu]"        # EasyOCR + OpenCV (GPU-accelerated secondary engine)
pip install -e ".[gcp]"        # Google Cloud Vision (fallback engine)
pip install -e ".[anthropic]"  # Use Anthropic Claude as LLM provider
pip install -e ".[litellm]"    # Use any LiteLLM-supported provider
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
POST /extract_file                  →  upload single file (PDF or image)
                                    →  OCR (Tesseract → EasyOCR → GCV fallback)
                                    →  return per-page text + quality metrics

POST /extract_from_doc              →  upload file(s) with structured extraction
                                    →  OCR + classify document type
                                    →  extract structured fields
                                    →  generate timeline + summary
                                    →  return JSON

POST /cases/{case_id}/documents     →  batch upload multiple files for a case
                                    →  process each through the OCR pipeline
                                    →  return array of results with confidence scores
                                    →  track by case_id

GET  /cases/{case_id}/documents     →  retrieve all processed documents for a case

POST /ai/invoke                     →  LLM invocation for PI assessment
POST /ai/generate-image             →  image generation via DALL-E
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

## Multi-LLM support

The AI endpoints (`/ai/invoke`, `/ai/generate-image`) support multiple LLM backends.
Set the provider via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, or `litellm` |
| `LLM_MODEL` | per-provider | Model name override (e.g. `gpt-4o`, `claude-sonnet-4-20250514`) |
| `OPENAI_API_KEY` | required for openai + image gen | OpenAI API key |
| `ANTHROPIC_API_KEY` | required for anthropic | Anthropic API key |

```bash
# Use Anthropic Claude
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Use any LiteLLM-supported model
export LLM_PROVIDER=litellm
export LLM_MODEL=together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

Image generation (`/ai/generate-image`) always uses OpenAI DALL-E regardless of `LLM_PROVIDER`.

---

## Docker

```bash
docker compose up --build              # recommended (uses docker-compose.yml)
docker build -t medical-ocr .          # or build manually
docker run -p 8000:8000 --env-file .env medical-ocr
```

---

## Batch endpoint

Upload multiple documents for a case in a single request:

```bash
curl -X POST http://localhost:9080/cases/case-001/documents \
  -F "files=@report1.pdf" \
  -F "files=@report2.pdf" \
  -F "files=@scan.jpg"
```

Response includes per-document results with confidence scores:

```json
{
  "case_id": "case-001",
  "documents_processed": 3,
  "results": [
    {
      "document_id": "...",
      "filename": "report1.pdf",
      "total_pages": 4,
      "text": "...",
      "confidence": {
        "overall": 0.87,
        "per_page": [
          {"page": 1, "confidence": 0.91, "quality_score": 0.85, "engine_used": "advanced_fusion"},
          {"page": 2, "confidence": 0.83, "quality_score": 0.80, "engine_used": "tesseract_v1"}
        ]
      }
    }
  ]
}
```

Retrieve all processed documents for a case:

```bash
curl http://localhost:9080/cases/case-001/documents
```

---

## Confidence scoring

Every OCR result now includes confidence scores at two levels:

- **Per-page confidence** — from the OCR engine (Tesseract word-level confidence averaged, or quality heuristics when engine data is unavailable)
- **Overall document confidence** — average of all page confidences

Confidence is available in:
- The batch endpoint response (`confidence.overall`, `confidence.per_page`)
- The OCR metadata (`_metadata.page_metrics.{page}.confidence`)
- The pipeline summary via `generate_summary_with_confidence()`

---

## Supported file formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Multi-page supported via pdf2image/poppler |
| PNG | `.png` | Single image |
| JPEG | `.jpg`, `.jpeg` | Single image |
| TIFF | `.tiff`, `.tif` | Multi-frame TIFFs expanded into separate pages |
| BMP | `.bmp` | Single image |
| WebP | `.webp` | Single image |

PDF files are rasterised at 300 DPI by default. Image files are loaded directly via Pillow.

---

## Immediate next steps (to productionise as B2B SaaS)
1. ~~Add `POST /cases/{case_id}/documents` batch endpoint~~ Done
2. ~~Add per-document confidence scores to the API response~~ Done
3. ~~Add PDF ingestion (currently image/scan input only)~~ Done (PDF + image)
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

---

<p align="center">Made with ❤️ by <a href="https://nometria.com">Nometria</a> — deploy AI apps to production in one click</p>
