import io
import base64
from PIL import Image


def to_b64_png(pil_img: Image.Image) -> str:
    """Convert PIL image to base64 PNG string."""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def bytes_to_b64(data: bytes) -> str:
    """Convert raw bytes to base64 string."""
    return base64.b64encode(data).decode("utf-8")
