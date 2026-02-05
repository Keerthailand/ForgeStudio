import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services.ai import anvil_reply


SESSION_KEY = "anvil_messages"


def _get_history(request):
    return request.session.get(SESSION_KEY, [])


def _set_history(request, history):
    request.session[SESSION_KEY] = history
    request.session.modified = True


def anvil_view(request):
    # Ensure a starter message exists
    history = _get_history(request)
    if not history:
        history = [
            {
                "role": "assistant",
                "content": "Welcome back to the anvil ⚒️\nTell me what you’re trying to create — and I’ll help you choose the smartest next move.",
            }
        ]
        _set_history(request, history)

    return render(request, "anvil/anvil.html")


@require_POST
def anvil_chat(request):
    """
    JSON body: { "message": "..." }
    Uses session-stored conversation history.
    Returns: { assistant_message, subtle_suggestion, history }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        user_msg = (data.get("message") or "").strip()
        if not user_msg:
            return JsonResponse({"error": "Say something and I’ll help."}, status=400)

        history = _get_history(request)
        history.append({"role": "user", "content": user_msg})

        assistant_message, subtle_suggestion = anvil_reply(history)

        history.append({"role": "assistant", "content": assistant_message})
        _set_history(request, history)

        return JsonResponse({
            "assistant_message": assistant_message,
            "subtle_suggestion": subtle_suggestion,
        })

    except Exception:
        return JsonResponse({"error": "Something went wrong. Try again."}, status=500)


@require_POST
def anvil_reset(request):
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    return JsonResponse({"ok": True})
