"""
OCR Service for extracting text from images and PDFs
"""

import logging
import os
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

class OCRService:
    """OCR Service for text extraction from files."""

    def __init__(self):
        self.enabled = os.getenv("OCR_ENABLED", "0") == "1"
        self.engine = os.getenv("OCR_ENGINE", "tesseract")  # tesseract, paddleocr, easyocr
        self._initialized = False

    async def initialize(self):
        """Initialize OCR engines."""
        if not self.enabled or self._initialized:
            return

        try:
            if self.engine == "tesseract":
                # Check if tesseract is available
                import subprocess
                result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("✅ Tesseract OCR initialized")
                    self._initialized = True
                else:
                    logger.warning("⚠️ Tesseract not available")
            elif self.engine in ["paddleocr", "easyocr"]:
                # These would require additional dependencies
                logger.warning(f"⚠️ OCR engine {self.engine} requires additional setup")
            else:
                logger.warning(f"⚠️ Unknown OCR engine: {self.engine}")
        except Exception as e:
            logger.error(f"❌ OCR initialization failed: {e}")

    from app.services.vision_service import vision_service

    async def extract_text(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """Extract text from file with Vision API fallback."""
        if not self.enabled:
            return {"text": None, "confidence": 0.0, "status": "disabled"}

        await self.initialize()

        start_time = time.time()
        try:
            if mime_type.startswith('image/'):
                # Try Vision API first for images
                vision_result = await vision_service.extract_text_and_entities(file_path)
                if vision_result.get("status") == "success":
                    return {
                        "text": vision_result.get("text"),
                        "confidence": vision_result.get("confidence", 0.0),
                        "status": "success",
                        "engine": f"{self.engine}_with_vision",
                        "entities": vision_result.get("entities", [])
                    }
                else:
                    # Fallback to Tesseract
                    return await self._extract_from_image(file_path)
            elif mime_type == 'application/pdf':
                return await self._extract_from_pdf(file_path)
            elif mime_type.startswith('text/'):
                return await self._extract_from_text(file_path)
            else:
                return {"text": None, "confidence": 0.0, "status": "unsupported"}
        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path}: {e}")
            return {"text": None, "confidence": 0.0, "status": "error", "error": str(e)}
        finally:
            processing_time = time.time() - start_time

    async def _extract_from_image(self, file_path: str) -> Dict[str, Any]:
        """Extract text from image using Tesseract."""
        if not self._initialized:
            return {"text": None, "confidence": 0.0, "status": "not_initialized"}

        try:
            import subprocess
            import tempfile

            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp_out:
                tmp_output = tmp_out.name

            # Run Tesseract
            result = subprocess.run([
                "tesseract",
                file_path,
                tmp_output.replace('.txt', ''),  # Remove .txt from path
                "--oem", "3",  # OCR Engine Mode
                "--psm", "6",  # Page Segmentation Mode for uniform blocks
                "-l", "eng+deu"  # English and German
            ], capture_output=True, text=True)

            if result.returncode == 0:
                # Read extracted text
                with open(tmp_output, 'r', encoding='utf-8') as f:
                    text = f.read().strip()

                # Estimate confidence (Tesseract doesn't provide confidence scores directly)
                confidence = 0.8 if len(text) > 10 else 0.5

                return {
                    "text": text,
                    "confidence": confidence,
                    "status": "success",
                    "engine": "tesseract"
                }
            else:
                return {
                    "text": None,
                    "confidence": 0.0,
                    "status": "failed",
                    "error": result.stderr
                }
        except Exception as e:
            return {"text": None, "confidence": 0.0, "status": "error", "error": str(e)}
        finally:
            # Cleanup temp file
            try:
                if 'tmp_output' in locals():
                    os.unlink(tmp_output)
            except:
                pass

    async def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF (stub for future implementation)."""
        # TODO: Implement PDF text extraction using libraries like PyPDF2 or pdfplumber
        try:
            # Try pdfplumber first for better layout handling
            import pdfplumber  # type: ignore
            text_parts: list[str] = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    try:
                        txt = page.extract_text() or ""
                        if txt:
                            text_parts.append(txt)
                    except Exception:
                        continue
            text = "\n\n".join([t.strip() for t in text_parts if t and t.strip()])
            return {
                "text": text or None,
                "confidence": 0.9 if text and len(text) > 20 else 0.5 if text else 0.0,
                "status": "success" if text else "empty",
                "engine": "pdfplumber"
            }
        except Exception:
            # Fallback to PyPDF2 basic text extraction
            try:
                import PyPDF2  # type: ignore
                text_parts: list[str] = []
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for i in range(len(reader.pages)):
                        try:
                            page = reader.pages[i]
                            txt = page.extract_text() or ""
                            if txt:
                                text_parts.append(txt)
                        except Exception:
                            continue
                text = "\n\n".join([t.strip() for t in text_parts if t and t.strip()])
                return {
                    "text": text or None,
                    "confidence": 0.7 if text and len(text) > 20 else 0.4 if text else 0.0,
                    "status": "success" if text else "empty",
                    "engine": "pypdf2"
                }
            except Exception as e:
                return {"text": None, "confidence": 0.0, "status": "error", "error": str(e)}

    async def _extract_from_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            return {
                "text": text,
                "confidence": 1.0,
                "status": "success",
                "engine": "text_reader"
            }
        except Exception as e:
            return {"text": None, "confidence": 0.0, "status": "error", "error": str(e)}

# Global OCR service instance
ocr_service = OCRService()
