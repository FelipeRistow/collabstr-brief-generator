"""HTTP layer: render the page and handle the generate-brief API call.

The view's job is narrow and readable: rate-limit, parse, validate, call the
service, and map outcomes to the right status codes. All the model logic lives
in ``services/llm.py``.
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .services import llm, safety
from .services.rate_limiter import rate_limiter


def _client_ip(request):
    """Best-effort client IP, honoring a proxy's X-Forwarded-For header."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@require_GET
def index(request):
    """Render the single-page form."""
    return render(request, "generator/index.html", {
        "platforms": safety.PLATFORMS,
        "goals": safety.GOALS,
        "tones": safety.TONES,
    })


@require_POST
def generate(request):
    """Validate inputs, generate a brief, and return JSON."""
    if not rate_limiter.is_allowed(_client_ip(request)):
        return JsonResponse(
            {"success": False, "error": "Rate limit exceeded. Please wait a minute and try again."},
            status=429,
        )

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"success": False, "error": "Invalid request format."}, status=400)

    brand_name = str(payload.get("brand_name", "")).strip()
    platform = str(payload.get("platform", "")).strip()
    goal = str(payload.get("goal", "")).strip()
    tone = str(payload.get("tone", "")).strip()
    description = str(payload.get("description", "")).strip()

    is_valid, error = safety.validate_all_inputs(brand_name, platform, goal, tone, description)
    if not is_valid:
        return JsonResponse({"success": False, "error": error}, status=400)

    try:
        result = llm.generate_campaign_brief(brand_name, platform, goal, tone, description)
    except llm.LLMError:
        return JsonResponse(
            {"success": False, "error": "The AI service is unavailable right now. Please try again."},
            status=502,
        )
    except Exception:
        return JsonResponse({"success": False, "error": "Unexpected server error."}, status=500)

    return JsonResponse({"success": True, **result})
