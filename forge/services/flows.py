def evaluate_brainstorm(answers: dict) -> dict:
    """
    Button-only flow. Answers keys:
      - goal: awareness | leads | trust | sales
      - audience_temp: cold | warm | hot
      - style: educational | entertaining | story | opinion
      - tone: bold | clean | friendly
      - platform: instagram | tiktok | x | facebook | linkedin
    """
    goal = answers.get("goal", "awareness")
    temp = answers.get("audience_temp", "cold")
    style = answers.get("style", "educational")
    tone = answers.get("tone", "clean")
    platform = answers.get("platform", "instagram")

    # Simple scoring logic
    best_content_type = None
    if style == "educational":
        best_content_type = "Quick tips carousel / thread / mini-tutorial"
    elif style == "entertaining":
        best_content_type = "Short-form hook-driven video"
    elif style == "story":
        best_content_type = "Personal story with lesson + CTA"
    else:
        best_content_type = "Strong opinion post with 3 supporting points"

    # Platform nuance
    platform_tip = {
        "instagram": "Use a bold first line + clean spacing + 3–8 hashtags.",
        "tiktok": "Fast hook in 1–2 seconds + on-screen text for every beat.",
        "x": "Keep it punchy, one clear point, end with a question.",
        "facebook": "Conversational tone, longer context, direct CTA.",
        "linkedin": "Professional value + bullets, minimal emojis, credibility."
    }.get(platform, "Keep it scannable and value-forward.")

    # Next tool suggestion (subtle)
    next_tools = []
    # If the user needs final posts -> Posting
    next_tools.append({"tool": "Posting", "why": "Generate platform-ready posts and previews from your chosen angle."})

    # If they have a draft -> Improve (only suggest when warm/hot or trust goal)
    if goal in ("trust", "sales") or temp in ("warm", "hot"):
        next_tools.append({"tool": "Improve", "why": "Refine your draft with three tone variants and polish."})

    # If video likely
    if platform in ("tiktok",) or best_content_type.lower().find("video") != -1:
        next_tools.append({"tool": "Script", "why": "Generate a HOOK/BODY/CTA script (1 min or 5 min) to match this angle."})

    # Output
    return {
        "headline": "Brainstorm Results",
        "recommendations": {
            "best_content_type": best_content_type,
            "best_platform": platform.title(),
            "best_tone": tone.title(),
            "audience_temperature": temp.title(),
        },
        "tips": [
            f"Goal focus: {goal.title()}",
            f"Platform tip: {platform_tip}",
            "Keep one message per post. One hook. One CTA.",
        ],
        "next_tools": next_tools[:3],
    }


def evaluate_plan(answers: dict) -> dict:
    """
    Button-only plan flow. Answers keys:
      - primary_goal: awareness | leads | trust | sales
      - seo_focus: none | light | strong
      - cadence: low | medium | high
      - format_mix: posts | video | mixed
      - funnel_stage: top | middle | bottom
    Outputs a high-level plan, NOT content.
    """
    goal = answers.get("primary_goal", "awareness")
    seo = answers.get("seo_focus", "light")
    cadence = answers.get("cadence", "medium")
    mix = answers.get("format_mix", "mixed")
    stage = answers.get("funnel_stage", "top")

    cadence_map = {
        "low": "3 posts/week",
        "medium": "5 posts/week",
        "high": "7–10 posts/week"
    }
    cadence_text = cadence_map.get(cadence, "5 posts/week")

    seo_map = {
        "none": "Focus on clarity and shareability instead of keywords.",
        "light": "Use 1–2 target phrases naturally in your hook and closing line.",
        "strong": "Pick 3 core keywords, repeat consistently in headlines, captions, and profile."
    }
    seo_direction = seo_map.get(seo, "Use clear language and keep keywords natural.")


    # Weekly structure (high-level)
    if mix == "posts":
        weekly = [
            "2x educational posts (how-to / tips)",
            "2x credibility posts (proof / results / story)",
            "1x engagement post (question / poll / hot take)",
        ]
    elif mix == "video":
        weekly = [
            "3x short-form videos (hook-driven tips)",
            "1x story video (personal lesson + CTA)",
            "1x Q&A video (answer common objection)",
        ]
    else:
        weekly = [
            "2x educational posts",
            "2x short-form videos",
            "1x story or proof piece",
        ]

    # Tool suggestions
    next_tools = [
        {"tool": "Forge Mode", "why": "Use Brainstorm to pick the best post angle each day."},
        {"tool": "Posting", "why": "Turn plan items into platform-ready posts and previews."},
    ]
    if mix in ("video", "mixed"):
        next_tools.append({"tool": "Script", "why": "Generate HOOK/BODY/CTA for your video slots."})

    if stage in ("middle", "bottom"):
        next_tools.append({"tool": "Improve", "why": "Polish credibility posts and conversion CTAs."})

    return {
        "headline": "Plan Results",
        "plan": {
            "primary_goal": goal.title(),
            "funnel_stage": stage.title(),
            "cadence": cadence_text,
            "format_mix": mix.title(),
            "seo_direction": seo_direction,
        },
        "weekly_structure": weekly,
        "operating_rules": [
            "Pick ONE message per piece.",
            "Repeat your key themes weekly (consistency beats variety).",
            "Track one metric tied to your goal (saves you from random posting).",
        ],
        "next_tools": next_tools[:3],
    }
