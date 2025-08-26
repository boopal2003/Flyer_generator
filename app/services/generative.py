# app/services/generative.py
from __future__ import annotations

import base64
from typing import List, Optional, Tuple

from ..openai_client import get_client          # decrypts API key at runtime
from ..prompts import FLYER_DIRECT_SYSTEM, FLYER_DIRECT_USER

# ---------- Pose directives ----------
POSE_DIRECTIVES = {
    "flat_lay": (
        "Place the product lying flat on a tabletop, camera directly above (90° top-down), "
        "orthographic feel with minimal perspective; show only the top face; hide thickness/side faces."
    ),
    "front_straight": (
        "Place the product standing but facing the camera straight-on; verticals and horizontals parallel; "
        "centered, minimal perspective."
    ),
    "angled_hero": (
        "Place the product as a 3/4 hero shot with gentle perspective and soft shadow; clearly show the front face."
    ),
    "isometric": (
        "Render with isometric-style parallel projection; equal angles, no vertical convergence."
    ),
}

# ---------- Template specs (target download size + model-allowed render size) ----------
# gpt-image-1 supports only these sizes: "1024x1024", "1024x1536", "1536x1024", or "auto"
TEMPLATE_SPECS = {
    "square_post":      {"target": (1080, 1080), "model": "square"},
    "quote":            {"target": (1080, 1080), "model": "square"},
    "carousel":         {"target": (1080, 1080), "model": "square"},

    "landscape_post":   {"target": (1200, 628),  "model": "landscape"},
    "thumbnail":        {"target": (1280, 720),  "model": "landscape"},
    "youtube_banner":   {"target": (2048, 1152), "model": "landscape"},
    "web_banner":       {"target": (1920, 600),  "model": "landscape"},
    "presentation":     {"target": (1920, 1080), "model": "landscape"},

    "story":            {"target": (1080, 1920), "model": "portrait"},
    "document":         {"target": (1240, 1754), "model": "portrait"},
    "print":            {"target": (1240, 1754), "model": "portrait"},
    "infographic":      {"target": (1080, 1920), "model": "portrait"},
}

MODEL_SIZE = {
    "square":    "1024x1024",
    "portrait":  "1024x1536",
    "landscape": "1536x1024",
}

ASPECT_NOTE = {
    "square":    "Square 1:1",
    "landscape": "Wide 3:2–16:9",
    "portrait":  "Tall 3:4–9:16",
}

# ---------- Platform audience hints ----------
PLATFORM_AUDIENCE = {
    "instagram": "visually stylish younger audience",
    "facebook":  "broad family-friendly audience",
    "linkedin":  "professional corporate audience",
    "x":         "fast-paced witty audience",
    "tiktok":    "trendy youth audience",
    "youtube":   "video-savvy global audience",
    "web":       "general consumer website visitors",
}


def compose_flyer_from_artworks(
    images_b64: List[str],
    panel_roles: Optional[List[str]],
    shape: str,
    sector: str,
    theme: str,
    colors: Optional[List[str]],
    template: str,
    platform: str,
    pose: str = "flat_lay",
) -> Tuple[str, int, int]:
    """
    Create a flyer image from artwork panels using gpt-image-1.
    Returns: (base64_png, target_width, target_height)

    - images_b64: list of panel images (base64-encoded PNG/JPG bytes)
    - panel_roles: matching roles like ["front","back","left","right","top","bottom","cap","generic"]
    - template: one of TEMPLATE_SPECS keys
    - pose: one of POSE_DIRECTIVES keys
    """

    # Choose template spec and model-compatible size
    spec = TEMPLATE_SPECS.get(template) or TEMPLATE_SPECS["square_post"]
    target_w, target_h = spec["target"]
    model_size = MODEL_SIZE[spec["model"]]
    aspect_note = ASPECT_NOTE[spec["model"]]

    # Platform voice
    audience = PLATFORM_AUDIENCE.get(platform, "general audience, balanced tone")

    # Role mapping lines (for prompt clarity)
    panel_roles = panel_roles or ["generic"] * len(images_b64)
    role_lines = [f"image[{i}] -> {r}" for i, r in enumerate(panel_roles)]

    # Colors & Pose text
    col = ", ".join(colors or []) or "brand palette"
    pose_directive = POSE_DIRECTIVES.get(pose, POSE_DIRECTIVES["flat_lay"])

    # Build final prompt
    prompt = (
        FLYER_DIRECT_SYSTEM
        + "\n\n"
        + FLYER_DIRECT_USER.format(
            shape=shape,
            role_map="\n".join(role_lines),
            sector=sector,
            theme=theme or "clean premium",
            colors=col,
            platform=platform,
            audience=audience,
            aspect_note=aspect_note,
            pose_directive=pose_directive,
        )
    )

    # Decode input images to raw bytes for the Images API
    img_inputs = [base64.b64decode(b) for b in images_b64]

    # Create client lazily — this decrypts your key via get_client()
    client = get_client()

    # Call Images Edit with a supported size close to desired aspect.
    resp = client.images.edit(
        model="gpt-image-1",
        prompt=prompt,
        image=img_inputs,           # list[bytes]
        size=model_size,            # "1024x1024" | "1024x1536" | "1536x1024" | "auto"
        # background="transparent",  # uncomment if you want PNG with alpha
    )

    # Return base64 image + the exact target pixels for client-side resizing on download
    return resp.data[0].b64_json, target_w, target_h
