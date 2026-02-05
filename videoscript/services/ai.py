import os
import textwrap

def _call_openai_chat(system, user, temperature=0.7):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    # New SDK
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
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
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            temperature=temperature,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return None


def build_videoscript_prompt(topic: str, length: str, platform: str):
    seconds = 60 if length == "short" else 300
    pacing = "fast, punchy, high retention" if length == "short" else "clear, paced, story-driven"
    plat = platform if platform else "general"

    system = (
        "You are ForgeStudio VideoScript, a friendly expert video scriptwriter.\n"
        "RULES:\n"
        "1) No profanity or slurs.\n"
        "2) Be warm, confident, and conversational.\n"
        "3) Output must be structured with headings: HOOK, BODY, CTA.\n"
        "4) BODY must include clear beats and suggested on-screen cues.\n"
        "5) Keep it approximately the requested duration.\n"
    )

    user = (
        f"Topic: {topic}\n"
        f"Length: {length} (~{seconds} seconds)\n"
        f"Platform: {plat}\n"
        f"Pacing: {pacing}\n\n"
        "Write a complete script with:\n"
        "- HOOK (0–5s short / 0–15s long)\n"
        "- BODY (beats with timestamps or sections + on-screen cues)\n"
        "- CTA (clear call to action)\n\n"
        "Also include a short 'Creator Notes' section at the end with filming tips.\n"
    )

    return system, user


def _mock_script(topic: str, length: str, platform: str):
    if length == "short":
        return textwrap.dedent(f"""
        HOOK (0–5s)
        “If you’ve been struggling with {topic}, this will save you time.”

        BODY (5–55s)
        Beat 1 (5–15s): What most people do wrong.
        [On-screen text]: “Stop doing THIS”
        Beat 2 (15–35s): The simple fix in 2 steps.
        [On-screen text]: “Do THIS instead”
        Beat 3 (35–55s): Quick example + result.
        [On-screen text]: “Example”

        CTA (55–60s)
        “If you want a checklist for {topic}, comment ‘FORGE’ and I’ll send it.”

        Creator Notes
        - Keep cuts every 1–2 seconds.
        - Use bold captions.
        - Platform: {platform or "any"} (frame it accordingly).
        """).strip()

    return textwrap.dedent(f"""
    HOOK (0–15s)
    “Today we’re breaking down {topic} — and by the end, you’ll know exactly what to do next.”

    BODY (15s–4m30s)
    Section 1: The real problem (15s–1m30s)
    - Define the problem in plain English.
    - Why it matters.
    [On-screen]: “The real issue is…”

    Section 2: The framework (1m30s–3m30s)
    Step 1: Identify your starting point.
    Step 2: Apply the simplest high-leverage change.
    Step 3: Track one metric that proves it’s working.
    [On-screen]: “3-step framework”

    Section 3: Example + common mistakes (3m30s–4m30s)
    - Walk through a realistic example.
    - Call out 2 common mistakes and fixes.
    [On-screen]: “Example + Fix”

    CTA (4m30s–5m)
    “If you want me to build a plan for your exact situation, drop your details in the comments or DM me.”

    Creator Notes
    - Add chapter cards between sections.
    - Slow down for key steps and use b-roll overlays.
    - Platform: {platform or "any"} (add formatting cues for it).
    """).strip()


def generate_script_package(topic: str, length: str, platform: str):
    system, user = build_videoscript_prompt(topic, length, platform)
    ai = _call_openai_chat(system, user, temperature=0.75)

    script_text = ai.strip() if ai else _mock_script(topic, length, platform)

    assistant_message = (
        "Done 🔥 I forged a full script with a strong hook, clean structure, and a clear CTA.\n"
        "You can read it below or download it as a file."
    )

    download_text = f"ForgeStudio Video Script\nTopic: {topic}\nLength: {length}\nPlatform: {platform or 'general'}\n\n{script_text}\n"

    return {
        "assistant_message": assistant_message,
        "script": script_text,
        "download_text": download_text,
    }
