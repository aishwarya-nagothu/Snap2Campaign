"""Text generation – tagline, blog introduction, social posts via OpenRouter."""
import atexit
import httpx
import json
import re
import time
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, TEXT_MODEL, TONE_STYLES

# The httpx client is shared across all text requests and is created
# unconditionally because it has no dependency on API keys.
_httpx_client = httpx.Client()
atexit.register(_httpx_client.close)

# The OpenAI text client is initialised lazily on first use.  Deferring
# initialisation prevents a crash (openai>=2.34 raises OpenAIError when
# api_key="") when OPENROUTER_API_KEY is not yet available at import time —
# for example on Streamlit Cloud before secrets are resolved.  The existing
# try/except blocks in app.py handle any failure surfaced at call time.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Return the shared OpenAI text client, creating it on first use.

    Raises RuntimeError when OPENROUTER_API_KEY is absent so callers receive
    a clear error rather than a cryptic OpenAI authentication failure.
    """
    global _client
    if _client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set; text generation is unavailable."
            )
        _client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            http_client=_httpx_client,
        )
    return _client

# ── Few-shot examples per tone ──────────────────────────────────────────────
_TAGLINE_EXAMPLES: dict[str, list[tuple[str, str]]] = {
    "premium":      [("LuxeWatch Pro", "Time refined to perfection."),
                     ("AuraSerum", "Skin that speaks before you do.")],
    "eco":          [("GreenPack", "Good for you. Kind to the earth."),
                     ("BioBottle", "Nature packaged, naturally.")],
    "playful":      [("BubblyBites", "Snack loud, smile louder!"),
                     ("ZippyShoes", "Run like nobody's watching.")],
    "professional": [("CoreAnalytics", "Data you can act on. Results you can trust."),
                     ("FlowDesk", "Work smarter. Lead better.")],
    "luxury":       [("Velour", "Crafted for those who know the difference."),
                     ("NoirEau", "Rare. Refined. Unforgettable.")],
    "minimal":      [("FormDesk", "Less desk. More done."),
                     ("PureAir", "Clean air, simply delivered.")],
    "friendly":     [("SipJoy", "Every sip, a little happier."),
                     ("WarmNest", "Home feels better with us.")],
}


def _chat(messages: list[dict], max_tokens: int = 240, retries: int = 3) -> str:
    """Call the OpenRouter chat endpoint with retry logic and dynamic token fallback.

    If the provider returns a 402 indicating a smaller affordable token budget,
    parse that value and retry with a reduced `max_tokens` automatically.
    """
    for attempt in range(retries):
        try:
            resp = _get_client().chat.completions.create(
                model=TEXT_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.8,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e)
            # Parse messages like "can only afford 257" from provider error text
            m = re.search(r"can only afford\s+(\d+)", msg, flags=re.IGNORECASE)
            if m:
                afford = int(m.group(1))
                # If provider indicates a very small affordable token budget,
                # lower max_tokens to something the provider can afford (small floor).
                # Use afford-2 as target but keep a small minimum to allow the model
                # to return a meaningful short reply.
                new_max = max(8, afford - 2)
                if new_max < max_tokens:
                    max_tokens = new_max
                    # quick backoff then retry with reduced budget
                    time.sleep(1)
                    continue

            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return ""


# Cached afford probing to avoid repeated probes
_last_probe = {"ts": 0.0, "afford": None}


def probe_affordance(max_probe: int = 256, ttl: int = 30) -> int | None:
    """Probe the provider with small `max_tokens` values to detect an affordable budget.

    Uses an exponential backoff probe (1,2,4,8...) up to `max_probe`. Returns the
    provider-reported afford value when a 402 is encountered, or the highest
    successful probe value if no 402 is seen. Caches result for `ttl` seconds.
    Returns None when probing fails entirely.
    """
    now = time.time()
    if _last_probe["afford"] is not None and now - _last_probe["ts"] < ttl:
        return _last_probe["afford"]

    tokens = 1
    last_success = 0
    probe_messages = [
        {"role": "system", "content": "Probe: return a very short acknowledgement word like 'ok'."},
        {"role": "user", "content": "Please reply with 'ok'."},
    ]

    while tokens <= max_probe:
        try:
            resp = _get_client().chat.completions.create(
                model=TEXT_MODEL,
                messages=probe_messages,
                max_tokens=tokens,
                temperature=0.0,
            )
            # success means provider can afford `tokens`
            last_success = tokens
            # increase exponentially but stay within max_probe
            tokens = min(max_probe, tokens * 2)
            if tokens == last_success:
                break
            # small pause to avoid rate issues
            time.sleep(0.2)
            continue
        except Exception as e:
            msg = str(e)
            m = re.search(r"can only afford\s+(\d+)", msg, flags=re.IGNORECASE)
            if m:
                afford = int(m.group(1))
                _last_probe["afford"] = afford
                _last_probe["ts"] = now
                return afford
            # unexpected failure; abort probing
            break

    # No explicit 402 encountered; if we had at least one successful small probe,
    # cache and return that as a conservative afford estimate.
    if last_success > 0:
        _last_probe["afford"] = last_success
        _last_probe["ts"] = now
        return last_success

    return None


def generate_tagline(product: str, audience: str, tone: str, ad_goal: str = "") -> str:
    """Few-shot prompting – return a single campaign tagline (≤10 words).

    ad_goal (e.g. "Flash Sale", "Product Launch") is woven into the prompt so the
    tagline reflects the advertising purpose, not just the product.
    """
    tone_key = tone.lower()
    examples = _TAGLINE_EXAMPLES.get(tone_key, _TAGLINE_EXAMPLES["professional"])

    few_shot = "\n".join(
        f'Product: {p}\nTagline: "{t}"' for p, t in examples
    )

    goal_line = f"Advertising Goal: {ad_goal}\n" if ad_goal else ""

    messages = [
        {"role": "system", "content": (
            "You are a Creative Director. Generate a memorable campaign tagline. "
            "Rules: max 10 words, no hashtags, no quotes, strong brand voice."
        )},
        {"role": "user", "content": (
            f"Tone examples:\n{few_shot}\n\n"
            f"Now create a tagline for:\n"
            f"Product: {product}\nAudience: {audience}\n{goal_line}Tone: {tone}\n\n"
            "Return ONLY the tagline."
        )},
    ]
    # probe_affordance() is designed for paid models that return 402 "can only
    # afford N tokens" errors.  Free models (:free suffix) never return that error
    # — they either succeed or return 429 (handled by the _chat retry loop).
    # Skipping the probe on free models saves scarce daily-quota requests.
    if TEXT_MODEL.endswith(":free"):
        chosen = 32   # safe fixed budget — taglines are always short
    else:
        # Probe provider affordance (cheap operation) and choose a safe token budget.
        afford = probe_affordance()
        if afford is None:
            chosen = 16
        else:
            chosen = max(8, min(32, afford - 2))

    return _chat(messages, max_tokens=chosen)


def generate_blog(product: str, audience: str, tone: str, tagline: str, ad_goal: str = "") -> str:
    """Role prompting – return a 100–120 word blog introduction.

    ad_goal is included so the copy reflects the campaign purpose.
    """
    goal_line = f"Advertising Goal: {ad_goal}\n" if ad_goal else ""
    messages = [
        {"role": "system", "content": (
            "You are an expert Content Strategist writing for a marketing blog. "
            "Write between 100 and 120 words. No headings, no bullet points – flowing prose only."
        )},
        {"role": "user", "content": (
            f"Write a compelling blog introduction for:\n"
            f"Product: {product}\nAudience: {audience}\n{goal_line}Tone: {tone}\n"
            f"Campaign tagline (weave it in naturally): \"{tagline}\"\n\n"
            "Length: 100-120 words."
        )},
    ]
    # Use a conservative token limit to fit smaller credit budgets
    return _chat(messages, max_tokens=140)


def _gen_social_platform(product: str, audience: str, tone: str, tagline: str, blog: str, platform: str, ad_goal: str = "", max_tokens: int = 140, retries: int = 2) -> str:
    """Generate a single platform post as plain text. Retries only this stage on failure."""
    limits = {
        "twitter": 280,
        "instagram": 2200,
        "linkedin": 700,
    }
    char_limit = limits.get(platform.lower(), 500)

    goal_line = f"Advertising Goal: {ad_goal}\n" if ad_goal else ""

    system_msg = (
        "You are a concise social media copywriter. Return ONLY the post text (no markdown, no JSON, no explanations). "
        "Keep it short and punchy. Observe platform-specific rules: no hashtags in LinkedIn."
    )

    user_msg = (
        f"Product: {product}\nAudience: {audience}\nTone: {tone}\nTagline: {tagline}\n"
        f"{goal_line}"
        f"Blog context (brief): {blog[:300]}\nPlatform: {platform}\n\n"
        "Return only the single post text, concise and within platform limits."
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    for attempt in range(retries):
        try:
            txt = _chat(messages, max_tokens=max_tokens)
            if not txt:
                raise RuntimeError("Empty response from model")
            # Trim and enforce char limit
            txt = txt.strip()
            if len(txt) > char_limit:
                txt = txt[:char_limit]
            # Remove stray markdown or JSON fences if present
            txt = txt.strip().removeprefix("```").removesuffix("```").strip()
            return txt
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1)


def generate_social_posts(product: str, audience: str, tone: str, blog: str, tagline: str, ad_goal: str = "") -> dict:
    """Generate social posts per platform and return dict.

    Splits work into three smaller calls (twitter/instagram/linkedin),
    retries only the failed platform, and assembles the final dict locally.
    """
    platforms = ["twitter", "instagram", "linkedin"]
    results: dict[str, str] = {}
    errors: dict[str, Exception] = {}

    # Allocate modest per-call token budgets — dynamic fallback will reduce if needed
    per_call_tokens = {"twitter": 120, "instagram": 140, "linkedin": 120}

    for p in platforms:
        try:
            results[p] = _gen_social_platform(
                product=product,
                audience=audience,
                tone=tone,
                tagline=tagline,
                blog=blog,
                platform=p,
                ad_goal=ad_goal,
                max_tokens=per_call_tokens.get(p, 120),
            )
        except Exception as e:
            errors[p] = e

    if errors:
        # Surface the first error with context
        first = next(iter(errors.items()))
        raise RuntimeError(f"Social posts failed for platform {first[0]}: {first[1]}")

    return results
