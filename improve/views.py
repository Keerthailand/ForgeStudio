import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
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
      - goal (optional): what the user wants (e.g., "make it more professional")
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

        combined = "\n\n".join([x for x in [content, file_text] if x]).strip()

        if not combined:
            return JsonResponse({"error": "Add text or upload a file to improve."}, status=400)

        result = improve_content_with_variants(
            user_content=combined,
            user_goal=goal,
            file_note=file_note
        )

        return JsonResponse(result)

    except Exception:
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
      { "image_url": "/media/generated/xyz.png" }
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        image_prompt = (payload.get("image_prompt") or "").strip()

        if not image_prompt:
            return JsonResponse({"error": "Missing image_prompt"}, status=400)

        out = generate_image_to_media(image_prompt, size="512x512")
        return JsonResponse({"image_url": out["url"]})
    except Exception:
        return JsonResponse({"error": "Image generation failed."}, status=500)
