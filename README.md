# Snap2Campaign

**Phone-first AI marketing assistant that turns a product into a complete campaign.**

---

## Overview

Snap2Campaign is designed for small sellers and independent creators who have a product but need campaign-ready content fast — without juggling multiple tools or requiring a marketing background.

Provide a product photo, a short description, an advertising goal, a target audience, and a brand tone. Snap2Campaign takes care of the rest, generating a complete set of campaign assets: a hero visual, a punchy tagline, social media copy for Instagram, LinkedIn, and X, and a short promotional video.

---

## Problem

Small sellers and creators often have great products but face a real barrier when it comes to marketing:

- Creating a campaign means coordinating graphic design, copywriting, and video tools separately
- Each platform (Instagram, LinkedIn, X) needs different copy with different character limits and tone
- Producing even a basic promotional video requires time and software skills most sellers don't have
- The whole process can take hours — and still not feel professional

---

## Solution

Snap2Campaign reduces the entire workflow to four steps:

```
Upload → Describe → Create → Get Campaign
```

Fill in your product details, press **Create Campaign**, and receive a complete set of publishable assets in one shot.

---

## Current Prototype

The current Streamlit-based prototype supports the full campaign-generation flow in a browser:

| Input | What you provide |
|---|---|
| Product Photo | Optional upload — used as the campaign hero visual if AI image generation is unavailable |
| Product Description | Name and short description of what you are advertising |
| Advertising Goal | Product Launch, Flash Sale, Festival Promotion, and more |
| Target Audience | Preset segments (Gamers, Young Professionals, Families…) or custom free-text |
| Brand Tone | Premium, Playful, Eco, Professional, Luxury, Minimal, or Friendly |

| Output | What you get |
|---|---|
| Hero Visual | AI-generated advertisement image styled to your tone and goal |
| Campaign Tagline | ≤ 10-word punchy line matched to your brand voice |
| Instagram Copy | Platform-specific post with hashtags |
| LinkedIn Copy | Professional post, no hashtags |
| X / Twitter Copy | ≤ 280-character post |
| Promotional Video | Short cinematic clip animated from the hero visual |
| Downloadable Assets | Hero image and promo video available for direct download |

**Graceful fallbacks** are built in: if AI image generation is unavailable, your uploaded product photo is used as the hero visual. If cloud video generation is unavailable, a local Ken Burns–style MP4 is rendered directly from the hero image — no external service required.

> **Note:** The current prototype runs in a browser. It does not perform on-device AI inference, Snapdragon NPU processing, native Android execution, voice input, or iQOO Office Kit integration. Those are planned hackathon capabilities described below.

---

## Hackathon Vision

The prototype is the foundation for the planned iQOO hackathon build. The final version is intended to be a fully **phone-first marketing workspace**:

- **iQOO camera as primary input** — point the camera at a product and the app begins building a campaign immediately, no file upload needed
- **Voice interaction** — describe the product, goal, and audience by speaking rather than typing
- **Local / open-source AI** — text and image generation running on-device for speed and privacy
- **Snapdragon NPU inference** — accelerated model execution where hardware capability allows
- **iQOO Office Kit integration** — seamless phone-to-laptop handoff for editing, downloading, and publishing campaign assets
- **Complete on-device pipeline** — from product capture to finished campaign without a cloud dependency

> These capabilities are **planned goals** for the hackathon build — not features of the current prototype.

---

## Tech Stack

| Component | Technology |
|---|---|
| UI framework | [Streamlit](https://streamlit.io) 1.58 |
| Text generation | [OpenRouter](https://openrouter.ai) via OpenAI-compatible client (`openai` 2.44) |
| Image generation | OpenRouter / Google Gemini Flash Image |
| Cloud video | [Runway](https://runwayml.com) Gen-3 Turbo (optional) |
| Local video | [MoviePy](https://github.com/Zulko/moviepy) 2.2 + `imageio-ffmpeg` (bundled FFmpeg, no system install needed) |
| Image processing | [Pillow](https://python-pillow.org) 11.3 |
| HTTP client | [HTTPX](https://www.python-httpx.org) 0.28 |
| Environment config | `python-dotenv` |

---

## How It Works

```
User Input
  └─ Product photo (optional) + description + goal + audience + tone
        │
        ├─ Stage 1 ── Hero Visual
        │              AI image generation (OpenRouter/Gemini Flash Image)
        │              └─ Fallback: uploaded product photo (PIL-treated to 16:9 canvas)
        │
        ├─ Stage 2 ── Tagline
        │              Few-shot prompted GPT-4o / free model via OpenRouter
        │
        ├─ Stage 3 ── Social Copy
        │              Three parallel text calls (Instagram / LinkedIn / X)
        │              Blog intro generated internally as context, not displayed
        │
        └─ Stage 4 ── Promotional Video
                       Runway Gen-3 Turbo (animates hero image)
                       └─ Fallback: local Ken Burns zoom-pan MP4 via MoviePy
```

All generated assets are saved to an `artifacts/` directory and available for download directly from the campaign results page.

---

## Running Locally

**Prerequisites:** Python 3.11 or higher.

```bash
git clone <repository-url>
cd Snap2Campaign
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

**Configure API keys** — create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=sk-or-v1-...          # required for text and image generation
OPENROUTER_IMAGE_API_KEY=sk-or-v1-...   # optional; falls back to OPENROUTER_API_KEY
RUNWAY_API_KEY=your_runway_key_here      # optional; local video fallback used if absent
```

**Run:**

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

> **Free tier:** OpenRouter's free tier allows up to 50 free-model requests per day. One campaign uses approximately 5 text requests. The default text model is `poolside/laguna-s-2.1:free`. To use a paid model, set `TEXT_MODEL=openai/gpt-4o` in your `.env`.

---

## Project Structure

```
Snap2Campaign/
├── app.py              # Streamlit UI and campaign pipeline
├── config.py           # Environment variables and shared constants
├── text_gen.py         # Tagline, blog, and social copy generation
├── image_gen.py        # Hero image generation
├── video_gen.py        # Runway cloud video generation
├── local_video.py      # Ken Burns local video fallback
├── requirements.txt    # Python dependencies
├── .env                # API keys (not committed)
└── artifacts/          # Generated campaign assets (created at runtime)
```

---

## License

This project is currently a hackathon prototype. Licensing details will be added as the project evolves.
