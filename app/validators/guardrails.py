import base64
import io
from PIL import Image
import pytesseract


def ocr_text(img_b64: str) -> str:
    """Extract text from base64 image using pytesseract OCR."""
    raw = base64.b64decode(img_b64)
    im = Image.open(io.BytesIO(raw))
    im = im.convert("L")  # grayscale
    return pytesseract.image_to_string(im) or ""


def check_integrity(source_text: str, generated_text: str, required_terms: list[str]) -> dict:
    """
    Check that required terms from the source appear in the generated text.
    Returns {ok: bool, missing: list}.
    """
    src = source_text.lower()
    gen = generated_text.lower()
    missing = [t for t in required_terms if t.lower() not in gen]
    return {"ok": len(missing) == 0, "missing": missing}
