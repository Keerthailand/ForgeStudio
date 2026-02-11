import json
import os
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI


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

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            return None
    return None


def _wrap_image_prompt(concept: str, user_content: str, user_goal: str, variant_label: str) -> str:
    """
    Forces each variant to have a distinct art direction.
    Still: social-media-ready, no text/logos/watermarks.
    """
    concept = (concept or "").strip()
    uc = (user_content or "").strip()
    ug = (user_goal or "").strip()

    # Bound context
    uc_short = uc[:700]
    ug_short = ug[:200]

    # Strongly distinct directions (palette + style + composition)
    presets = {
        "Version A": (
            "Art direction: Bold, high-energy, cinematic poster vibe. "
            "Dynamic composition, dramatic lighting, strong contrast. "
            "Use a vibrant accent palette (not primarily orange). "
            "Add motion/energy through shapes or lighting."
        ),
        "Version B": (
            "Art direction: Minimal, premium, brand-like design. "
            "Lots of negative space, subtle gradients, elegant geometry. "
            "Use a neutral palette with ONE accent color (not the same as Version A). "
            "Clean, calm, sophisticated."
        ),
        "Version C": (
            "Art direction: Friendly, playful, approachable. "
            "Softer lighting, rounded shapes, slightly whimsical illustration feel. "
            "Use a brighter, more colorful palette (not the same as A or B). "
            "Warm and inviting without looking childish."
        ),
    }
    direction = presets.get(variant_label, presets["Version B"])

    base = (
        "Create a social-media-ready graphic background image. "
        "No text, no typography, no letters, no logos, no watermarks. "
        "Avoid repeating the same composition or palette as the other variants. "
        "Visual theme must closely match this concept: "
    )

    if concept:
        prompt = f"{base}{concept}. {direction} Context (no text): {uc_short}"
    else:
        prompt = f"{base}A visual concept that matches the user's content. {direction} Context (no text): {uc_short}"

    if ug_short:
        prompt += f" User goal context: {ug_short}"

    # Add a uniqueness cue so prompts don't collapse into the same look
    prompt += f" Unique cue: {variant_label}."

    return prompt.strip()


def improve_content_with_variants(user_content: str, user_goal: str = "", file_note: str = "") -> Dict[str, Any]:
    """
    Called by improve_analyze view.

    Returns JSON with:
      - assistant_message
      - variants: [{label, tone, improved_text, image_prompt, image_url}]
    """
    user_content = (user_content or "").strip()
    user_goal = (user_goal or "").strip()
    file_note = (file_note or "").strip()

    if not user_content:
        return {"assistant_message": "Paste content or upload a file and I’ll improve it.", "variants": []}

    client = _get_client()

    # --------- No API key fallback (text-only, prompts still varied) ----------
    if client is None:
        base = _sanitize_no_profanity(user_content[:1200])
        variants = [
            {
                "label": "Version A",
                "tone": "Bold + engaging",
                "improved_text": f"{base}\n\n(Upgrade: punchier hook, stronger flow, clearer call-to-action.)",
                "image_prompt": _wrap_image_prompt(
                    "Bold, energetic visual concept matching the content",
                    user_content,
                    user_goal,
                    "Version A",
                ),
                "image_url": "",
            },
            {
                "label": "Version B",
                "tone": "Clean + professional",
                "improved_text": f"{base}\n\n(Upgrade: structured, concise, professional wording.)",
                "image_prompt": _wrap_image_prompt(
                    "Clean, premium professional visual concept matching the content",
                    user_content,
                    user_goal,
                    "Version B",
                ),
                "image_url": "",
            },
            {
                "label": "Version C",
                "tone": "Friendly + conversational",
                "improved_text": f"{base}\n\n(Upgrade: warmer, conversational tone.)",
                "image_prompt": _wrap_image_prompt(
                    "Friendly, approachable visual concept matching the content",
                    user_content,
                    user_goal,
                    "Version C",
                ),
                "image_url": "",
            },
        ]
        return {
            "assistant_message": "I don’t see an OpenAI key set, but here are three draft variants to start with.",
            "variants": variants,
        }

    # --------- OpenAI: JSON-only (3 variants + 3 DISTINCT image concepts) ----------
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
        "6) The three image_concept values must be VERY DIFFERENT:\n"
        "   - Different palette (not all dark/orange)\n"
        "   - Different composition (close-up vs wide vs abstract)\n"
        "   - Different style (cinematic vs minimalist vs playful)\n"
        "7) Output must be valid JSON only. No extra commentary outside JSON.\n"
    )

    prompt_obj = {
        "goal": goal_text,
        "content": user_content[:7000],
        "note": note_text,
        "required_output": {
            "assistant_message": "short, friendly explanation of what you changed",
            "variants": [
                {
                    "label": "Version A",
                    "tone": "Bold + engaging",
                    "improved_text": "string",
                    "image_concept": "visual-only concept (no text/logos/watermarks) - cinematic/poster style",
                },
                {
                    "label": "Version B",
                    "tone": "Clean + professional",
                    "improved_text": "string",
                    "image_concept": "visual-only concept (no text/logos/watermarks) - minimalist/brand style",
                },
                {
                    "label": "Version C",
                    "tone": "Friendly + conversational",
                    "improved_text": "string",
                    "image_concept": "visual-only concept (no text/logos/watermarks) - playful/approachable style",
                },
            ],
        },
    }

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            temperature=0.85,  # a bit higher to help diversity
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

    fallback_defs = [
        ("Version A", "Bold + engaging", "Cinematic, energetic poster-style concept"),
        ("Version B", "Clean + professional", "Minimalist, premium brand-style concept"),
        ("Version C", "Friendly + conversational", "Playful, friendly illustration-style concept"),
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

        image_prompt = _wrap_image_prompt(image_concept, user_content, user_goal, label)

        variants_out.append(
            {
                "label": label,
                "tone": tone,
                "improved_text": improved_text,
                "image_prompt": image_prompt,
                "image_url": "",  # generated later (sequential endpoint)
            }
        )

    if not assistant_message:
        assistant_message = "Got it 🔥 I tightened the writing and forged three strong options you can choose from."

    return {"assistant_message": assistant_message, "variants": variants_out}
