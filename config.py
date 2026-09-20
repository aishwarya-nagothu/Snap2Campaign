"""Configuration – loads environment variables and shared constants.

Resolution order for secrets and configurable values:
  1. Environment variable (os.getenv) — covers local .env via python-dotenv,
     system environment, and any CI/CD injection.
  2. Streamlit Secrets (st.secrets) — used on Streamlit Cloud where secrets are
     stored in the app dashboard rather than as environment variables.
  3. Hard-coded default — only for non-sensitive defaults such as model names.

This means the app works without modification in both local development (with a
.env file) and on Streamlit Cloud (with secrets configured in the dashboard).
"""
import os
from dotenv import load_dotenv

# Load .env into the process environment when running locally.
# On Streamlit Cloud there is no .env file; this call is a no-op there.
load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Return the value for *key* using the two-step resolution order.

    1. os.getenv() — environment variable / .env file (via load_dotenv above).
    2. st.secrets.get() — Streamlit Cloud secrets dashboard.
    3. *default* — hard-coded fallback (empty string unless overridden).

    st.secrets is only imported when needed so this module remains importable
    outside a Streamlit context (unit tests, CLI scripts, etc.) without error.
    """
    value = os.getenv(key, "")
    if value:
        return value

    # Fall back to Streamlit Secrets when the env var is absent or empty.
    try:
        import streamlit as st  # noqa: PLC0415 – intentional lazy import
        value = st.secrets.get(key, default)
    except Exception:
        # st.secrets is unavailable (not a Streamlit runtime, or secrets not
        # configured).  Silently fall through to the default.
        value = default

    return value or default


OPENROUTER_API_KEY: str = _get_secret("OPENROUTER_API_KEY")

# OPENROUTER_IMAGE_API_KEY is optional; when absent it falls back to the main
# key so callers that only set one key still work.  image_gen.py treats an empty
# value as "image generation unavailable" and lets app.py use the photo fallback.
OPENROUTER_IMAGE_API_KEY: str = _get_secret(
    "OPENROUTER_IMAGE_API_KEY", default=OPENROUTER_API_KEY
)

RUNWAY_API_KEY: str = _get_secret("RUNWAY_API_KEY")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Text model used for tagline, blog, and social post generation.
# Override via TEXT_MODEL env var (local) or Streamlit Secret (cloud) to switch
# between paid and free tiers without editing this file.
TEXT_MODEL: str = _get_secret("TEXT_MODEL", default="poolside/laguna-s-2.1:free")

IMAGE_MODEL = "google/gemini-3.1-flash-image"
VIDEO_DURATION = 8         # seconds

# ── Campaign input options ────────────────────────────────────────────────────

# Advertising purposes shown in the "Advertising Goal" dropdown.
AD_GOALS: list[str] = [
    "Product Launch",
    "Festival Promotion",
    "Flash Sale",
    "Special Offer",
    "Brand Awareness",
    "New Store Opening",
    "Seasonal Promotion",
]

# Preset audience segments shown in the "Target Audience" dropdown.
# The UI also allows a free-text custom entry.
AUDIENCE_OPTIONS: list[str] = [
    "College Students",
    "Young Professionals",
    "Families",
    "Gamers",
    "Budget-Conscious Buyers",
    "Premium Customers",
    "Custom…",       # sentinel – UI switches to a text input when selected
]

TONE_STYLES: dict[str, dict] = {
    "premium":      {"style": "photorealistic",      "lighting": "dramatic studio lighting",   "palette": "rich deep tones, gold accents"},
    "eco":          {"style": "watercolour illustration", "lighting": "soft natural daylight",  "palette": "earthy greens, warm neutrals"},
    "playful":      {"style": "bright digital illustration", "lighting": "vibrant even lighting", "palette": "vivid multicolour"},
    "professional": {"style": "commercial photography",  "lighting": "editorial lighting",      "palette": "clean neutrals, confident blues"},
    "luxury":       {"style": "high-fashion photography", "lighting": "cinematic low-key",      "palette": "black, white, champagne gold"},
    "minimal":      {"style": "clean modern product shot", "lighting": "soft diffused shadows", "palette": "white, light grey, single accent"},
    "friendly":     {"style": "warm lifestyle photography", "lighting": "golden-hour natural",  "palette": "warm pastels, approachable tones"},
}
