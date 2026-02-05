import os
import openai

API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

def forge_brainstorm(choice, session_history=None):
    """
    Suggests the best content type, tone, and platform based on button choice.
    Returns recommendation + next suggested ForgeStudio tool.
    """
    session_history = session_history or []
    return f"Brainstorm result for '{choice}': Best content type is Instagram Carousel. Suggested tool next: Posting."

def forge_plan(choice, session_history=None):
    """
    Provides high-level plan based on button-driven marketing goals.
    Outputs marketing strategy, SEO direction, posting cadence.
    """
    session_history = session_history or []
    return f"Plan result for '{choice}': Post 3x/week, focus on SEO keywords, use ForgeStudio Posting and Improve tools."
