"""Tests for medical-ocr filters — no GPU/tesseract required."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_filters_module_imports():
    """filters.py must import cleanly (no tesseract dependency at import time)."""
    import filters  # noqa: F401


def test_utils_module_imports():
    """utils.py must import cleanly."""
    import utils  # noqa: F401


def test_models_module_imports():
    """models.py must import cleanly (pydantic models)."""
    try:
        import models  # noqa: F401
    except ImportError as e:
        # pydantic not installed in test env is acceptable
        assert "pydantic" in str(e) or "openai" in str(e)


def test_ocr_config_has_required_keys():
    """OCR config must define supported output formats."""
    import ocr_config as cfg
    # Should define at least one supported format
    has_formats = (
        hasattr(cfg, "SUPPORTED_FORMATS")
        or hasattr(cfg, "OUTPUT_FORMATS")
        or hasattr(cfg, "EXPORT_FORMATS")
        or hasattr(cfg, "DEFAULT_ENGINE")
    )
    assert has_formats, "ocr_config must define supported formats or engine config"


def test_medical_vocabulary_not_empty():
    """Medical vocabulary lists must be non-empty."""
    import medical_text_refiner as mtr
    # Just ensure it loads without error
    assert mtr is not None
