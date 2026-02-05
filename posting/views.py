import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services.ai import generate_post_with_image

def posting_view(request):
    return render(request, "posting/posting.html")

@require_POST
def posting_generate(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return JsonResponse({"error": "Please enter a prompt."}, status=400)

        result = generate_post_with_image(prompt)

        return JsonResponse({
            "assistant_message": result.assistant_message,
            "platforms": {
                "instagram": result.instagram,
                "x": result.x,
                "facebook": result.facebook,
                "linkedin": result.linkedin,
            },
            "image": {
                "prompt": result.image_prompt,
                "url": result.image_url,
            },
            "variants": result.variants
        })

    except Exception as e:
        return JsonResponse({"error": "Something went wrong forging your post."}, status=500)
