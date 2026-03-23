from pdf2image import convert_from_path
import pytesseract
import utils
from parser_patient_details import PatientDetailsParser
from parser_prescription import PrescriptionParser
from enhanced_ocr import extract_page_text
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# POPPLER_PATH = r"C:/poppler-24.02.0/Library/bin"
# TESSERACT_ENGINE_PATH = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd = TESSERACT_ENGINE_PATH


def OCR_old(file_path):
    # 1. extracting text from pdf file
    pages = convert_from_path(file_path)
    document_text = ""
    data={}
    for i in range(len(pages)):
        page = pages[i]
        processed_image = utils.preprocess_image(page)
        text = pytesseract.image_to_string(processed_image, lang="eng")
        data[f"{i+1}"]=text
    # print(data)
    return data

def OCR(file_path: str) -> Dict[str, Any]:
    """
    Enhanced OCR function using multiple engines for better accuracy.
    Returns page-level text extraction with quality metrics.
    """
    logger.info(f"🔄 Starting enhanced OCR processing for: {file_path}")
    
    # 1. Convert PDF to images
    try:
        pages = convert_from_path(file_path)
        logger.info(f"📄 Converted PDF to {len(pages)} page images")
    except Exception as e:
        logger.error(f"❌ Failed to convert PDF to images: {e}")
        return {"error": f"PDF conversion failed: {str(e)}"}
    
    # 2. Process each page with enhanced OCR
    data = {}
    page_metrics = {}
    
    for i, page in enumerate(pages):
        page_num = i + 1
        logger.info(f"🔄 Processing page {page_num}/{len(pages)}")
        
        try:
            # Use enhanced OCR system
            ocr_result = extract_page_text(page)
            
            # Store the extracted text
            data[str(page_num)] = ocr_result["text"]
            
            # Store additional metrics for analysis
            page_metrics[str(page_num)] = {
                "confidence": ocr_result["confidence"],
                "quality_score": ocr_result["quality_score"],
                "engine_used": ocr_result["engine_used"],
                "processing_time": ocr_result["processing_time"],
                "word_count": ocr_result["word_count"],
                "character_count": ocr_result["character_count"],
                "used_external_api": ocr_result.get("used_external_api", False)
            }
            
            logger.info(f"✅ Page {page_num} processed successfully "
                       f"(engine: {ocr_result['engine_used']}, "
                       f"confidence: {ocr_result['confidence']:.2f}, "
                       f"quality: {ocr_result['quality_score']:.2f})")
                       
        except Exception as e:
            logger.error(f"❌ Failed to process page {page_num}: {e}")
            # Fallback to basic pytesseract
            try:
                processed_image = utils.preprocess_image(page)
                text = pytesseract.image_to_string(processed_image, lang="eng")
                data[str(page_num)] = text
                page_metrics[str(page_num)] = {
                    "confidence": 0.5,  # Default fallback confidence
                    "quality_score": 0.5,
                    "engine_used": "tesseract_fallback",
                    "processing_time": 0.0,
                    "word_count": len(text.split()),
                    "character_count": len(text),
                    "used_external_api": False,
                    "error": str(e)
                }
                logger.info(f"⚠️ Used fallback OCR for page {page_num}")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback OCR also failed for page {page_num}: {fallback_error}")
                data[str(page_num)] = ""
                page_metrics[str(page_num)] = {
                    "confidence": 0.0,
                    "quality_score": 0.0,
                    "engine_used": "failed",
                    "processing_time": 0.0,
                    "word_count": 0,
                    "character_count": 0,
                    "used_external_api": False,
                    "error": str(fallback_error)
                }
    
    # 3. Calculate overall document metrics
    overall_metrics = calculate_document_metrics(page_metrics)
    
    # 4. Prepare final response
    result = {
        **data,  # Page-level text data (maintains backward compatibility)
        "_metadata": {
            "total_pages": len(pages),
            "processing_summary": overall_metrics,
            "page_metrics": page_metrics,
            "file_path": file_path
        }
    }
    
    logger.info(f"✅ Enhanced OCR processing completed for {file_path}")
    logger.info(f"📊 Overall confidence: {overall_metrics['avg_confidence']:.2f}, "
               f"quality: {overall_metrics['avg_quality']:.2f}")
    
    return result


def calculate_document_metrics(page_metrics: Dict[str, Dict]) -> Dict[str, Any]:
    """Calculate overall document quality metrics from page-level metrics."""
    if not page_metrics:
        return {
            "avg_confidence": 0.0,
            "avg_quality": 0.0,
            "total_processing_time": 0.0,
            "engines_used": [],
            "external_api_usage": 0,
            "successful_pages": 0,
            "failed_pages": 0
        }
    
    confidences = []
    qualities = []
    processing_times = []
    engines_used = set()
    external_api_count = 0
    successful_pages = 0
    failed_pages = 0
    
    for page_data in page_metrics.values():
        if "error" not in page_data:
            successful_pages += 1
            confidences.append(page_data["confidence"])
            qualities.append(page_data["quality_score"])
        else:
            failed_pages += 1
            
        processing_times.append(page_data["processing_time"])
        engines_used.add(page_data["engine_used"])
        
        if page_data.get("used_external_api", False):
            external_api_count += 1
    
    return {
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "avg_quality": sum(qualities) / len(qualities) if qualities else 0.0,
        "total_processing_time": sum(processing_times),
        "engines_used": list(engines_used),
        "external_api_usage": external_api_count,
        "successful_pages": successful_pages,
        "failed_pages": failed_pages
    }

def extract(file_path, file_format):
    # 1. extracting text from pdf file
    pages = convert_from_path(file_path)
    document_text = ""

    for page in pages:
        processed_image = utils.preprocess_image(page)
        text = pytesseract.image_to_string(processed_image, lang="eng")
        document_text = document_text + "\n" + text
    
    print(document_text)
    # 2. extract fields from text
    if file_format == "prescription":
        extracted_data = PrescriptionParser(document_text).parse()

    elif file_format == "patient_details":
        extracted_data = PatientDetailsParser(document_text).parse()
    
    else:
        raise Exception(f"Invalid file format: {file_format}")
    
    return extracted_data,document_text

