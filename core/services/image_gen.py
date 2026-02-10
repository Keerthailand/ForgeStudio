import base64
import os
import uuid
from pathlib import Path

from django.conf import settings
from openai import OpenAI


# Supported sizes for GPT image models (gpt-image-1 / gpt-image-1-mini)
_ALLOWED_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}


def generate_image_to_media(prompt: str, size: str = "auto") -> dict:
    """
    Generates an image using gpt-image-1-mini (MEDIUM quality only),
    saves it to MEDIA_ROOT/generated, and returns its URL.

    NOTE: GPT image models do NOT support 256x256 or 512x512.
    Supported: 1024x1024, 1024x1536, 1536x1024, auto.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Image prompt is empty")

    # Guardrail: if old code passes 512x512, don't crash the whole app
    size = (size or "auto").strip()
    if size not in _ALLOWED_SIZES:
        size = "auto"

    client = OpenAI(api_key=api_key)

    response = client.images.generate(
        model="gpt-image-1-mini",
        prompt=prompt,
        size=size,        # auto (default) or 1024x1024/1024x1536/1536x1024
        quality="medium", # LOCKED to medium for budget safety
    )

    b64_data = response.data[0].b64_json
    image_bytes = base64.b64decode(b64_data)

    out_dir = Path(settings.MEDIA_ROOT) / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"
    file_path = out_dir / filename
    file_path.write_bytes(image_bytes)

    media_url = (settings.MEDIA_URL or "/media/").rstrip("/") + "/"
    return {
        "url": f"{media_url}generated/{filename}",
        "path": str(file_path),
    }
