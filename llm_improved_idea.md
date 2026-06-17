Build it as a **small polished vertical slice**, not a “cool AI app.” The evaluator wants to see: clean Django organization, structured LLM output, guardrails, telemetry, and Collabstr-style UI.

## Best project concept

**AI Campaign Brief Generator**

A single-page Django app where a brand enters:

* Brand name
* Platform
* Goal
* Tone

Then the backend returns:

* 4–6 sentence campaign brief
* 3 content angles
* 3 creator selection criteria
* latency
* token usage
* estimated cost

Keep the scope exactly there. Do **not** add login, history, database models, streaming, image generation, user accounts, or dashboards.

Collabstr’s design system emphasizes semantic tokens, cards, inputs, buttons, loaders, spacing on a modified 8px grid, rounded borders, and subtle shadows, so the UI should look clean, white, card-based, minimal, and marketplace/SaaS-like. ([Collabstr][1])

---

# 1-hour execution plan

## Minute 0–5: Create project

Project name:

```bash
collabstr-ai-brief-generator
```

Suggested stack:

```txt
Django
openai
python-dotenv
django-ratelimit
```

Use SQLite/default Django only. No custom DB models needed.

File structure:

```txt
collabstr-ai-brief-generator/
  briefgen/
    settings.py
    urls.py
  generator/
    views.py
    urls.py
    services/
      __init__.py
      llm.py
      safety.py
      pricing.py
    templates/
      generator/
        index.html
    static/
      generator/
        styles.css
        app.js
  manage.py
  requirements.txt
  README.md
  .env.example
```

The clean organization is important because the challenge explicitly asks for `views.py` and `services/llm.py`.

---

# Backend plan

## Endpoint

Use:

```txt
GET  /              -> renders page
POST /api/generate/ -> returns JSON
```

Request body:

```json
{
  "brand_name": "Nike",
  "platform": "Instagram",
  "goal": "Awareness",
  "tone": "Friendly"
}
```

Response:

```json
{
  "brief": "4-6 sentence paragraph...",
  "angles": [
    "Behind-the-scenes product moment",
    "Creator-led problem/solution demo",
    "Lifestyle integration with clear CTA"
  ],
  "criteria": [
    "Creators with strong audience alignment",
    "Proven short-form engagement",
    "Clean, brand-safe content style"
  ],
  "metrics": {
    "latency_ms": 1240,
    "prompt_tokens": 180,
    "completion_tokens": 140,
    "total_tokens": 320,
    "estimated_cost_usd": 0.0002,
    "model": "..."
  }
}
```

## Validation

Do server-side validation before calling the LLM.

Rules:

```python
ALLOWED_PLATFORMS = {"Instagram", "TikTok", "UGC"}
ALLOWED_GOALS = {"Awareness", "Conversions", "Content Assets"}
ALLOWED_TONES = {"Professional", "Friendly", "Playful"}
```

Brand name:

```txt
Required
2–60 characters
Letters, numbers, spaces, apostrophe, ampersand, hyphen, period
No URLs
No email addresses
No obvious profanity
```

This lets you say in the README:

> I used allowlist validation for controlled fields and constrained brand names to a safe character set to reduce prompt-injection and abuse risk.

## Rate limiting

Use a simple IP-based limit:

```python
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
```

That is enough. Don’t build Redis rate limiting for this challenge.

## LLM service

In `services/llm.py`, create one function:

```python
generate_campaign_brief(brand_name, platform, goal, tone)
```

It should:

1. Build the system prompt.
2. Build the compact user prompt.
3. Start timer.
4. Call OpenAI.
5. Parse structured output.
6. Compute latency.
7. Extract token usage.
8. Estimate cost.
9. Return normalized dict.

Use structured output / JSON schema. OpenAI’s current docs describe Structured Outputs as a way to make model responses adhere to a JSON Schema and distinguish it from plain JSON mode because schema adherence is the point. ([OpenAI Platform][2])

---

# Prompt plan

## System prompt

Use this:

```txt
You are an AI assistant for Collabstr-style creator marketing workflows.
Generate concise, practical campaign briefs for brands hiring creators.
Follow the requested tone, avoid unsupported claims, avoid offensive content, and never mention being an AI.
Return only valid structured data matching the schema.
```

Why this works:

* Short
* Deterministic
* Product-specific
* Guardrails included
* No bloated prompt engineering

## User prompt

Use this:

```txt
Create a campaign brief for:
Brand: {brand_name}
Target platform: {platform}
Goal: {goal}
Tone: {tone}

Requirements:
- brief: 4–6 sentences
- angles: exactly 3 short content angle ideas
- criteria: exactly 3 creator selection criteria
- Keep it specific to the platform and goal.
```

Do not include massive examples. The challenge says concise.

## Schema

Conceptually:

```json
{
  "type": "object",
  "properties": {
    "brief": {
      "type": "string"
    },
    "angles": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 3,
      "maxItems": 3
    },
    "criteria": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 3,
      "maxItems": 3
    }
  },
  "required": ["brief", "angles", "criteria"],
  "additionalProperties": false
}
```

In README, explicitly say:

> I used schema-constrained output instead of asking the model to “please return JSON,” because the app needs reliable rendering of `brief`, `angles`, and `criteria`.

---

# Model settings

Use environment variables:

```txt
OPENAI_API_KEY=
OPENAI_MODEL=
```

For the actual submission, use a fast low-cost model available in your account. Do not hardcode the key. The docs note that Structured Outputs can be supplied through JSON schema response format, and newer OpenAI models support it. ([OpenAI Platform][2])

Use:

```python
temperature=0.3
max_tokens=500
```

Why:

* Temperature under 0.5 satisfies requirement.
* 500 max tokens is enough for 4–6 sentences + 6 bullets.
* Lower temperature makes demos consistent.

---

# Telemetry plan

Measure latency manually:

```python
start = time.perf_counter()
# LLM call
latency_ms = round((time.perf_counter() - start) * 1000)
```

Token usage:

```python
usage.prompt_tokens
usage.completion_tokens
usage.total_tokens
```

Estimated cost:

Create `services/pricing.py`.

Keep it simple:

```python
MODEL_PRICING = {
    "gpt-4o-mini": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
    }
}
```

Then:

```python
cost = (
    prompt_tokens / 1_000_000 * input_price
    + completion_tokens / 1_000_000 * output_price
)
```

In README:

> Token usage comes from the OpenAI response usage object. Latency is measured around the model call with `time.perf_counter()`. Cost is estimated from a small pricing map by model.

Even if exact pricing changes, this shows the right engineering thinking.

---

# Frontend plan

## Layout

One page:

```txt
Top nav / mini brand
Hero title
Subtitle
Two-column layout on desktop:
  left: form card
  right: output card
Mobile: stacked cards
```

Visual style:

* White background
* Soft gray page background
* Pink accent
* Rounded cards
* Subtle shadow
* Clean labels
* Large primary button
* Error alert
* Small telemetry footer

Use Collabstr-adjacent naming:

```txt
AI Campaign Brief Generator
Create a creator-ready brief in seconds.
```

## Form

Fields:

```html
<input id="brand_name">
<select id="platform">
<select id="goal">
<select id="tone">
<button>
```

Options:

```txt
Instagram / TikTok / UGC
Awareness / Conversions / Content Assets
Professional / Friendly / Playful
```

## jQuery behavior

On submit:

1. Prevent default.
2. Clear previous errors.
3. Disable button.
4. Change button text to `Generating...`.
5. Show skeleton/loading state.
6. POST JSON to `/api/generate/`.
7. Render result.
8. Show telemetry.
9. Re-enable button.

Render:

```txt
Brief
[p]

Content Angles
1. ...
2. ...
3. ...

Creator Selection Criteria
• ...
• ...
• ...

Telemetry
Latency: 1,240ms · Tokens: 320 · Est. cost: $0.0002
```

Add one small “Copy brief” button only if you have time. Nice but optional.

---

# README plan

Your README should be short but look intentional.

Sections:

```md
# Collabstr AI Brief Generator

A small Django + jQuery AI feature that generates creator campaign briefs from brand/platform/goal/tone inputs.

## Live Demo
URL here

## Loom Demo
URL here

## Tech Stack
- Django
- Python
- OpenAI structured outputs
- HTML/CSS/JavaScript/jQuery
- SQLite

## Prompt Design
Explain short system prompt + compact user prompt.

## Guardrails
- Server-side allowlist validation for platform/goal/tone
- Brand name length and character validation
- Basic profanity filter
- Rate limiting
- Temperature <= 0.5
- Max token cap
- Schema-constrained output

## Telemetry
- Latency measured around LLM call
- Token usage returned from model response
- Estimated cost calculated from token counts and model pricing map

## Running Locally
Commands

## Environment Variables
OPENAI_API_KEY=
OPENAI_MODEL=
```

Do not write a novel. They will skim it.

---

# Deployment plan

Fastest options:

## Best for Django

Use **Render**.

Why:

* Easy Django deployment
* Public URL
* Add environment variables
* Free-ish/simple
* GitHub integration

Deployment checklist:

```txt
Add gunicorn
Add whitenoise
Set ALLOWED_HOSTS
Set CSRF_TRUSTED_ORIGINS
Set DEBUG=False in production
Add OPENAI_API_KEY env var
```

Requirements:

```txt
Django
openai
python-dotenv
django-ratelimit
gunicorn
whitenoise
```

Procfile or Render start command:

```bash
gunicorn briefgen.wsgi:application
```

Static files:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    ...
]
```

Then:

```bash
python manage.py collectstatic --noinput
```

For 1 hour, Render is probably safer than trying to fight Railway/Fly.io if you haven’t used them recently.

---

# What to prioritize

## Must-have

These are non-negotiable:

```txt
Working public page
Working API call
Server-side validation
Structured JSON output
Loading and error state
Latency + token metrics
README notes
Loom under 1 minute
```

## Nice-to-have

Only add after core works:

```txt
Copy button
Example brand chips
Skeleton loader
Better mobile polish
Cost estimate
```

## Do not build

Avoid:

```txt
User auth
Database persistence
Campaign history
Streaming
RAG
Image generation
Docker
Complex tests
Multiple pages
Admin panel
```

This is a shipping challenge, not an architecture contest.

---

# Suggested 1-hour timeline

## 0–10 min: Django skeleton

Create app, routes, template, static files.

## 10–25 min: Backend endpoint

Validation, safety, rate limit, LLM service stub.

At this point, make it return mock data first so frontend can be built.

## 25–40 min: Real OpenAI call

Add JSON schema, telemetry, token usage, cost estimate.

## 40–50 min: UI polish

Collabstr-like card layout, button loading, error alert, clean result rendering.

## 50–60 min: README + deploy prep

Push to GitHub, deploy, record Loom.

Realistically, the live deploy may push you past 1 hour. That’s okay. The important part is to timebox the app itself.

---

# Demo script for Loom

Keep it under 45 seconds:

> “Hi, this is my Collabstr AI Brief Generator. It’s a small Django app with a jQuery frontend. The form takes brand name, target platform, campaign goal, and tone. On submit, it validates inputs server-side, rate-limits requests, calls the LLM with a concise deterministic prompt, and uses schema-constrained output so the UI can reliably render the brief, three content angles, and three creator criteria. At the bottom, I return latency, token usage, and estimated cost for basic observability. The code is organized with the Django view handling HTTP validation and `services/llm.py` handling the model orchestration.”

---

# Final email to Clayton

You’ll send something like this after deploying:

```txt
Subject: Collabstr Full-Stack Developer Project Submission

Hi Clayton,

Thanks again for the technical challenge.

Here are the project links:

GitHub repo: [repo URL]
Live demo: [live URL]
Loom demo: [loom URL]

I kept the scope intentionally tight: a Django + jQuery AI Brief Generator with server-side validation, rate limiting, schema-constrained LLM output, and basic telemetry for latency, token usage, and estimated cost.

Best,
Felipe
```

My recommendation: build the backend first with mock output, then wire the frontend, then swap in the real LLM call. That avoids the classic trap of losing 40 minutes debugging OpenAI/deployment before you even have a working page.

[1]: https://collabstr.com/design-system "Design System | Collabstr"
[2]: https://platform.openai.com/docs/guides/structured-outputs "Structured model outputs | OpenAI API"

