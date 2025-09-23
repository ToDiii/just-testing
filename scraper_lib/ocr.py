import pytesseract
from pdf2image import convert_from_path

def extract_text_with_ocr(pdf_path: str) -> str:
    """
    Extracts text from a PDF using OCR if it's an image-based PDF.
    """
    try:
        images = convert_from_path(pdf_path)
        return "\n".join(pytesseract.image_to_string(img) for img in images)
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""
