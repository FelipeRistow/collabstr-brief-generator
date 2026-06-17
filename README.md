# Collabstr AI Campaign Brief Generator

A small Django + jQuery app that turns a few inputs — **brand name, platform, goal, tone**, and an optional **campaign description** — into a creator-ready campaign brief with **3 content angles** and **3 creator selection criteria**, plus latency, token, and cost telemetry.

Built as a tight vertical slice: clean Django organization, schema-constrained LLM output, input guardrails, and a Collabstr-style UI.

## Live Demo
_TODO: add the public URL_

## Loom Demo
_TODO: add the Loom link (<1 min)_

## Tech Stack
- **Backend:** Django 6, Python 3.12+
- **AI:** OpenAI `gpt-4o-mini` with **Structured Outputs** (Pydantic schema)
- **Frontend:** HTML, CSS, JavaScript, jQuery (AJAX)
- **Database:** SQLite (Django default; nothing is persisted)

## Run Locally
```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # then add your OPENAI_API_KEY
python manage.py migrate            # sets up Django's default tables
python manage.py runserver
```
Open http://localhost:8000.

## Prompt Design
- **Short, deterministic system prompt** ([`generator/services/llm.py`](generator/services/llm.py)) fixes the persona (a Collabstr campaign strategist), the structure (4–6 sentence brief, exactly 3 angles, exactly 3 criteria), and the guardrails (stay on tone, no unsupported claims, never reveal it's an AI).
- **Compact user prompt** just carries the four inputs — no bloated examples.
- **Schema-constrained output:** we pass a Pydantic model as `response_format` and call `client.chat.completions.parse`, so the model must return exactly `{brief, angles, criteria}`. This is more reliable than asking the model to "please return JSON," which is the whole point for a UI that renders fixed fields.

## Guardrails
- **Allowlist validation** for platform / goal / tone (exact-match — the strongest guard).
- **Brand name** constrained to 2–60 chars and a safe character set; the charset itself blocks the punctuation used in most prompt-injection attempts. URLs, emails, and a basic profanity list are rejected.
- **Campaign description** (optional) is length-capped (300 chars), profanity-checked, and passed to the model clearly labelled as untrusted input.
- **Rate limiting:** 5 requests/min per IP (in-memory sliding window, `services/rate_limiter.py`).
- **Model settings:** `temperature=0.3` (≤ 0.5) and a `max_completion_tokens=500` cap.
- **CSRF stays enabled**; the AJAX call sends the `X-CSRFToken` header.
- All errors return JSON with the right status code (400 invalid input, 429 rate-limited, 502 AI error, 500 unexpected).

## Telemetry
Every successful response includes a `metrics` block:
- **Latency** — measured with `time.perf_counter()` around the LLM call.
- **Tokens** — `prompt_tokens` / `completion_tokens` / `total_tokens` from the OpenAI response `usage` object.
- **Estimated cost** — computed from token counts and a per-model price map in `services/pricing.py` (prices are approximate and for visibility, not billing).

## Environment Variables
| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | yes | — | Your OpenAI key. |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | Any model supporting Structured Outputs. |
| `DEBUG` | no | `True` | Set `False` in production. |
| `SECRET_KEY` | no | dev key | Set a real value in production. |
| `ALLOWED_HOSTS` | no | `localhost,127.0.0.1` | Comma-separated. |

## Project Structure
```
briefgen/            # Django project (settings, urls)
generator/
  views.py           # GET page + POST /api/generate/ (HTTP + status codes)
  services/
    llm.py           # OpenAI Structured Outputs + telemetry
    safety.py        # input validation / guardrails
    pricing.py       # token -> cost estimate
    rate_limiter.py  # in-memory per-IP limiter
  templates/generator/index.html
  static/generator/  # styles.css, app.js (jQuery AJAX)
```

## Notes / Production To-Dos
Intentionally out of scope for this exercise: auth, persistence/history, tests, and a shared-cache rate limiter (the in-memory one is per-process — use Redis behind multiple workers).
