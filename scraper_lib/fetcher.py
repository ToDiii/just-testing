import requests
import tempfile
import os
from PyPDF2 import PdfReader

from .ocr import extract_text_with_ocr

def fetch_html(session: requests.Session, url: str) -> str | None:
    """Fetches HTML content from a URL."""
    print(f"Fetching: {url}")
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def download_pdf_to_text(session: requests.Session, pdf_url: str) -> str | None:
    """
    Downloads a PDF, extracts text, and uses OCR as a fallback.
    Returns the extracted text or None on failure.
    """
    print(f"Downloading PDF: {pdf_url}")
    temp_pdf_path = None
    try:
        response = session.get(pdf_url, timeout=45)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            temp_pdf_path = tmp_file.name

        text = ""
        try:
            with open(temp_pdf_path, 'rb') as f:
                reader = PdfReader(f)
                if reader.is_encrypted:
                    try:
                        reader.decrypt('')
                    except Exception:
                        print(f"Could not decrypt PDF {pdf_url}")
                        return None
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2 error while reading {pdf_url}: {e}.")

        if not text.strip():
            print(f"Warning: No text extracted from PDF, using OCR fallback: {pdf_url}")
            text = extract_text_with_ocr(temp_pdf_path)

        return text if text.strip() else None
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF {pdf_url}: {e}")
        return None
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)