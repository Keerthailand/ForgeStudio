import base64
import os
import uuid
from pathlib import Path

from django.conf import settings
from openai import OpenAI


# Keep this tight to avoid accidental cost bumps
_ALLOWED_SIZES = {"256x256", "512x512", "1024x1024"}


def generate_image_to_media(prompt: str, size: str = "512x512", subdir: str = "generated") -> dict:
    """
    Generates an image using gpt-image-1-mini (MEDIUM quality only),
    saves it to MEDIA_ROOT/<subdir>, and returns its URL.

    Cost-safe defaults:
    - model: gpt-image-1-mini
    - quality: medium (LOCKED)
    - size: 512x512
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Image prompt is empty")

    if size not in _ALLOWED_SIZES:
        # Guardrail so you never accidentally pass something odd
        raise ValueError(f"Invalid size '{size}'. Allowed: {sorted(_ALLOWED_SIZES)}")

    # Default to "generated" if someone passes "" accidentally
    subdir = (subdir or "generated").strip().strip("/")

    client = OpenAI(api_key=api_key)

    response = client.images.generate(
        model="gpt-image-1-mini",
        prompt=prompt,
        size=size,
        quality="medium",  # LOCKED for budget safety
    )

    # Defensive parsing
    try:
        b64_data = response.data[0].b64_json
    except Exception as e:
        raise RuntimeError(f"Image generation response missing b64 data: {e}")

    image_bytes = base64.b64decode(b64_data)

    out_dir = Path(settings.MEDIA_ROOT) / subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"
    file_path = out_dir / filename
    file_path.write_bytes(image_bytes)

    # Normalize MEDIA_URL to avoid '//'
    media_url = (settings.MEDIA_URL or "/media/").strip()
    if not media_url.startswith("/"):
        media_url = "/" + media_url
    if not media_url.endswith("/"):
        media_url += "/"

    return {
        "url": f"{media_url}{subdir.strip('/')}/{filename}",
        "path": str(file_path),
    }   