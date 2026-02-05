import os

def _call_openai_chat(messages, temperature=0.7):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    # New SDK
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
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
            messages=messages,
            temperature=temperature,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return None


def _system_prompt():
    return (
        "You are ForgeStudio Anvil — an expert creative director.\n"
        "You do NOT generate final content.\n"
        "Your job: ask smart questions, clarify intent, and recommend the right ForgeStudio tool.\n\n"
        "Rules:\n"
        "1) Be friendly, calm, conversational, and strategic.\n"
        "2) No profanity or slurs.\n"
        "3) Do NOT write the final post/script. Instead, guide.\n"
        "4) End with ONE subtle suggestion of the next tool only if appropriate.\n"
        "   Tools: Posting, Improve, VideoScript, Forge Mode.\n"
        "5) Keep answers tight: 4–8 sentences, plus 1–3 short questions.\n"
    )


def _mock_reply(user_text: str):
    # Deterministic fallback: strategic guidance, not content generation
    lower = user_text.lower()

    # Heuristic tool suggestion
    if any(k in lower for k in ["rewrite", "fix", "improve", "make it better", "edit"]):
        tool = ("Improve", "If you want, jump into **Improve** and paste what you have — I’ll help you refine it with variants.")
    elif any(k in lower for k in ["video", "script", "hook", "cta", "tiktok", "youtube", "reel"]):
        tool = ("VideoScript", "If you’re ready, **Script** can generate a HOOK/BODY/CTA structure for a 1-min or 5-min video.")
    elif any(k in lower for k in ["plan", "strategy", "content calendar", "schedule", "cadence", "seo"]):
        tool = ("Forge Mode", "If you want structure, **Forge Mode** can help you brainstorm or build a high-level plan.")
    else:
        tool = ("Posting", "When you’re ready, **Posting** can forge the actual platform-ready version and previews.")

    assistant = (
        "Okay — I’ve got you ⚒️\n"
        "Before we pick a direction, let’s get three things clear:\n"
        "1) Who is this for (audience)?\n"
        "2) What’s the goal (attention, leads, trust, sales)?\n"
        "3) What tone do you want (bold, clean, friendly)?\n\n"
        "Answer those in one line each and I’ll guide the next best move."
    )

    return assistant, tool[1]


def anvil_reply(history):
    """
    history: list[{role, content}] with 'user'/'assistant' roles
    Returns: (assistant_message, subtle_suggestion)
    """
    # Build chat messages for OpenAI
    msgs = [{"role": "system", "content": _system_prompt()}]
    for item in history[-12:]:  # keep it snappy
        role = "assistant" if item["role"] == "assistant" else "user"
        msgs.append({"role": role, "content": item["content"]})

    # Ask model for guidance + suggestion in a consistent format
    user_instruction = (
        "Respond as Anvil.\n"
        "At the end add a line exactly like:\n"
        "Suggestion: <tool> — <one sentence>\n"
        "If no suggestion is appropriate, write:\n"
        "Suggestion: none\n"
    )
    msgs.append({"role": "user", "content": user_instruction})

    ai = _call_openai_chat(msgs, temperature=0.7)

    if not ai:
        # fallback
        last_user = ""
        for m in reversed(history):
            if m["role"] == "user":
                last_user = m["content"]
                break
        return _mock_reply(last_user)

    # Parse "Suggestion:" line
    lines = [ln.strip() for ln in ai.splitlines() if ln.strip()]
    suggestion_line = ""
    for ln in reversed(lines):
        if ln.lower().startswith("suggestion:"):
            suggestion_line = ln
            break

    assistant_lines = []
    for ln in lines:
        if ln.lower().startswith("suggestion:"):
            break
        assistant_lines.append(ln)

    assistant_message = "\n".join(assistant_lines).strip()

    subtle_suggestion = ""
    if suggestion_line:
        value = suggestion_line.split(":", 1)[1].strip()
        if value.lower() != "none":
            subtle_suggestion = value

    # If model forgets suggestion formatting, keep it empty
    return assistant_message, subtle_suggestion
