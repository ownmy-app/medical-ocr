"""
Configuration file for Enhanced OCR system.
Set up environment variables for external API services.
"""

import os
from typing import Dict, List

# Top-level constants for quick access
DEFAULT_ENGINE = "tesseract"
SUPPORTED_FORMATS = ["pdf", "png", "jpg", "jpeg", "tiff", "bmp"]

# OCR Engine Configuration
OCR_CONFIG = {
    # Confidence thresholds (0.0 to 1.0)
    "confidence_threshold": float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7")),
    "quality_threshold": float(os.getenv("OCR_QUALITY_THRESHOLD", "0.6")),
    
    # Engine preferences (engines to try in order)
    "preferred_engines": os.getenv("OCR_PREFERRED_ENGINES", "easyocr,paddleocr,tesseract,trocr").split(","),
    
    # Enable/disable external APIs
    "enable_google_vision": os.getenv("ENABLE_GOOGLE_VISION", "true").lower() == "true",
    "enable_azure_vision": os.getenv("ENABLE_AZURE_VISION", "true").lower() == "true",
    "enable_aws_textract": os.getenv("ENABLE_AWS_TEXTRACT", "true").lower() == "true",
    
    # Processing settings
    "max_image_size": int(os.getenv("OCR_MAX_IMAGE_SIZE", "4096")),  # pixels
    "timeout_per_engine": int(os.getenv("OCR_ENGINE_TIMEOUT", "30")),  # seconds
    "parallel_processing": os.getenv("OCR_PARALLEL_PROCESSING", "true").lower() == "true",
}

# Google Cloud Vision API
GOOGLE_CLOUD_CONFIG = {
    "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
}

# Azure Computer Vision API
AZURE_VISION_CONFIG = {
    "endpoint": os.getenv("AZURE_VISION_ENDPOINT"),
    "key": os.getenv("AZURE_VISION_KEY"),
    "region": os.getenv("AZURE_VISION_REGION", "eastus"),
}

# AWS Textract
AWS_TEXTRACT_CONFIG = {
    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
}

# Medical document specific settings
MEDICAL_OCR_CONFIG = {
    "enable_medical_postprocessing": True,
    "medical_vocabulary_boost": True,
    "handwriting_detection": True,
    "signature_detection": False,  # Set to True if you need signature detection
}

def get_available_engines() -> List[str]:
    """Return list of available OCR engines based on configuration."""
    engines = []
    
    # Always available
    engines.append("tesseract")
    
    # Check for optional engines
    try:
        import easyocr  # noqa: F401
        engines.append("easyocr")
    except ImportError:
        pass
    
    try:
        from paddleocr import PaddleOCR  # noqa: F401
        engines.append("paddleocr")
    except ImportError:
        pass
    
    try:
        from transformers import TrOCRProcessor  # noqa: F401
        engines.append("trocr")
    except ImportError:
        pass
    
    # External APIs
    if GOOGLE_CLOUD_CONFIG["credentials_path"] and OCR_CONFIG["enable_google_vision"]:
        engines.append("google_vision")
    
    if AZURE_VISION_CONFIG["endpoint"] and AZURE_VISION_CONFIG["key"] and OCR_CONFIG["enable_azure_vision"]:
        engines.append("azure_vision")
    
    if AWS_TEXTRACT_CONFIG["access_key_id"] and OCR_CONFIG["enable_aws_textract"]:
        engines.append("aws_textract")
    
    return engines

def validate_configuration() -> Dict[str, bool]:
    """Validate OCR configuration and return status of each component."""
    status = {
        "tesseract": True,  # Always assume available
        "easyocr": False,
        "paddleocr": False,
        "trocr": False,
        "google_vision": False,
        "azure_vision": False,
        "aws_textract": False,
    }
    
    try:
        import easyocr  # noqa: F401
        status["easyocr"] = True
    except ImportError:
        pass
    
    try:
        from paddleocr import PaddleOCR  # noqa: F401
        status["paddleocr"] = True
    except ImportError:
        pass
    
    try:
        from transformers import TrOCRProcessor  # noqa: F401
        status["trocr"] = True
    except ImportError:
        pass
    
    # Check external API configurations
    if GOOGLE_CLOUD_CONFIG["credentials_path"]:
        try:
            from google.cloud import vision  # noqa: F401
            status["google_vision"] = True
        except ImportError:
            pass
    
    if AZURE_VISION_CONFIG["endpoint"] and AZURE_VISION_CONFIG["key"]:
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient  # noqa: F401
            status["azure_vision"] = True
        except ImportError:
            pass
    
    if AWS_TEXTRACT_CONFIG["access_key_id"]:
        try:
            import boto3  # noqa: F401
            status["aws_textract"] = True
        except ImportError:
            pass
    
    return status

if __name__ == "__main__":
    print("🔧 Enhanced OCR Configuration Status:")
    print("=" * 50)
    
    available_engines = get_available_engines()
    print(f"📋 Available engines: {', '.join(available_engines)}")
    
    validation_status = validate_configuration()
    for engine, available in validation_status.items():
        status_icon = "✅" if available else "❌"
        print(f"{status_icon} {engine}: {'Available' if available else 'Not configured/installed'}")
    
    print("\n🔧 Current Configuration:")
    print(f"  - Confidence threshold: {OCR_CONFIG['confidence_threshold']}")
    print(f"  - Quality threshold: {OCR_CONFIG['quality_threshold']}")
    print(f"  - Preferred engines: {', '.join(OCR_CONFIG['preferred_engines'])}")
    print(f"  - Max image size: {OCR_CONFIG['max_image_size']}px")
    print(f"  - Engine timeout: {OCR_CONFIG['timeout_per_engine']}s")

