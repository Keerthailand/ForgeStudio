import json
import os
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from core.services.image_gen import generate_image_to_media


TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL", "gpt-4o-mini")


def _get_client() -> Optional[OpenAI]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _sanitize_no_profanity(text: str) -> str:
    """
    Guardrail: ForgeStudio bots should not output profanity.
    This is not exhaustive, but prevents obvious slips.
    """
    if not text:
        return ""
    replacements = {
        r"\bfuck\b": "mess up",
        r"\bshit\b": "stuff",
        r"\bbitch\b": "jerk",
        r"\basshole\b": "rude person",
        r"\bwtf\b": "what the heck",
    }
    out = text
    for pat, repl in replacements.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.strip()


def _safe_json(raw: str) -> Optional[dict]:
    if not raw:
        return None
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Try extracting first {...} block
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            return None
    return None


def _wrap_image_prompt(concept: str, user_content: str, user_goal: str) -> str:
    """
    Professional IG-style by default. No text/logos/watermarks.
    Does NOT force medieval/forge aesthetic unless implied by the user content.
    """
    concept = (concept or "").strip()
    uc = (user_content or "").strip()
    ug = (user_goal or "").strip()

    base = (
        "Professional Instagram-style social media graphic. "
        "Clean, modern design, high contrast, strong visual hierarchy. "
        "Warm accent colors on dark background. Minimalist premium look. "
        "No text, no logos, no watermarks. "
        "Visual theme should closely match this concept: "
    )

    # Keep prompts bounded for stability/cost
    uc_short = uc[:700]
    ug_short = ug[:200]

    if concept:
        prompt = f"{base}{concept}. Context (no text): {uc_short}"
    else:
        prompt = f"{base}A visual concept that matches the user’s content. Context (no text): {uc_short}"

    if ug_short:
        prompt += f" User goal context: {ug_short}"

    return prompt.strip()


def improve_content_with_variants(user_content: str, user_goal: str = "", file_note: str = "") -> Dict[str, Any]:
    """
    Called by improve_analyze view.

    Inputs:
      - user_content: combined content (typed + extracted file text)
      - user_goal: optional goal
      - file_note: short note about file extraction (e.g., 'PDF parsed', 'DOCX extracted')

    Output:
      {
        "assistant_message": "...",
        "variants": [
          {"label","tone","improved_text","image_prompt","image_url"},
          ...
        ]
      }
    """
    user_content = (user_content or "").strip()
    user_goal = (user_goal or "").strip()
    file_note = (file_note or "").strip()

    if not user_content:
        return {"assistant_message": "Paste content or upload a file and I’ll improve it.", "variants": []}

    client = _get_client()

    # --------- If no API key, provide a safe fallback (no images) ----------
    if client is None:
        base = _sanitize_no_profanity(user_content[:1200])
        variants = [
            {
                "label": "Version A",
                "tone": "Bold + engaging",
                "improved_text": f"{base}\n\n(Upgrade: punchier hook, stronger flow, clearer call-to-action.)",
                "image_prompt": _wrap_image_prompt("Bold, energetic visual concept matching the content", user_content, user_goal),
                "image_url": "",
            },
            {
                "label": "Version B",
                "tone": "Clean + professional",
                "improved_text": f"{base}\n\n(Upgrade: structured, concise, professional wording.)",
                "image_prompt": _wrap_image_prompt("Clean, premium professional visual concept matching the content", user_content, user_goal),
                "image_url": "",
            },
            {
                "label": "Version C",
                "tone": "Friendly + conversational",
                "improved_text": f"{base}\n\n(Upgrade: warmer, more human, conversational tone.)",
                "image_prompt": _wrap_image_prompt("Friendly, approachable visual concept matching the content", user_content, user_goal),
                "image_url": "",
            },
        ]
        return {
            "assistant_message": "I don’t see an OpenAI key set, but here are three draft variants to start with.",
            "variants": variants,
        }

    # --------- OpenAI: produce JSON-only (3 variants + 3 image concepts) ----------
    goal_text = user_goal or "Improve clarity, structure, and impact while staying true to the original meaning."
    note_text = f"(File note: {file_note})" if file_note else ""

    system = (
        "You are ForgeStudio Improve — an expert editor and content strategist.\n"
        "Hard rules:\n"
        "1) Do NOT output profanity.\n"
        "2) Preserve meaning; improve clarity, structure, and persuasion.\n"
        "3) No medical/legal claims. No unsafe instructions.\n"
        "4) Provide exactly 3 variants: A bold/engaging, B clean/professional, C friendly/conversational.\n"
        "5) Provide a short image concept for each (visual-only). Do NOT request text/logos/watermarks.\n"
        "6) Output must be valid JSON only. No extra commentary outside JSON.\n"
    )

    prompt_obj = {
        "goal": goal_text,
        "content": user_content[:7000],  # bound for cost/stability
        "note": note_text,
        "required_output": {
            "assistant_message": "short, friendly explanation of what you changed",
            "variants": [
                {
                    "label": "Version A",
                    "tone": "Bold + engaging",
                    "improved_text": "string",
                    "image_concept": "visual-only concept (no text/logos/watermarks)",
                },
                {
                    "label": "Version B",
                    "tone": "Clean + professional",
                    "improved_text": "string",
                    "image_concept": "visual-only concept (no text/logos/watermarks)",
                },
                {
                    "label": "Version C",
                    "tone": "Friendly + conversational",
                    "improved_text": "string",
                    "image_concept": "visual-only concept (no text/logos/watermarks)",
                },
            ],
        },
    }

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(prompt_obj)},
            ],
        )
        raw = resp.choices[0].message.content or ""
        parsed = _safe_json(raw) or {}
    except Exception:
        parsed = {}

    assistant_message = _sanitize_no_profanity(parsed.get("assistant_message") or "")
    variants_in = parsed.get("variants") if isinstance(parsed.get("variants"), list) else []

    # Normalize to exactly 3 variants, always present
    fallback_defs = [
        ("Version A", "Bold + engaging", "Bold, energetic visual concept matching the content"),
        ("Version B", "Clean + professional", "Clean, premium professional visual concept matching the content"),
        ("Version C", "Friendly + conversational", "Friendly, approachable visual concept matching the content"),
    ]

    variants_out: List[Dict[str, Any]] = []

    for i in range(3):
        label, tone, fallback_concept = fallback_defs[i]
        v = variants_in[i] if i < len(variants_in) and isinstance(variants_in[i], dict) else {}

        improved_text = _sanitize_no_profanity(v.get("improved_text") or "")
        image_concept = (v.get("image_concept") or "").strip()

        if not improved_text:
            improved_text = _sanitize_no_profanity(user_content[:1400])

        if not image_concept:
            image_concept = fallback_concept

        image_prompt = _wrap_image_prompt(image_concept, user_content, user_goal)

        variants_out.append(
            {
                "label": label,
                "tone": tone,
                "improved_text": improved_text,
                "image_prompt": image_prompt,
                "image_url": "",  # fill after generation
            }
        )

    if not assistant_message:
        assistant_message = "Got it 🔥 I tightened the writing and forged three strong options you can choose from."

    # --------- Generate images (locked budget settings via your image_gen.py) ----------
    v["image_url"] = ""


    return {"assistant_message": assistant_message, "variants": variants_out}
