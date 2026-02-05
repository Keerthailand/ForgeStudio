import os
import re

# --- Optional OpenAI integration (supports both old and new SDK) ---
def _openai_available():
    return bool(os.environ.get("OPENAI_API_KEY"))

def _call_openai_chat(system, user, temperature=0.7):
    """
    Attempts to call OpenAI with either:
      - New SDK: from openai import OpenAI
      - Old SDK: import openai
    Returns assistant text.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    # New SDK
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception:
        pass

    # Old SDK fallback
    try:
        import openai
        openai.api_key = api_key
        resp = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return None


def _strip_profanity_output(text: str) -> str:
    """
    Light safeguard (not a giant list). If AI slips, we soften it.
    We keep this minimal and avoid maintaining huge dictionaries.
    """
    if not text:
        return text
    # Replace a few common hard hits with softened alternatives
    replacements = {
        r"\bfuck\b": "mess up",
        r"\bshit\b": "stuff",
        r"\bbitch\b": "jerk",
        r"\basshole\b": "rude person",
    }
    out = text
    for pattern, repl in replacements.items():
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    return out


def improve_content_with_variants(user_content: str, user_goal: str = "", file_note: str = ""):
    """
    Returns dict:
      assistant_message
      variants: [{label, tone, improved_text, image_prompt, image_url}]
    """
    goal_line = user_goal.strip() if user_goal.strip() else "Improve clarity, structure, and impact while staying true to the original meaning."
    note_line = f"\nContext note: {file_note}" if file_note else ""

    system = (
        "You are ForgeStudio Improve — a friendly, expert editor and strategist.\n"
        "RULES:\n"
        "1) Do NOT output profanity or slurs.\n"
        "2) If the user content contains harsh language, rewrite it into a professional, clean version.\n"
        "3) Preserve meaning, improve readability, and sharpen the message.\n"
        "4) Output should be polished and ready to post.\n"
        "5) No medical/legal claims. No unsafe instructions.\n"
    )

    # We ask for structured output that we can split cleanly.
    user = (
        f"User goal:\n{goal_line}\n\n"
        f"Content to improve:\n{user_content}\n"
        f"{note_line}\n\n"
        "Create THREE improved versions labeled exactly:\n"
        "Version A (bold + engaging)\n"
        "Version B (clean + professional)\n"
        "Version C (friendly + conversational)\n\n"
        "Under each version, output the improved text only.\n"
        "Also provide ONE image prompt per version in a separate section labeled:\n"
        "Image Prompts:\n"
        "A: ...\nB: ...\nC: ...\n"
    )

    ai_text = _call_openai_chat(system, user, temperature=0.7)

    # If AI isn’t available, return deterministic mock that’s still clean + useful
    if not ai_text:
        base = user_content.strip()
        return {
            "assistant_message": (
                "Alright 🔥 I’ve got your draft on the anvil. Here are three improved versions you can choose from."
            ),
            "variants": [
                {
                    "label": "Version A",
                    "tone": "Bold + engaging",
                    "improved_text": f"{base}\n\n(Improved A: stronger hook, punchier lines, clearer CTA.)",
                    "image_prompt": "Fantasy forge-themed social post graphic, warm orange glow, sparks, cinematic lighting.",
                    "image_url": "https://via.placeholder.com/1024x1024.png?text=Improve+Image+A"
                },
                {
                    "label": "Version B",
                    "tone": "Clean + professional",
                    "improved_text": f"{base}\n\n(Improved B: concise, structured, professional tone.)",
                    "image_prompt": "Minimal forge aesthetic, dark metal texture background, subtle ember glow, clean typography.",
                    "image_url": "https://via.placeholder.com/1024x1024.png?text=Improve+Image+B"
                },
                {
                    "label": "Version C",
                    "tone": "Friendly + conversational",
                    "improved_text": f"{base}\n\n(Improved C: warm, human, conversational phrasing.)",
                    "image_prompt": "Friendly forge workshop scene, warm light, sparks, cozy fantasy aesthetic, social media graphic.",
                    "image_url": "https://via.placeholder.com/1024x1024.png?text=Improve+Image+C"
                },
            ]
        }

    # Parse AI output into versions + image prompts
    # We keep parsing resilient to minor formatting differences.
    text = ai_text.strip()

    def extract_block(label):
      # find "Version A" and capture until next "Version" or "Image Prompts"
      pattern = rf"{label}\s*\(.*?\)\s*\n(.*?)(?=\nVersion [ABC]\b|\nImage Prompts:|\Z)"
      m = re.search(pattern, text, flags=re.S | re.I)
      return (m.group(1).strip() if m else "").strip()

    a = extract_block("Version A")
    b = extract_block("Version B")
    c = extract_block("Version C")

    def extract_img(letter):
      m = re.search(rf"^{letter}\s*:\s*(.+)$", text, flags=re.M | re.I)
      return m.group(1).strip() if m else "Fantasy forge aesthetic, warm orange embers, cinematic social graphic."

    img_a = extract_img("A")
    img_b = extract_img("B")
    img_c = extract_img("C")

    # Light safety polish
    a = _strip_profanity_output(a)
    b = _strip_profanity_output(b)
    c = _strip_profanity_output(c)

    # Image URLs: placeholder now (swap to real image API later)
    return {
        "assistant_message": (
            "Got it 🔥 I cleaned up the tone, sharpened the structure, and forged three strong options. "
            "Pick the one that matches your vibe."
        ),
        "variants": [
            {"label": "Version A", "tone": "Bold + engaging", "improved_text": a, "image_prompt": img_a,
             "image_url": "https://via.placeholder.com/1024x1024.png?text=Improve+Image+A"},
            {"label": "Version B", "tone": "Clean + professional", "improved_text": b, "image_prompt": img_b,
             "image_url": "https://via.placeholder.com/1024x1024.png?text=Improve+Image+B"},
            {"label": "Version C", "tone": "Friendly + conversational", "improved_text": c, "image_prompt": img_c,
             "image_url": "https://via.placeholder.com/1024x1024.png?text=Improve+Image+C"},
        ]
    }
