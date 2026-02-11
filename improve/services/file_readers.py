import base64
import json
import os
from typing import Optional, Tuple

from openai import OpenAI


VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", os.environ.get("OPENAI_TEXT_MODEL", "gpt-4o-mini"))


def _get_client() -> Optional[OpenAI]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _is_image(uploaded_file) -> bool:
    name = (uploaded_file.name or "").lower()

    if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return True

    ctype = (getattr(uploaded_file, "content_type", "") or "").lower()
    if ctype.startswith("image/"):
        return True

    return False


def _analyze_image_visual_only(uploaded_file) -> Tuple[str, str]:
    """
    Returns (image_context, note).
    This is VISUAL understanding only — NO OCR / no text extraction.
    """
    client = _get_client()
    if client is None:
        return "", "Image uploaded, but OPENAI_API_KEY is not set (image analysis skipped)."

    uploaded_file.seek(0)
    img_bytes = uploaded_file.read()

    mime = getattr(uploaded_file, "content_type", None) or "image/png"
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    data_url = f"data:{mime};base64,{b64}"

    prompt = (
        "Analyze this image visually to help generate NEW images based on it.\n"
        "IMPORTANT: Do NOT extract, quote, or transcribe any text from the image. No OCR.\n"
        "Return STRICT JSON only with these keys:\n"
        "{\n"
        '  "subject_summary": "what the image is mainly about",\n'
        '  "key_elements": ["notable objects/people/setting"],\n'
        '  "style_tags": ["style words like cinematic, cyberpunk, minimalist, watercolor, etc."],\n'
        '  "color_palette": ["3-6 colors described in words"],\n'
        '  "lighting_mood": "short lighting/mood description",\n'
        '  "composition": "short composition description (close-up, wide, centered, etc.)"\n'
        "}\n"
        "Keep it concise and useful for image generation.\n"
    )

    try:
        # Use the Responses API so we can send input_image
        resp = client.responses.create(
            model=VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )

        raw = (resp.output_text or "").strip()
        if not raw:
            return "", "Image analyzed (visual), but no output returned."

        # Parse JSON (be forgiving)
        try:
            parsed = json.loads(raw)
        except Exception:
            # If model returns non-JSON (rare), still pass it as context
            return raw, "Image analyzed (visual, non-JSON)."

        subject = (parsed.get("subject_summary") or "").strip()
        elems = parsed.get("key_elements") or []
        tags = parsed.get("style_tags") or []
        palette = parsed.get("color_palette") or []
        mood = (parsed.get("lighting_mood") or "").strip()
        comp = (parsed.get("composition") or "").strip()

        # Build a compact context string to merge into Improve input
        context = (
            "Reference image (visual analysis, no OCR):\n"
            f"- Subject: {subject}\n"
            f"- Key elements: {', '.join([str(x) for x in elems])}\n"
            f"- Style tags: {', '.join([str(x) for x in tags])}\n"
            f"- Color palette: {', '.join([str(x) for x in palette])}\n"
            f"- Lighting/mood: {mood}\n"
            f"- Composition: {comp}\n"
        ).strip()

        return context, "Image analyzed (visual)."

    except Exception:
        return "", "Image uploaded, but visual analysis failed."


def extract_text_from_upload(uploaded_file):
    """
    Returns: (text, note)

    NOTE:
    - For images, this returns a VISUAL ANALYSIS CONTEXT (not OCR text).
    - For PDFs, still not enabled.
    """
    name = (uploaded_file.name or "").lower()

    # ✅ Image support (visual-only analysis)
    if _is_image(uploaded_file):
        return _analyze_image_visual_only(uploaded_file)

    if name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text.strip(), "Loaded text from .txt file."

    if name.endswith(".docx"):
        # Optional dependency: python-docx
        try:
            import docx  # python-docx package
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs]).strip()
            if not text:
                return "", "DOCX uploaded, but no readable text found."
            return text, "Loaded text from .docx file."
        except Exception:
            return "", "DOCX uploaded, but DOCX parsing isn't available. Paste the text for best results."

    if name.endswith(".pdf"):
        return "", "PDF uploaded. For best results, paste the text you want improved (PDF parsing not enabled yet)."

    return "", "File uploaded, but that type isn’t supported yet. Use .txt, .docx, or paste text."
