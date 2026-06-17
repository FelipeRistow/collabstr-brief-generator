"""Estimate the USD cost of an OpenAI call from its token usage.

Prices are per 1,000,000 tokens and are approximate (they change over time),
so the estimate is for cost *visibility*, not billing accuracy.
"""

# USD per 1M tokens. Source: OpenAI pricing for gpt-4o-mini (approximate).
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def estimate_cost(model, prompt_tokens, completion_tokens):
    """Return the estimated cost in USD, rounded to 6 decimal places.

    Unknown models fall back to $0.00 so a model swap never crashes the app.
    """
    price = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    cost = (
        prompt_tokens / 1_000_000 * price["input"]
        + completion_tokens / 1_000_000 * price["output"]
    )
    return round(cost, 6)
