from app.adapters.ocr.base import BaseOCR


class StubOCR(BaseOCR):
    async def extract_text(self, image_bytes: bytes) -> str:
        return "[OCR stub] Extracted text from image placeholder. In production, this would use a real OCR engine."
