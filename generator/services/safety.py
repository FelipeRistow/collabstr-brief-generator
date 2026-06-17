"""Server-side validation and input guardrails.

Validation runs before any LLM call. The select fields use a strict allowlist
(the strongest guardrail), and the brand name is constrained to a safe
character set, which also blocks the punctuation used in most prompt-injection
attempts (braces, colons, backticks, newlines, etc.).

Each validator returns a ``(is_valid, error_message)`` tuple so the view can
return a clean, user-facing message without exceptions.
"""

import re

# Allowed values for the dropdowns. These lists are the single source of truth:
# the template renders them as options and the validators reject anything else.
PLATFORMS = ["Instagram", "TikTok", "UGC"]
GOALS = ["Awareness", "Conversions", "Content Assets"]
TONES = ["Professional", "Friendly", "Playful"]

# Brand name: letters, numbers, spaces, and a few common punctuation marks.
# Allowing only these characters is itself the prompt-injection guard.
BRAND_RE = re.compile(r"^[A-Za-z0-9 &\-.'’]{2,60}$")

# Reject anything that looks like a URL or an email address (defense in depth,
# since "." and "-" are allowed in the charset above).
URL_RE = re.compile(r"(https?://|www\.|\.[a-z]{2,}(/|$))", re.IGNORECASE)
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

# A small, illustrative profanity list. A production app would use a maintained
# library; this satisfies the "basic profanity filter" requirement.
PROFANITY = {
    "shit", "fuck", "bitch", "asshole", "bastard", "dick", "cunt", "piss",
}

# Optional free-text campaign description: bounded length, profanity-checked.
DESCRIPTION_MAX = 300


def _validate_brand_name(brand_name):
    if not brand_name:
        return False, "Brand name is required."
    if len(brand_name) < 2 or len(brand_name) > 60:
        return False, "Brand name must be between 2 and 60 characters."
    if not BRAND_RE.match(brand_name):
        return False, "Brand name contains invalid characters."
    if URL_RE.search(brand_name) or EMAIL_RE.search(brand_name):
        return False, "Brand name cannot contain a URL or email address."
    lowered = brand_name.lower()
    if any(word in lowered.split() for word in PROFANITY):
        return False, "Brand name contains inappropriate language."
    return True, None


def _validate_choice(value, allowed, field_label):
    if value not in allowed:
        return False, f"{field_label} must be one of: {', '.join(allowed)}."
    return True, None


def _validate_description(description):
    # Optional: an empty description is always valid.
    if not description:
        return True, None
    if len(description) > DESCRIPTION_MAX:
        return False, f"Campaign description must be {DESCRIPTION_MAX} characters or fewer."
    if any(word in description.lower().split() for word in PROFANITY):
        return False, "Campaign description contains inappropriate language."
    return True, None


def validate_all_inputs(brand_name, platform, goal, tone, description=""):
    """Validate all inputs. Returns ``(is_valid, error_message)``.

    ``description`` is optional free text; the rest are required.
    """
    for is_valid, error in (
        _validate_brand_name(brand_name),
        _validate_choice(platform, PLATFORMS, "Platform"),
        _validate_choice(goal, GOALS, "Goal"),
        _validate_choice(tone, TONES, "Tone"),
        _validate_description(description),
    ):
        if not is_valid:
            return False, error
    return True, None
