import json
import traceback

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.services.image_gen import generate_image_to_media
from .services.ai import improve_content_with_variants
from .services.file_readers import extract_text_from_upload


def improve_view(request):
    return render(request, "improve/improve.html")


@require_POST
def improve_analyze(request):
    """
    Expects multipart/form-data:
      - content (optional)
      - file (optional)
      - goal (optional)
    Returns JSON with:
      - assistant_message
      - variants: [{label, tone, improved_text, image_url, image_prompt}]
    """
    try:
        content = (request.POST.get("content") or "").strip()
        goal = (request.POST.get("goal") or "").strip()

        uploaded_file = request.FILES.get("file")
        file_text = ""
        file_note = ""

        if uploaded_file:
            file_text, file_note = extract_text_from_upload(uploaded_file)

        parts = []
        if content:
            parts.append(content)
        if file_text:
            # If it's an image analysis context, it already includes a label
            parts.append(file_text)

        combined = "\n\n".join(parts).strip()

        if not combined:
            return JsonResponse({"error": "Add text or upload a file to improve."}, status=400)

        result = improve_content_with_variants(
            user_content=combined,
            user_goal=goal,
            file_note=file_note
        )

        return JsonResponse(result)

    except Exception:
        traceback.print_exc()
        return JsonResponse(
            {"error": "Something went wrong while improving your content. Try again."},
            status=500
        )


@require_POST
def improve_generate_image(request):
    """
    Expects application/json:
      { "image_prompt": "..." }

    Returns:
      { "image_url": "/media/generated/<uuid>.png" }
    """
    try:
        # Parse JSON safely
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)

        image_prompt = (payload.get("image_prompt") or "").strip()
        if not image_prompt:
            return JsonResponse({"error": "Missing image_prompt."}, status=400)

        # Generate via your cost-safe image_gen.py (gpt-image-1-mini, medium, 512x512)
        out = generate_image_to_media(image_prompt, size="auto")
        image_url = out.get("url") or ""
        if not image_url:
            return JsonResponse({"error": "No image URL returned."}, status=500)

        return JsonResponse({"image_url": image_url})

    except Exception:
        # Print the *real* error to your runserver console
        traceback.print_exc()
        return JsonResponse({"error": "Image generation failed."}, status=500)
