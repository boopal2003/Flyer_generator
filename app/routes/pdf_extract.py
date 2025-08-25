# app/routes/pdf_extract.py
from flask import Blueprint, request, jsonify
from ..utils.pdf import pdf_to_page_pngs, extract_art_panels_from_png, b64
import base64, numpy as np, cv2

bp = Blueprint("pdf_extract", __name__)

@bp.post("/pdf_extract")
def pdf_extract():
    """
    Body: { "pdf_b64": "<base64>", "dpi": 400 }
    Returns:
    { "panels": [{ "image_b64": "...", "role": "front|back|generic", "w": int, "h": int }...],
      "pages": N }
    """
    data = request.get_json(force=True)
    pdf_b64 = data.get("pdf_b64")
    if not pdf_b64:
        return jsonify({"error": "pdf_b64 required"}), 400

    dpi = int(data.get("dpi", 400))
    pdf_bytes = base64.b64decode(pdf_b64)

    # Rasterize with caps
    page_pngs = pdf_to_page_pngs(pdf_bytes, dpi=dpi)

    panels = []
    for page_idx, page_png in enumerate(page_pngs):
        crops = extract_art_panels_from_png(page_png)
        if not crops:
            continue
        for i, crop_png in enumerate(crops):
            # Use OpenCV to get size (avoids Pillow DecompressionBomb)
            arr = np.frombuffer(crop_png, np.uint8)
            im = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
            h, w = im.shape[:2] if im is not None else (0, 0)
            role = "front" if i == 0 else ("back" if i == 1 else "generic")
            panels.append({
                "image_b64": b64(crop_png),
                "role": role,
                "w": int(w),
                "h": int(h),
            })

    if not panels and page_pngs:
        # Fallback: whole first page
        arr = np.frombuffer(page_pngs[0], np.uint8)
        im = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
        h, w = im.shape[:2] if im is not None else (0, 0)
        panels.append({
            "image_b64": b64(page_pngs[0]),
            "role": "generic",
            "w": int(w),
            "h": int(h),
        })

    return jsonify({"panels": panels, "pages": len(page_pngs)})
