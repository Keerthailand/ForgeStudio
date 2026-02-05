import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

from .services.ai import generate_script_package


def videoscript_view(request):
    return render(request, "videoscript/videoscript.html")


@require_POST
def videoscript_generate(request):
    """
    JSON body:
      {
        "topic": "what the video is about",
        "length": "short" | "long",
        "platform": "instagram" | "tiktok" | "youtube" | "linkedin" | "" (optional)
      }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        topic = (data.get("topic") or "").strip()
        length = (data.get("length") or "short").strip().lower()
        platform = (data.get("platform") or "").strip().lower()

        if not topic:
            return JsonResponse({"error": "Type a topic first — what’s the video about?"}, status=400)

        if length not in ("short", "long"):
            length = "short"

        pkg = generate_script_package(topic=topic, length=length, platform=platform)

        # Store last generated script in session for download
        request.session["videoscript_last"] = pkg["download_text"]

        return JsonResponse(pkg)

    except Exception:
        return JsonResponse({"error": "Something went wrong generating your script. Try again."}, status=500)


def videoscript_download(request):
    """
    Downloads the last generated script as a .txt file.
    """
    text = request.session.get("videoscript_last")
    if not text:
        return HttpResponse("No script available yet. Generate one first.", status=400)

    resp = HttpResponse(text, content_type="text/plain; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="forgestudio_script.txt"'
    return resp
