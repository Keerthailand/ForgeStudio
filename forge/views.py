import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services.flows import evaluate_brainstorm, evaluate_plan


def forge_intro(request):
    return render(request, "forge/forge.html")


def forge_brainstorm(request):
    return render(request, "forge/brainstorm.html")


def forge_plan(request):
    return render(request, "forge/plan.html")


@require_POST
def forge_brainstorm_evaluate(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        answers = data.get("answers") or {}
        result = evaluate_brainstorm(answers)

        # store in session for convenience
        request.session["forge_brainstorm_last"] = result
        request.session.modified = True

        return JsonResponse(result)
    except Exception:
        return JsonResponse({"error": "Couldn’t evaluate brainstorm. Try again."}, status=500)


@require_POST
def forge_plan_evaluate(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        answers = data.get("answers") or {}
        result = evaluate_plan(answers)

        request.session["forge_plan_last"] = result
        request.session.modified = True

        return JsonResponse(result)
    except Exception:
        return JsonResponse({"error": "Couldn’t build your plan. Try again."}, status=500)
