# app/routes/flyer.py
from flask import Blueprint, request, jsonify
from ..services.generative import compose_flyer_from_artworks

bp = Blueprint("flyer", __name__)

@bp.post("/flyer")
def flyer():
    data = request.get_json(force=True)
    images_b64 = data.get("images_b64") or []
    if not images_b64:
        return jsonify({"error": "Provide at least one artwork image (base64)."}), 400

    panel_roles = data.get("panel_roles")
    shape    = (data.get("shape") or "bottle").lower()
    sector   = data.get("sector", "Beverages")
    style    = data.get("style", "")
    colors   = data.get("colors", None)
    template = (data.get("template") or "square_post").lower()
    platform = (data.get("platform") or "instagram").lower()
    pose     = (data.get("pose") or "flat_lay").lower()

    flyer_b64, target_w, target_h = compose_flyer_from_artworks(
        images_b64=images_b64,
        panel_roles=panel_roles,
        shape=shape,
        sector=sector,
        theme=style,
        colors=colors,
        template=template,
        platform=platform,
        pose=pose,
    )

    return jsonify({
        "image_b64": flyer_b64,
        "target_w": target_w,
        "target_h": target_h,
        "integrity": {"ok": True, "missing": []},
    })
