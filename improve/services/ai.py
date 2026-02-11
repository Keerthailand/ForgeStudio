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


def _redact_names_for_image_prompts(text: str) -> str:
    """
    Optional guardrail: for image prompts, avoid using potentially copyrighted
    character names directly. Replace with a generic description.

    You can expand this list later if needed.
    """
    if not text:
        return ""
    # Example: if user says "Thorfinn", use a general description in image prompts
    text = re.sub(r"\bthorfinn\b", "a young Viking warrior", text, flags=re.IGNORECASE)
    return text.strip()


def _extract_variant_concepts(client: OpenAI, user_content: str, user_goal: str) -> List[Dict[str, str]]:
    """
    Analyze the user's request and extract THREE distinct visual concepts
    for Version A/B/C. This prevents sending the same combined prompt to all images.

    Returns:
      [{"label":"Version A","concept":"..."}, {"label":"Version B","concept":"..."}, {"label":"Version C","concept":"..."}]
    """
    text = (user_content or "").strip()
    goal = (user_goal or "").strip()

    system = (
        "You are a prompt analyst. Extract variant requests from user text.\n"
        "Return STRICT JSON only.\n"
        "Rules:\n"
        "- If user asks for multiple versions (e.g., cyberpunk / arctic / India), split them into separate concepts.\n"
        "- Produce exactly 3 concepts mapped to Version A, Version B, Version C.\n"
        "- If fewer than 3 are requested, invent additional distinct concepts consistent with the request.\n"
        "- Concepts must be concise, visual-only, and MUST NOT include text/logos/watermarks.\n"
        "- Do not use copyrighted character names; describe characters generically.\n"
    )

    payload = {
        "user_text": text[:2500],
        "user_goal": goal[:300],
        "output_schema": {
            "requested_variants": [
                {"label": "Version A", "concept": "visual-only concept"},
                {"label": "Version B", "concept": "visual-only concept"},
                {"label": "Version C", "concept": "visual-only concept"},
            ]
        },
    }

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        raw = resp.choices[0].message.content or ""
        parsed = _safe_json(raw) or {}
    except Exception:
        parsed = {}

    arr = parsed.get("requested_variants")
    if not isinstance(arr, list) or len(arr) == 0:
        # fallback: still provide three distinct settings
        base = _redact_names_for_image_prompts(text[:600])
        return [
            {"label": "Version A", "concept": f"A bold cinematic version of: {base}"},
            {"label": "Version B", "concept": f"A minimalist premium version of: {base}"},
            {"label": "Version C", "concept": f"A friendly playful version of: {base}"},
        ]

    out: List[Dict[str, str]] = []
    labels = ["Version A", "Version B", "Version C"]

    for i, label in enumerate(labels):
        item = arr[i] if i < len(arr) and isinstance(arr[i], dict) else {}
        concept = (item.get("concept") or "").strip()
        concept = _redact_names_for_image_prompts(concept)
        if not concept:
            concept = "A distinct visual-only version of the user's request"
        out.append({"label": label, "concept": concept})

    return out


def _wrap_image_prompt(concept: str, user_content: str, user_goal: str, variant_label: str) -> str:
    """
    Forces each variant to have a distinct art direction.
    Still: social-media-ready, no text/logos/watermarks.
    """
    concept = (concept or "").strip()
    uc = (user_content or "").strip()
    ug = (user_goal or "").strip()

    uc_short = uc[:700]
    ug_short = ug[:200]

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

    prompt += f" Unique cue: {variant_label}."
    return prompt.strip()


def improve_content_with_variants(user_content: str, user_goal: str = "", file_note: str = "") -> Dict[str, Any]:
    """
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

    # --------- No API key fallback ----------
    if client is None:
        base = _sanitize_no_profanity(user_content[:1200])
        return {
            "assistant_message": "I don’t see an OpenAI key set, but here are three draft variants to start with.",
            "variants": [
                {
                    "label": "Version A",
                    "tone": "Bold + engaging",
                    "improved_text": f"{base}\n\n(Upgrade: punchier hook, stronger flow, clearer call-to-action.)",
                    "image_prompt": _wrap_image_prompt("Bold cinematic version of the idea", user_content, user_goal, "Version A"),
                    "image_url": "",
                },
                {
                    "label": "Version B",
                    "tone": "Clean + professional",
                    "improved_text": f"{base}\n\n(Upgrade: structured, concise, professional wording.)",
                    "image_prompt": _wrap_image_prompt("Minimal premium version of the idea", user_content, user_goal, "Version B"),
                    "image_url": "",
                },
                {
                    "label": "Version C",
                    "tone": "Friendly + conversational",
                    "improved_text": f"{base}\n\n(Upgrade: warmer, conversational tone.)",
                    "image_prompt": _wrap_image_prompt("Friendly playful version of the idea", user_content, user_goal, "Version C"),
                    "image_url": "",
                },
            ],
        }

    # ✅ NEW: extract 3 distinct image concepts first (splits multi-version requests)
    variant_concepts = _extract_variant_concepts(client, user_content, user_goal)

    # --------- OpenAI: JSON-only writing variants ----------
    goal_text = user_goal or "Improve clarity, structure, and impact while staying true to the original meaning."
    note_text = f"(File note: {file_note})" if file_note else ""

    system = (
        "You are ForgeStudio Improve — an expert editor and content strategist.\n"
        "Hard rules:\n"
        "1) Do NOT output profanity.\n"
        "2) Preserve meaning; improve clarity, structure, and persuasion.\n"
        "3) No medical/legal claims. No unsafe instructions.\n"
        "4) Provide exactly 3 variants: A bold/engaging, B clean/professional, C friendly/conversational.\n"
        "5) Output must be valid JSON only. No extra commentary outside JSON.\n"
    )

    prompt_obj = {
        "goal": goal_text,
        "content": user_content[:7000],
        "note": note_text,
        "required_output": {
            "assistant_message": "short, friendly explanation of what you changed",
            "variants": [
                {"label": "Version A", "tone": "Bold + engaging", "improved_text": "string"},
                {"label": "Version B", "tone": "Clean + professional", "improved_text": "string"},
                {"label": "Version C", "tone": "Friendly + conversational", "improved_text": "string"},
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

    fallback_defs = [
        ("Version A", "Bold + engaging"),
        ("Version B", "Clean + professional"),
        ("Version C", "Friendly + conversational"),
    ]

    variants_out: List[Dict[str, Any]] = []

    for i in range(3):
        label, tone = fallback_defs[i]
        v = variants_in[i] if i < len(variants_in) and isinstance(variants_in[i], dict) else {}

        improved_text = _sanitize_no_profanity(v.get("improved_text") or "")
        if not improved_text:
            improved_text = _sanitize_no_profanity(user_content[:1400])

        # ✅ Use the parsed concept for THIS label
        concept_for_label = variant_concepts[i]["concept"]
        image_prompt = _wrap_image_prompt(concept_for_label, user_content, user_goal, label)

        variants_out.append(
            {
                "label": label,
                "tone": tone,
                "improved_text": improved_text,
                "image_prompt": image_prompt,
                "image_url": "",  # generated later
            }
        )

    if not assistant_message:
        assistant_message = "Got it 🔥 I tightened the writing and forged three strong options you can choose from."

    return {"assistant_message": assistant_message, "variants": variants_out}
