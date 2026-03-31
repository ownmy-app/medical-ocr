"""
Unified file ingestion: PDF and image support.

- PDF files are split into per-page images via pdf2image (poppler).
- Image files (PNG, JPG, TIFF, BMP, WEBP) are loaded directly via Pillow.
- Multi-page TIFFs are expanded into separate frames.

All paths return a list of PIL.Image.Image objects (one per page/frame).
"""

import logging
import os
from pathlib import Path
from typing import List

from PIL import Image

logger = logging.getLogger(__name__)

# Supported image extensions (case-insensitive)
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif"}

# Supported PDF extensions
_PDF_EXTENSIONS = {".pdf"}


def _is_pdf(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()
    return ext in _PDF_EXTENSIONS


def _is_image(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()
    return ext in _IMAGE_EXTENSIONS


def ingest_pdf(file_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Convert a PDF to a list of PIL Images (one per page).

    Requires ``poppler`` system dependency and ``pdf2image`` Python package.

    Parameters
    ----------
    file_path : str
        Path to the PDF file.
    dpi : int
        Resolution for rasterisation (default 300).

    Returns
    -------
    list[Image.Image]
        One PIL Image per PDF page.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError(
            "pdf2image is required for PDF ingestion. "
            "Install with: pip install pdf2image  "
            "(and ensure poppler is installed on your system)"
        )

    logger.info("Ingesting PDF: %s (dpi=%d)", file_path, dpi)
    pages = convert_from_path(file_path, dpi=dpi)
    logger.info("PDF converted to %d page image(s)", len(pages))
    return pages


def ingest_image(file_path: str) -> List[Image.Image]:
    """
    Load an image file as a list of PIL Images.

    Multi-frame TIFFs are expanded into separate frames.  All other formats
    return a single-element list.

    Parameters
    ----------
    file_path : str
        Path to the image file.

    Returns
    -------
    list[Image.Image]
        One PIL Image per frame/page.
    """
    logger.info("Ingesting image: %s", file_path)
    img = Image.open(file_path)

    # Handle multi-frame TIFF
    frames: List[Image.Image] = []
    try:
        while True:
            # Convert to RGB to normalise mode (some TIFFs are CMYK/L)
            frame = img.copy()
            if frame.mode not in ("RGB", "L"):
                frame = frame.convert("RGB")
            frames.append(frame)
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        # Single-frame image
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        frames = [img]

    logger.info("Image loaded: %d frame(s)", len(frames))
    return frames


def ingest_file(file_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Auto-detect file type and return a list of PIL Images.

    Supports PDF files and common image formats.  Raises ValueError for
    unsupported file types.

    Parameters
    ----------
    file_path : str
        Path to the file (PDF or image).
    dpi : int
        DPI for PDF rasterisation (ignored for images).

    Returns
    -------
    list[Image.Image]
        One PIL Image per page/frame.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if _is_pdf(file_path):
        return ingest_pdf(file_path, dpi=dpi)
    elif _is_image(file_path):
        return ingest_image(file_path)
    else:
        # Try PDF first (some files lack extension), fall back to image
        ext = Path(file_path).suffix.lower()
        logger.warning(
            "Unrecognised extension '%s' for %s; attempting PDF then image",
            ext, file_path,
        )
        try:
            return ingest_pdf(file_path, dpi=dpi)
        except Exception:
            pass
        try:
            return ingest_image(file_path)
        except Exception:
            pass
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {sorted(_PDF_EXTENSIONS | _IMAGE_EXTENSIONS)}"
        )


def get_supported_extensions() -> List[str]:
    """Return sorted list of all supported file extensions."""
    return sorted(_PDF_EXTENSIONS | _IMAGE_EXTENSIONS)
