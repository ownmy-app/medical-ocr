from fastapi import FastAPI, File, UploadFile
import uvicorn
from .extractor import extract, OCR
from .pipeline import generate_summary, generate_summary_with_confidence
from .export_md import to_markdown
import uuid
import os
from typing import Any, Dict, List, Optional

import shutil
import mimetypes
from urllib.parse import urlparse
import json

import requests
from fastapi import HTTPException, Body

from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
print("🤖 Initializing OpenAI client...")
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print("✅ OpenAI API key found in environment")
    openai_client = OpenAI(api_key=openai_api_key)
    print("✅ OpenAI client initialized successfully")
else:
    print("⚠️ Warning: OPENAI_API_KEY not found in environment variables")
    openai_client = None

app = FastAPI()

origins = [
    "http://localhost:3000",   # React/Next.js local dev
    "http://127.0.0.1:3000",
     "http://localhost:5173",
      "http://127.0.0.1:5173",
      "http://127.0.0.1:8000",
      "http://localhost:8000",
      "http://localhost:8585",
      "https://supa.nometria.com",
      "https://supa.ownmy.app",
      "https://demo.nometria.com",
      "https://app.nometria.com",
      "https://nometria.com",
      "https://functions.nometria.com"
    "https://your-frontend-domain.com",  # production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100 MB
REQUEST_TIMEOUT = (5, 60)  # (connect, read) seconds

    

def _build_records_for_summary(
    *,
    ocr_text: str,
    extractor_payload: Optional[Dict[str, Any]],
    source_name: str
) -> List[Dict[str, Any]]:
    """
    Normalizes extractor output into the format expected by generate_summary().
    Tries to pull a date if your extractor provided one; otherwise leaves it None.
    """
    # Try common date fields your pipeline might accept
    possible_date_keys = ["date", "document_date", "service_date", "created_at"]
    date_val = None
    if isinstance(extractor_payload, dict):
        for k in possible_date_keys:
            if k in extractor_payload and extractor_payload[k]:
                date_val = extractor_payload[k]
                break

    return [{
        "text": ocr_text or "",
        "date": date_val,       # your pipeline can ignore None
        "source": source_name,
    }]


def _safe_ext_from_mime(mime: Optional[str], default=".pdf") -> str:
    if not mime:
        return default
    # Basic MIME -> extension mapping
    ext = mimetypes.guess_extension(mime.split(";")[0].strip())
    return ext or default


def _ext_from_url(url: str, default=".pdf") -> str:
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    return ext if ext else default


def _stream_download(url: str, dst_path: str) -> None:
    """
    Stream a file from HTTP(S) to dst_path with size limit and basic validations.
    Raises HTTPException on failures.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed.")

    try:
        with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as r:
            r.raise_for_status()

            # Optional: validate content type if you only expect PDFs/images
            ctype = r.headers.get("Content-Type", "").lower()
            # You can tighten this as needed:
            allowed_prefixes = ("application/pdf", "image/", "application/octet-stream")
            if not any(ctype.startswith(p) for p in allowed_prefixes):
                # Not fatal, but you may choose to reject:
                pass

            total = 0
            with open(dst_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
                    if chunk:  # filter out keep-alive chunks
                        total += len(chunk)
                        if total > MAX_DOWNLOAD_BYTES:
                            raise HTTPException(status_code=413, detail="Remote file too large.")
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")




def _filename_from_url(url: str, fallback_ext: str) -> str:
    try:
        name = url.split("?")[0].rsplit("/", 1)[-1]
        if not os.path.splitext(name)[1]:
            name += fallback_ext
        return name
    except Exception:
        return f"remote{fallback_ext}"

@app.post("/extract_file")
def extract_file(
    payload: dict = Body(...)
):
    print("📄 /extract_file endpoint called")
    print(f"📨 Received payload keys: {list(payload.keys())}")
    
    file_url = payload.get("file_url")
    file = payload.get("file")
    file_format = payload.get("file_format")
    
    print("🔍 Extracted parameters:")
    print(f"  - File URL: {file_url}")
    print(f"  - File provided: {file is not None}")
    print(f"  - File format: {file_format}")

    tmp_path = None

    if not file and not file_url:
        raise HTTPException(status_code=400, detail="Provide either `file` or `file_url`.")

    try:
        # --- Case 1: Uploaded file ---
        if file is not None:
            # Name temp file using original extension if available, else .pdf
            _, ext = os.path.splitext(file.filename or "")
            ext = ext if ext else ".pdf"
            tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")

            with open(tmp_path, "wb") as f_out:
                shutil.copyfileobj(file.file, f_out)

        # --- Case 2: Remote file via URL ---
        else:
            # Prefer extension from URL; fall back to MIME after a HEAD, else .pdf
            # First try a HEAD to guess content type (non-fatal if blocked)
            mime_guess = None
            try:
                head = requests.head(file_url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
                mime_guess = head.headers.get("Content-Type")
            except requests.exceptions.RequestException:
                pass

            ext = _ext_from_url(file_url) or _safe_ext_from_mime(mime_guess, default=".pdf")
            if not ext.startswith("."):
                ext = "." + ext

            tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
            _stream_download(file_url, tmp_path)

        # --- Run your OCR/extractor on tmp_path ---
        print(f"🔄 Running OCR extraction on file: {tmp_path}")
        result = OCR(tmp_path)  # pass file_format if useful
        print("✅ OCR extraction completed")
        print(f"📊 Result type: {type(result).__name__}")
        return result

    except HTTPException as http_error:
        # Propagate FastAPI HTTPExceptions as-is
        print(f"🚫 HTTP Exception in extract_file: {http_error.detail}")
        raise

    except Exception as e:
        # Generic error envelope
        print(f"💥 Unexpected error in extract_file: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return {"error": str(e)}

    finally:
        # Cleanup
        try:
            if tmp_path and os.path.exists(tmp_path):
                print(f"🧹 Cleaning up temporary file: {tmp_path}")
                os.remove(tmp_path)
                print("✅ Temporary file cleaned up")
        except Exception as cleanup_error:
            print(f"⚠️ Failed to cleanup temporary file: {cleanup_error}")
            pass
@app.post("/extract_from_doc")
def extract_from_doc(
    payload: dict = Body(...)
):
    # Save incoming file temporarily
    file_urls: List[str] = payload.get("file_urls") or []
    file_url: Optional[str] = payload.get("file_url")
    file = payload.get("file")  # keeping back-compat with your original shape
    file_format: str = payload.get("file_format", "patient_details")

    # Normalize into a list of sources to process
    sources: List[Dict[str, Any]] = []
    if file_urls:
        for u in file_urls:
            if isinstance(u, str) and u.strip():
                sources.append({"kind": "url", "value": u.strip()})
    elif file_url:
        sources.append({"kind": "url", "value": file_url})
    elif file is not None:
        sources.append({"kind": "upload", "value": file})
    else:
        raise HTTPException(status_code=400, detail="Provide `file_urls` or `file_url` or `file`.")

    all_records: List[Dict[str, Any]] = []
    per_file_results: List[Dict[str, Any]] = []
    tmp_paths_to_cleanup: List[str] = []

    data: Dict[str, Any] = {}
    text: Optional[str] = None
    summary_out: Optional[Dict[str, Any]] = None
    markdown_preview: Optional[str] = None

    try:
        for src in sources:
            tmp_path = None
            src_name = "uploaded.pdf"
            src_url = None

            try:
                if src["kind"] == "upload":
                    up = src["value"]
                    _, ext = os.path.splitext(getattr(up, "filename", "") or "")
                    ext = ext if ext else ".pdf"
                    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                    with open(tmp_path, "wb") as f_out:
                        shutil.copyfileobj(up.file, f_out)
                    src_name = getattr(up, "filename", src_name)

                else:  # remote URL
                    src_url = src["value"]
                    # HEAD (best-effort) for mime
                    mime_guess = None
                    try:
                        head = requests.head(src_url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
                        mime_guess = head.headers.get("Content-Type")
                    except requests.exceptions.RequestException:
                        pass

                    ext = _ext_from_url(src_url) or _safe_ext_from_mime(mime_guess, default=".pdf")
                    if not ext.startswith("."):
                        ext = "." + ext

                    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                    _stream_download(src_url, tmp_path)
                    src_name = _filename_from_url(src_url, ext)

                tmp_paths_to_cleanup.append(tmp_path)

                # --- Extract per file ---
                data: Dict[str, Any] = {}
                text: Optional[str] = None

                result = extract(tmp_path, file_format)
                if isinstance(result, tuple) and len(result) == 2:
                    data, text = result
                else:
                    data = result if isinstance(result, dict) else {}
                    text = data.get("text")

                if not text and isinstance(data, dict):
                    text = data.get("ocr") or data.get("raw_text") or ""

                # --- Build summary input records (PER FILE) ---
                file_records = _build_records_for_summary(
                    ocr_text=text or "",
                    extractor_payload=data if isinstance(data, dict) else None,
                    source_name=src_name
                )

                # Ensure iterable
                if isinstance(file_records, dict):
                    file_records = [file_records]
                elif not isinstance(file_records, list):
                    file_records = []

                # Inject file-level metadata into each record
                file_meta = {
                    "file_name": src_name,
                    "file_url": src_url,
                    "file_format": file_format,
                    "tmp_path": tmp_path,  # useful for tracing; omit in prod if sensitive
                    "text_chars": len(text or ""),
                }
                for rec in file_records:
                    # avoid collision; keep it namespaced
                    rec["file_meta"] = file_meta

                all_records.extend(file_records)

                per_file_results.append({
                    "file_meta": file_meta,
                    "extractor_payload_keys": list(data.keys()) if isinstance(data, dict) else [],
                    "record_count": len(file_records),
                    "error": None,
                })

            except HTTPException:
                continue
                raise  # pass FastAPI errors through unchanged
            except Exception as e:
                per_file_results.append({
                    "file_meta": {
                        "file_name": src_name,
                        "file_url": src_url,
                        "file_format": file_format,
                        "tmp_path": tmp_path,
                    },
                    "extractor_payload_keys": [],
                    "record_count": 0,
                    "error": str(e),
                })
                continue
        # Run the summarizer pipeline
        summary_out = generate_summary(all_records)

        # Create a short markdown preview (you can return full markdown if you prefer)
        try:
            markdown_full = to_markdown(summary_out)
            markdown_preview = markdown_full[:2000]  # trim to keep response light
        except Exception as _:
            markdown_preview = None

        # Shape the response
        response = {
            "data": data,                    # structured fields from extractor
            "text": text,                    # full OCR text
            "summary": summary_out,          # full summarizer output (includes summary_text, faq, etc.)
            "summary_text": summary_out.get("summary_text") if isinstance(summary_out, dict) else None,
            "faq": summary_out.get("faq") if isinstance(summary_out, dict) else None,
            "markdown_preview": markdown_preview
        }
        return response

    except Exception as e:
        return {
            "error": str(e)
        }
    finally:
        # Clean up temp file
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


# ─── In-memory case document store ────────────────────────────────────────────
_case_documents: Dict[str, List[Dict[str, Any]]] = {}


@app.post("/cases/{case_id}/documents")
async def batch_upload_documents(
    case_id: str,
    files: List[UploadFile] = File(...),
):
    """
    Batch endpoint: upload multiple documents for a case.

    Accepts multiple files in one request, processes each through the OCR
    pipeline, and returns an array of results with per-page and overall
    confidence scores.  Results are tracked by case_id.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results: List[Dict[str, Any]] = []
    tmp_paths: List[str] = []

    for upload_file in files:
        tmp_path = None
        try:
            # Save uploaded file to temp location
            _, ext = os.path.splitext(upload_file.filename or "")
            ext = ext if ext else ".pdf"
            tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
            tmp_paths.append(tmp_path)

            with open(tmp_path, "wb") as f_out:
                content = await upload_file.read()
                f_out.write(content)

            # Run OCR
            ocr_result = OCR(tmp_path)

            # Extract page-level confidence from metadata
            metadata = ocr_result.get("_metadata", {})
            page_metrics = metadata.get("page_metrics", {})
            processing_summary = metadata.get("processing_summary", {})

            # Build per-page confidence array
            page_confidences = []
            for page_num in sorted(page_metrics.keys(), key=lambda x: int(x)):
                pm = page_metrics[page_num]
                page_confidences.append({
                    "page": int(page_num),
                    "confidence": round(pm.get("confidence", 0.0), 4),
                    "quality_score": round(pm.get("quality_score", 0.0), 4),
                    "engine_used": pm.get("engine_used", "unknown"),
                })

            # Overall document confidence (average of page confidences)
            if page_confidences:
                avg_confidence = sum(
                    pc["confidence"] for pc in page_confidences
                ) / len(page_confidences)
            else:
                avg_confidence = processing_summary.get("avg_confidence", 0.0)

            # Collect page text for summary
            page_texts = []
            for key, val in ocr_result.items():
                if key.startswith("_"):
                    continue
                if isinstance(val, str):
                    page_texts.append(val)
            full_text = "\n".join(page_texts)

            doc_result = {
                "document_id": str(uuid.uuid4()),
                "case_id": case_id,
                "filename": upload_file.filename,
                "total_pages": metadata.get("total_pages", len(page_texts)),
                "text": full_text,
                "confidence": {
                    "overall": round(avg_confidence, 4),
                    "per_page": page_confidences,
                },
                "processing_summary": processing_summary,
                "error": None,
            }
            results.append(doc_result)

        except Exception as exc:
            results.append({
                "document_id": str(uuid.uuid4()),
                "case_id": case_id,
                "filename": upload_file.filename or "unknown",
                "total_pages": 0,
                "text": "",
                "confidence": {"overall": 0.0, "per_page": []},
                "processing_summary": {},
                "error": str(exc),
            })

    # Store results by case_id
    if case_id not in _case_documents:
        _case_documents[case_id] = []
    _case_documents[case_id].extend(results)

    # Clean up temp files
    for tmp_path in tmp_paths:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    return {
        "case_id": case_id,
        "documents_processed": len(results),
        "results": results,
    }


@app.get("/cases/{case_id}/documents")
def get_case_documents(case_id: str):
    """Retrieve all processed documents for a case."""
    docs = _case_documents.get(case_id, [])
    return {
        "case_id": case_id,
        "document_count": len(docs),
        "documents": docs,
    }


def normalize_schema(schema):
    """Normalize JSON schema for OpenAI structured outputs"""
    print("🔧 Normalizing schema...")
    if not schema:
        print("📋 No schema provided")
        return schema
    
    print(f"📋 Schema type: {schema.get('type', 'undefined')}")
    print(f"📋 Schema keys: {list(schema.keys())}")
    
    # shallow clone is fine here; deepen if you plan nested strictness
    copy = dict(schema)
    if copy.get("type") == "object" and "additionalProperties" not in copy:
        copy["additionalProperties"] = False
        print("🔧 Added additionalProperties: false")
    
    print("✅ Schema normalization completed")
    return copy


def parse_pi_assessment(resp, schema):
    """Parse PI assessment response from OpenAI"""
    print("🔄 Starting parse_pi_assessment...")
    print(f"📋 Schema provided: {schema is not None}")
    
    # Extract the text blob (Responses API variations handled)
    text = None
    
    # Try different response formats
    print("🔍 Attempting to extract text from response...")
    if hasattr(resp, 'output_text'):
        text = resp.output_text
        print("✅ Found text via output_text attribute")
    elif hasattr(resp, 'output') and resp.output:
        print("🔍 Searching through output array...")
        for i, item in enumerate(resp.output):
            print(f"  - Checking output item {i}")
            if hasattr(item, 'content') and item.content:
                for j, content in enumerate(item.content):
                    print(f"    - Checking content item {j}")
                    if hasattr(content, 'text'):
                        text = content.text
                        print("✅ Found text via output.content.text")
                        break
                    elif hasattr(content, 'output_text'):
                        text = content.output_text
                        print("✅ Found text via output.content.output_text")
                        break
                if text:
                    break
    elif hasattr(resp, 'choices') and resp.choices:
        # Standard chat completion format
        text = resp.choices[0].message.content
        print("✅ Found text via choices[0].message.content")
    
    if not text:
        print("❌ Could not extract text from response")
        print(f"🔍 Response attributes: {dir(resp)}")
        raise HTTPException(status_code=500, detail="Could not find model JSON in response")

    print(f"📝 Extracted text length: {len(text)} characters")
    print(f"📝 Text preview: {text[:200]}...")

    # Parse JSON
    print("🔄 Attempting to parse JSON...")
    try:
        data = json.loads(text)
        print("✅ Successfully parsed JSON")
        print(f"📊 Parsed data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"📝 Raw text that failed to parse: {text}")
        raise HTTPException(status_code=500, detail="Model output was not valid JSON")

    # Repair common issues to satisfy schema
    if schema and "viability_score" in data and isinstance(data["viability_score"], (int, float)):
        print(f"🔧 Processing viability_score: {data['viability_score']}")
        original_score = data["viability_score"]
        
        # If model produced 0..1, scale to 1..10
        if data["viability_score"] > 0 and data["viability_score"] <= 1:
            data["viability_score"] = data["viability_score"] * 10
            print(f"  - Scaled from 0-1 range: {original_score} -> {data['viability_score']}")
        
        # Clamp to [1, 10] and round to 2 decimals
        if data["viability_score"] < 1:
            data["viability_score"] = 1
            print(f"  - Clamped to minimum: {original_score} -> 1")
        if data["viability_score"] > 10:
            data["viability_score"] = 10
            print(f"  - Clamped to maximum: {original_score} -> 10")
        
        data["viability_score"] = round(data["viability_score"] * 100) / 100
        print(f"  - Final viability_score: {data['viability_score']}")

    # Ensure array types
    if "strengths" in data:
        if not isinstance(data.get("strengths"), list):
            print("🔧 Converting strengths to empty array")
            data["strengths"] = []
        else:
            print(f"✅ Strengths is array with {len(data['strengths'])} items")
    
    if "weaknesses" in data:
        if not isinstance(data.get("weaknesses"), list):
            print("🔧 Converting weaknesses to empty array")
            data["weaknesses"] = []
        else:
            print(f"✅ Weaknesses is array with {len(data['weaknesses'])} items")

    # Optional: if recommendation is "refer" but no reason, add a minimal reason
    if data.get("recommendation") == "refer" and not data.get("referral_reason"):
        print("🔧 Adding default referral reason for 'refer' recommendation")
        data["referral_reason"] = "Refer for trucking litigation specialization or venue strategy."

    print("✅ Parse PI assessment completed successfully")
    return data


@app.post("/ai/invoke")
def invoke_llm(payload: dict = Body(...)):
    """Backend endpoint for LLM invocation"""
    print("🚀 /ai/invoke endpoint called")
    print(f"📨 Received payload keys: {list(payload.keys())}")
    
    # Check if OpenAI client is available
    if openai_client is None:
        print("❌ Error: OpenAI client not initialized (missing API key)")
        raise HTTPException(status_code=500, detail="OpenAI API not configured")
    
    try:
        prompt = payload.get("prompt")
        add_context_from_internet = payload.get("add_context_from_internet", False)
        response_json_schema = payload.get("response_json_schema")
        file_urls = payload.get("file_urls")
        
        print("🔍 Extracted parameters:")
        print(f"  - Prompt length: {len(prompt) if prompt else 0} characters")
        print(f"  - Context from internet: {add_context_from_internet}")
        print(f"  - Has schema: {response_json_schema is not None}")
        print(f"  - File URLs: {file_urls}")
        
        if not prompt:
            print("❌ Error: No prompt provided")
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # If we have a schema, use structured outputs
        if response_json_schema:
            print("🔧 Using structured outputs with schema")
            normalized_schema = normalize_schema(response_json_schema)
            print(f"📋 Normalized schema keys: {list(normalized_schema.keys()) if normalized_schema else None}")
            
            try:
                print("🤖 Attempting OpenAI Responses API call...")
                # Try using the responses API for structured outputs
                resp = openai_client.responses.create(
                    model="gpt-5",
                    reasoning={"effort": "medium"},
                    input=[
                        {
                            "role": "system",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": "You are an experienced U.S. personal-injury attorney. "
                                           "Return your answer strictly as JSON that matches the provided schema. "
                                           "No prose outside JSON.",
                                }
                            ],
                        },
                        {
                            "role": "user",
                            "content": [{"type": "input_text", "text": prompt}],
                        },
                    ],
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "assessment_response",
                            "schema": normalized_schema,
                            "strict": False
                        },
                    },
                )
                
                print("✅ OpenAI Responses API call successful")
                print("🔄 Parsing PI assessment response...")
                
                result = parse_pi_assessment(resp, normalized_schema)
                print("✅ Successfully parsed PI assessment")
                print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                
                response_data = {
                    "data": {
                        "message": result,
                    }
                }
                print("🎯 Returning structured response")
                return response_data
                
            except Exception as e:
                # Fall back to regular chat completion if responses API fails
                print(f"⚠️ Responses API failed, falling back to chat completion: {e}")
                print("🤖 Attempting OpenAI Chat Completion API call...")
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant. Return your response as JSON if a schema is provided."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"} if response_json_schema else None
                )
                
                print("✅ OpenAI Chat Completion API call successful")
                content = response.choices[0].message.content
                print(f"📝 Received content length: {len(content)} characters")
                
                try:
                    print("🔄 Attempting to parse JSON response...")
                    parsed_content = json.loads(content) if response_json_schema else content
                    print("✅ Successfully parsed JSON")
                    
                    response_data = {
                        "data": {
                            "message": parsed_content,
                        }
                    }
                    print("🎯 Returning fallback structured response")
                    return response_data
                except json.JSONDecodeError as json_error:
                    print(f"⚠️ JSON parsing failed: {json_error}")
                    print("📝 Returning raw content")
                    return {
                        "data": {
                            "message": content,
                        }
                    }
        else:
            print("💬 Using regular text response (no schema)")
            print("🤖 Making OpenAI Chat Completion API call...")
            
            # Regular text response
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            print("✅ OpenAI API call successful")
            content = response.choices[0].message.content
            print(f"📝 Received response length: {len(content)} characters")
            
            response_data = {
                "response": content
            }
            print("🎯 Returning text response")
            return response_data
            
    except HTTPException as http_error:
        print(f"🚫 HTTP Exception: {http_error.detail}")
        raise
    except Exception as e:
        print(f"💥 Unexpected error in LLM invocation: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"LLM invocation failed: {str(e)}")


@app.post("/ai/generate-image")
def generate_image(payload: dict = Body(...)):
    """Backend endpoint for image generation"""
    print("🎨 /ai/generate-image endpoint called")
    print(f"📨 Received payload keys: {list(payload.keys())}")
    
    # Check if OpenAI client is available
    if openai_client is None:
        print("❌ Error: OpenAI client not initialized (missing API key)")
        raise HTTPException(status_code=500, detail="OpenAI API not configured")
    
    try:
        prompt = payload.get("prompt")
        
        print("🔍 Extracted parameters:")
        print(f"  - Prompt length: {len(prompt) if prompt else 0} characters")
        print(f"  - Prompt preview: {prompt[:100] if prompt else 'None'}...")
        
        if not prompt:
            print("❌ Error: No prompt provided")
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        print("🤖 Making OpenAI DALL-E API call...")
        print("  - Model: dall-e-3")
        print("  - Size: 1024x1024")
        print("  - Quality: standard")
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        print("✅ OpenAI DALL-E API call successful")
        image_url = response.data[0].url
        print(f"🖼️ Generated image URL: {image_url[:50]}...")
        
        response_data = {"url": image_url}
        print("🎯 Returning image response")
        return response_data
        
    except HTTPException as http_error:
        print(f"🚫 HTTP Exception: {http_error.detail}")
        raise
    except Exception as e:
        print(f"💥 Unexpected error in image generation: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Nometria Backend Server...")
    print("🌐 Host: 0.0.0.0")
    print("🔌 Port: 9080")
    print("📡 CORS enabled for local development")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=9080)
