import io
from pypdf import PdfReader
from docx import Document

def extract_text_from_attachment(filedata: bytes, filename: str) -> str | None:
    """Extracts readable text from common office document formats.
    Returns None if the format isn't supported or extraction fails."""
    if not filename:
        return None

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    try:
        if ext == 'pdf':
            reader = PdfReader(io.BytesIO(filedata))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text.strip() or None

        elif ext == 'docx':
            doc = Document(io.BytesIO(filedata))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text.strip() or None

        elif ext in ('txt', 'csv'):
            return filedata.decode('utf-8', errors='ignore').strip() or None

        else:
            # Unsupported for now: .doc (old binary format), .xlsx, images, .zip
            return None

    except Exception:
        return None