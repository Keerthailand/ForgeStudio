from dataclasses import dataclass
from core.services.image_gen import generate_image_to_media


@dataclass
class PostingResult:
    assistant_message: str
    instagram: str
    x: str
    facebook: str
    linkedin: str
    image_prompt: str
    image_url: str  # can be None if generation fails
    variants: list


def build_posting_prompts(user_prompt: str) -> dict:
    system = (
        "You are ForgeStudio Posting, a friendly expert social media writer. "
        "RULES:\n"
        "1) Do not output profanity or slurs.\n"
        "2) If the user includes harsh language, rewrite it into a professional, clean version.\n"
        "3) Keep the meaning, but clean the tone.\n"
        "4) Output must be high-quality and platform-appropriate.\n"
        "5) Return output as JSON ONLY.\n"
    )

    user = (
        "User idea (may include harsh language):\n"
        f"{user_prompt}\n\n"
        "Task:\n"
        "Generate ONE core message, then adapt it for each platform:\n"
        "- Instagram: energetic, emoji-friendly, 1–2 short paragraphs, 3–8 hashtags.\n"
        "- X: punchy, <= 280 chars, 1–2 relevant hashtags.\n"
        "- Facebook: conversational, slightly longer, clear call-to-action.\n"
        "- LinkedIn: professional, value-focused, minimal emojis, 3 bullet points max.\n\n"
        "Return JSON with keys: instagram, x, facebook, linkedin.\n"
    )

    image_prompt = (
        "Professional Instagram-style social media graphic. "
        "Clean, modern design, high contrast, strong visual hierarchy. "
        "Never use blacksmith theme."
        "Never use fire."
        "All images should not include a combination of dark colors, use only if specified."
        "No text, no logos, no watermarks. "
        "Visual theme should closely match this concept: {user_prompt}"
)


    return {"system": system, "user": user, "image_prompt": image_prompt}


def _safe_generate_image(prompt: str):
    try:
        img = generate_image_to_media(prompt, size="1024x1024")
        return img.get("url")
    except Exception:
        return None


def generate_post_with_image(user_prompt: str) -> PostingResult:
    """
    Generates platform-specific post text + a real generated image saved in MEDIA_ROOT.
    (Text is still mock here; swap in your OpenAI chat call when ready.)
    """
    user_prompt = (user_prompt or "").strip()

    assistant_message = (
        "Got it 🔥 I’m heating this up in the forge now.\n"
        "Here’s a polished set of posts — plus a matching image."
    )

    # Mock platform text (replace with model output)
    instagram = f"🔥 {user_prompt}\n\nHere’s the move: keep it simple, bold, and scroll-stopping.\n#ForgeStudio #ContentCreation #Marketing"
    x = f"{user_prompt} 🔥\nForge it. Post it. Grow it. #content"
    facebook = f"{user_prompt}\n\nIf you want, tell me your audience and I’ll tune the tone even tighter."
    linkedin = f"{user_prompt}\n\n• Clear value\n• Strong hook\n• Simple CTA\n\n#marketing #content"

    # Real image generation
    image_prompt = (
        "Fantasy forge / medieval blacksmith social media graphic, cinematic lighting, "
        "warm orange embers and sparks, dark metal textures, clean composition, "
        f"theme: {user_prompt}, no text, no logos"
    )
    image_url = _safe_generate_image(image_prompt)

    variants = [
        {
            "label": "Version A",
            "tone": "Bold + hype",
            "instagram": instagram.replace("keep it simple, bold, and scroll-stopping", "go loud, confident, and instantly attention-grabbing"),
            "x": x.replace("Forge it. Post it. Grow it.", "Hammer it. Post it. Win."),
        },
        {
            "label": "Version B",
            "tone": "Clean + minimal",
            "instagram": f"{user_prompt}\n\nClean message. Clear benefit. Strong CTA.\n#ForgeStudio #Brand",
            "x": f"{user_prompt} — clean, clear, and ready to ship.",
        },
        {
            "label": "Version C",
            "tone": "Friendly + casual",
            "instagram": f"Okayyy this is a fun one 😄\n\n{user_prompt}\n\nLet’s make it feel human + real.\n#ForgeStudio #Creator",
            "x": f"{user_prompt} 😄 Let’s keep it real and post-worthy.",
        },
    ]

    return PostingResult(
        assistant_message=assistant_message,
        instagram=instagram,
        x=x,
        facebook=facebook,
        linkedin=linkedin,
        image_prompt=image_prompt,
        image_url=image_url,
        variants=variants
    )
