import io
import re
import os
import logging
from typing import Tuple, Dict, Any
from PIL import Image, ImageEnhance

# PDF Libraries
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# OCR Library & Binary Auto-Detection
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
    
    # Auto-detect Tesseract binary path on Windows if not in PATH
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logging.info(f"Tesseract binary configured at: {path}")
            break

except ImportError:
    PYTESSERACT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResumeParser")


class ResumeParser:
    """
    Fast Parser for extracting text from PDF, JPG, JPEG, and PNG resume files.
    Supports native PDF text reading and high-speed Tesseract OCR with 7s timeout safety.
    """

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """Apply fast image processing to improve OCR speed and prevent freezing."""
        if image.mode != "RGB":
            image = image.convert("RGB")
        image = image.convert("L")
        
        # Downscale large image to max 1500px dimension for fast 1-second OCR
        width, height = image.size
        max_dim = max(width, height)
        if max_dim > 1500:
            scale = 1500.0 / max_dim
            image = image.resize((int(width * scale), int(height * scale)), Image.Resampling.BILINEAR)
        elif max_dim < 800:
            scale = 1.5
            image = image.resize((int(width * scale), int(height * scale)), Image.Resampling.BILINEAR)

        return image

    @classmethod
    def parse_pdf(cls, file_bytes: bytes) -> str:
        """Extract text from PDF using available libraries."""
        text = ""

        # Strategy 1: pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    extracted = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted.append(page_text)
                    if extracted:
                        text = "\n".join(extracted)
                        logger.info("Extracted PDF text via pdfplumber")
                        return cls.clean_text(text)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}")

        # Strategy 2: pypdf
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                extracted = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted.append(page_text)
                if extracted:
                    text = "\n".join(extracted)
                    logger.info("Extracted PDF text via pypdf")
                    return cls.clean_text(text)
            except Exception as e:
                logger.warning(f"pypdf extraction failed: {e}")

        # Strategy 3: PyPDF2 fallback
        if PYPDF2_AVAILABLE:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                extracted = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted.append(page_text)
                if extracted:
                    text = "\n".join(extracted)
                    logger.info("Extracted PDF text via PyPDF2")
                    return cls.clean_text(text)
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")

        return cls.clean_text(text)

    @classmethod
    def parse_image(cls, file_bytes: bytes) -> Tuple[str, bool]:
        """
        Extract text from JPG/JPEG/PNG images using Tesseract OCR with 7-second safety timeout.
        Returns (extracted_text, is_ocr_successful).
        """
        try:
            image = Image.open(io.BytesIO(file_bytes))
            processed_img = cls.preprocess_image(image)

            if PYTESSERACT_AVAILABLE:
                try:
                    # Run Tesseract with strict 7s timeout to prevent hanging on cloud servers
                    text = pytesseract.image_to_string(processed_img, timeout=7)
                    if not text or len(text.strip()) < 15:
                        text = pytesseract.image_to_string(image, timeout=5)
                    
                    if text and len(text.strip()) > 15:
                        logger.info("Successfully extracted text from image using Tesseract OCR")
                        return cls.clean_text(text), True
                except Exception as tess_err:
                    logger.warning(f"Tesseract execution error or timeout: {tess_err}")

            return "Scanned Image Resume Uploaded.", False
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return "Scanned Image Resume Uploaded.", False

    @classmethod
    def parse_file(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """Main entrypoint for parsing PDF, JPG, JPEG, PNG."""
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            raw_text = cls.parse_pdf(file_bytes)
            file_type = "PDF Document"
            ocr_used = False
        elif ext in [".jpg", ".jpeg", ".png"]:
            raw_text, ocr_used = cls.parse_image(file_bytes)
            file_type = f"Image ({ext.upper().replace('.', '')})"
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Only PDF, JPG, JPEG, PNG are supported.")

        cleaned_text = cls.clean_text(raw_text)

        return {
            "filename": filename,
            "file_type": file_type,
            "char_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "raw_text": cleaned_text,
            "ocr_used": ocr_used
        }

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        text = re.sub(r'[\r\t]', ' ', text)
        text = re.sub(r'[ ]{2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
