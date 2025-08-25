# app/utils/pdf.py
import base64
import fitz  # PyMuPDF
import numpy as np
import cv2
from typing import List, Tuple

def pdf_to_page_pngs(pdf_bytes: bytes, dpi: int = 400,
                     max_pixels: int = 160_000_000,
                     max_side: int = 10_000) -> List[bytes]:
    """
    Rasterize each page to PNG bytes with a dynamic scale cap to avoid gigantic bitmaps.
    - dpi: base DPI target (will be scaled down if the page exceeds limits)
    - max_pixels: total pixel budget per page (e.g., 160M)
    - max_side: hard cap for width/height (e.g., 10k px)
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pngs: List[bytes] = []
    base_zoom = dpi / 72.0

    for page in doc:
        rect = page.rect  # width/height in points
        # Nominal pixel size at requested DPI
        w_nom = rect.width * base_zoom
        h_nom = rect.height * base_zoom
        pixels = w_nom * h_nom

        scale = 1.0
        # Cap by total pixels
        if pixels > max_pixels:
            scale = (max_pixels / pixels) ** 0.5  # scale both axes
        # Cap by longest side
        longest_nom = max(w_nom, h_nom)
        if longest_nom * scale > max_side:
            scale = min(scale, max_side / longest_nom)

        zoom = base_zoom * scale
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)  # RGB
        pngs.append(pix.tobytes("png"))
    return pngs

def _auto_panel_boxes(img_bgr: np.ndarray) -> List[Tuple[int,int,int,int]]:
    """
    Heuristic to detect big artwork rectangles on dieline pages.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # If page is bright overall, invert so content becomes white blobs
    if np.mean(gray) > 127:
        th = 255 - th

    # Close gaps to merge lines/text into larger regions
    kernel = np.ones((15, 15), np.uint8)
    closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)

    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = gray.shape
    min_area = 0.02 * W * H  # ignore very small regions (<2% of page)
    boxes = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < min_area:
            continue
        # filter tiny/thin artifacts
        if w < 0.08 * W and h < 0.08 * H:
            continue
        boxes.append((x, y, w, h))

    if not boxes:
        boxes = [(0, 0, W, H)]

    # Sort row-major (top→bottom buckets) then left→right
    boxes.sort(key=lambda b: (b[1] // max(1, H // 10), b[0]))
    return boxes

def extract_art_panels_from_png(png_bytes: bytes) -> List[bytes]:
    """
    From a page PNG, return cropped panel PNGs (bytes).
    """
    nparr = np.frombuffer(png_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    boxes = _auto_panel_boxes(img)
    out: List[bytes] = []
    for (x, y, w, h) in boxes:
        crop = img[y:y+h, x:x+w].copy()
        ok, enc = cv2.imencode(".png", crop, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        if ok:
            out.append(enc.tobytes())
    return out

def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
