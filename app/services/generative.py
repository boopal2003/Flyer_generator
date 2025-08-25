# app/services/generative.py
import base64
from openai import OpenAI
from ..prompts import FLYER_DIRECT_SYSTEM, FLYER_DIRECT_USER

client = OpenAI()

# Pose directives
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

# Template specs:
# - target: exact pixels for download (frontend resizes to this)
# - model: which allowed size to ask gpt-image-1 for ("square" | "landscape" | "portrait")
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

# Platform → audience hints
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
    images_b64: list[str],
    panel_roles: list[str] | None,
    shape: str,
    sector: str,
    theme: str,
    colors: list[str] | None,
    template: str,
    platform: str,
    pose: str = "flat_lay",
) -> tuple[str, int, int]:
    """
    Create a flyer image from artwork panels.
    Returns (base64_png, target_width, target_height)
    """
    spec = TEMPLATE_SPECS.get(template) or TEMPLATE_SPECS["square_post"]
    target_w, target_h = spec["target"]
    model_size = MODEL_SIZE[spec["model"]]
    aspect_note = {
        "square": "Square 1:1",
        "landscape": "Wide 3:2–16:9",
        "portrait": "Tall 3:4–9:16",
    }[spec["model"]]

    audience = PLATFORM_AUDIENCE.get(platform, "general audience, balanced tone")

    # role mapping
    panel_roles = panel_roles or ["generic"] * len(images_b64)
    role_lines = [f"image[{i}] -> {r}" for i, r in enumerate(panel_roles)]

    col = ", ".join(colors or []) or "brand palette"
    pose_directive = POSE_DIRECTIVES.get(pose, POSE_DIRECTIVES["flat_lay"])

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

    img_inputs = [base64.b64decode(b) for b in images_b64]

    # Ask the model for a supported render size close to the desired aspect.
    resp = client.images.edit(
        model="gpt-image-1",
        prompt=prompt,
        image=img_inputs,
        size=model_size,  # one of: 1024x1024, 1024x1536, 1536x1024, or "auto"
    )

    return resp.data[0].b64_json, target_w, target_h
