"""Snap2Campaign – Phase 1 prototype.

Evolved from the AI Content Engine base to demonstrate the iQOO hackathon concept:
  "A small seller points their phone at a product and receives a complete
   marketing campaign ready to publish."

This prototype runs entirely in a browser via Streamlit.
The final hackathon version will be a native Android app with on-device AI,
Snapdragon NPU inference, camera input, and iQOO Office Kit integration.
"""
import json
from pathlib import Path

import httpx
import streamlit as st

from config import AD_GOALS, AUDIENCE_OPTIONS, TONE_STYLES, VIDEO_DURATION
from image_gen import generate_image
from local_video import create_ken_burns
from text_gen import generate_blog, generate_social_posts, generate_tagline
from video_gen import generate_video

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Snap2Campaign",
    page_icon="⚡",
    layout="wide",                   # use full browser width; CSS caps at 1080px
    initial_sidebar_state="collapsed",
)

# ── Design system (dark theme) ────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        color: #e2e8f0;
    }

    /* ── Page shell: centred column, max 1160px, compact vertical rhythm ── */
    .block-container {
        max-width: 1160px !important;
        padding: 1.6rem 2.5rem 3rem !important;
        margin: 0 auto;
    }

    /* ── Brand header ── */
    .s2c-header {
        text-align: center;
        padding: 1rem 0 1.2rem;
    }
    .s2c-wordmark {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #f1f5f9;            /* light/white so it reads on dark bg */
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .s2c-wordmark span {
        color: #818cf8;            /* indigo-400 accent for the "2" */
    }
    .s2c-tagline {
        font-size: 1rem;
        color: #64748b;
        font-weight: 400;
        margin: 0;
    }

    /* ── Field labels above each control ── */
    .field-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 0.3rem;
    }

    /* ── Input card wrappers ── */
    .s2c-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1rem 1.1rem 0.9rem;
        margin-bottom: 0.75rem;
    }

    /* ── Override Streamlit's default widget label to zero-margin
           (we're rendering our own labels above) ── */
    .stTextInput label, .stSelectbox label, .stFileUploader label {
        display: none !important;
    }

    /* ── Make widgets fill their column ── */
    .stTextInput > div, .stSelectbox > div {
        width: 100% !important;
    }

    /* ── Primary CTA button ── */
    div.stButton > button[kind="primary"] {
        width: 100%;
        padding: 0.72rem 1rem;
        font-size: 1rem;
        font-weight: 700;
        border-radius: 10px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        color: #ffffff;
        letter-spacing: 0.01em;
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.38);
        transition: opacity 0.15s;
    }
    div.stButton > button[kind="primary"]:hover { opacity: 0.86; }

    /* ── Output campaign header ── */
    .s2c-output-header {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 1.2rem 0 0.2rem;
    }
    .s2c-output-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #f1f5f9;
        letter-spacing: -0.02em;
    }
    .s2c-badge-success {
        background: #14532d;
        color: #4ade80;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
    }

    /* ── Output section labels ── */
    .s2c-section-label {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #475569;
        margin: 1.4rem 0 0.45rem;
    }

    /* ── Tagline ── */
    .s2c-tagline-display {
        font-size: 1.65rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1.25;
        letter-spacing: -0.025em;
        padding: 0.5rem 0;
    }

    /* ── Social copy card ── */
    .s2c-copy-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1rem 1.15rem;
        font-size: 0.94rem;
        line-height: 1.7;
        color: #cbd5e1;
        white-space: pre-wrap;
        margin-bottom: 0.65rem;
    }

    /* ── Tab text ── */
    button[data-baseweb="tab"] {
        font-size: 0.88rem;
        font-weight: 600;
        color: #94a3b8;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #818cf8;
    }

    /* ── Hero image container: capped width, centred ── */
    .s2c-hero-wrap {
        max-width: 780px;
        margin: 0 auto;
    }

    /* ── Dividers ── */
    hr {
        border-color: #1e293b;
        margin: 1.2rem 0;
    }

    /* ── Empty state ── */
    .s2c-empty {
        text-align: center;
        padding: 0.6rem 1rem 0.3rem;
        color: #475569;
        font-size: 0.88rem;
    }
    .s2c-steps {
        display: flex;
        justify-content: center;
        gap: 0.35rem;
        flex-wrap: wrap;
        margin-top: 0.3rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
        letter-spacing: 0.03em;
    }
    .s2c-step-sep { color: #334155; }

    /* ── Responsive: single column on narrow viewports ── */
    @media (max-width: 640px) {
        .block-container { padding: 1rem 1rem 2rem !important; }
        .s2c-wordmark { font-size: 2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers (unchanged) ───────────────────────────────────────────────────────

def get_artifacts_dir() -> Path:
    """Return (and create) the artifacts output directory."""
    artifacts = Path("artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    return artifacts


def download_image(image_url: str, target_path: Path) -> Path:
    """Download a remote image to a local path and return that path."""
    response = httpx.get(image_url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    target_path.write_bytes(response.content)
    return target_path


def save_uploaded_photo(uploaded_file, artifacts_dir: Path) -> Path:
    """Persist the user's uploaded product photo to artifacts/ and return its path."""
    ext = Path(uploaded_file.name).suffix or ".jpg"
    dest = artifacts_dir / f"product_photo{ext}"
    dest.write_bytes(uploaded_file.getbuffer())
    return dest


# ── Brand header ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="s2c-header">
        <div class="s2c-wordmark">Snap<span>2</span>Campaign</div>
        <p class="s2c-tagline">Turn a product into a campaign.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Input form ────────────────────────────────────────────────────────────────

# — Product photo (full width) —
st.markdown('<p class="field-label">📸 &nbsp;Product Photo &nbsp;<span style="font-weight:400;text-transform:none;letter-spacing:0;color:#334155">(optional)</span></p>', unsafe_allow_html=True)
with st.container(border=True):
    uploaded_photo = st.file_uploader(
        "Product photo",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
        help="If AI image generation is unavailable, your photo will be used as the campaign visual.",
    )
    if uploaded_photo is None:
        st.caption("Drag & drop or browse  ·  JPG, PNG, WEBP")

st.write("")   # small gap before the 2-col grid

# — 2-column input grid —
col_left, col_right = st.columns(2, gap="medium")

with col_left:
    # Product
    st.markdown('<p class="field-label">✏️ &nbsp;Product</p>', unsafe_allow_html=True)
    with st.container(border=True):
        product = st.text_input(
            "Product name or description",
            placeholder="e.g.  iQOO Neo 9 Pro — 144 Hz gaming phone",
            label_visibility="collapsed",
        )

    # Target Audience
    st.markdown('<p class="field-label">👥 &nbsp;Target Audience</p>', unsafe_allow_html=True)
    with st.container(border=True):
        audience_choice = st.selectbox(
            "Target Audience",
            options=AUDIENCE_OPTIONS,
            label_visibility="collapsed",
        )
        if audience_choice == "Custom…":
            audience = st.text_input(
                "Describe your audience",
                placeholder="e.g.  small business owners in tier-2 cities",
                label_visibility="collapsed",
            )
        else:
            audience = audience_choice

with col_right:
    # Advertising Goal
    st.markdown('<p class="field-label">🎯 &nbsp;Advertising Goal</p>', unsafe_allow_html=True)
    with st.container(border=True):
        ad_goal = st.selectbox(
            "Advertising Goal",
            options=AD_GOALS,
            label_visibility="collapsed",
        )

    # Brand Tone
    st.markdown('<p class="field-label">🎨 &nbsp;Brand Tone</p>', unsafe_allow_html=True)
    with st.container(border=True):
        tone = st.selectbox(
            "Brand Tone",
            options=list(TONE_STYLES.keys()),
            format_func=str.capitalize,
            label_visibility="collapsed",
        )

# — CTA (centred) —
st.write("")
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    create_btn = st.button("⚡  Create Campaign", type="primary")

# — Empty state (compact, shown only before first click) —
if not create_btn:
    st.markdown(
        """
        <div class="s2c-empty">
            <div class="s2c-steps">
                <span>Upload</span>
                <span class="s2c-step-sep">&nbsp;→&nbsp;</span>
                <span>Describe</span>
                <span class="s2c-step-sep">&nbsp;→&nbsp;</span>
                <span>Create</span>
                <span class="s2c-step-sep">&nbsp;→&nbsp;</span>
                <span>Get Campaign</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Generation pipeline ───────────────────────────────────────────────────────
if create_btn:
    # Validate required fields
    if not product:
        st.error("Please enter a product name or description.")
        st.stop()
    if not audience:
        st.error("Please describe your target audience.")
        st.stop()

    # Output header
    st.markdown(
        """
        <div class="s2c-output-header">
            <span class="s2c-output-title">Your Campaign</span>
            <span class="s2c-badge-success">READY</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    artifacts_dir = get_artifacts_dir()

    # Save the uploaded photo early so it is available as a fallback if AI
    # image generation fails. The path is None when no photo was uploaded.
    uploaded_photo_path: Path | None = None
    if uploaded_photo is not None:
        uploaded_photo_path = save_uploaded_photo(uploaded_photo, artifacts_dir)

    # ── Stage 1: Hero image ───────────────────────────────────────────────────
    # Try AI generation first. On any failure, fall back to the uploaded photo
    # if one was provided; otherwise halt with an error.
    image_url: str | None = None      # remote URL (set only on AI success)
    hero_path: Path | None = None     # local PNG path (set on AI success or fallback)
    used_photo_fallback: bool = False  # True when the uploaded photo is the hero visual
    image_prompt: str = ""

    with st.spinner("Creating hero visual…"):
        try:
            image_url, image_prompt = generate_image(
                product, audience, tone, tagline="", ad_goal=ad_goal
            )
        except Exception as e:
            err = str(e)
            # Surface the specific failure reason so it is never hidden.
            if "billing_hard_limit_reached" in err or "Billing hard limit" in err:
                st.warning(
                    "AI image generation is currently unavailable (spending limit reached). "
                    "Using your uploaded photo as the campaign visual."
                )
            elif "402" in err or "credits" in err.lower():
                st.warning(
                    "AI image generation is currently unavailable (credits needed). "
                    "Using your uploaded photo as the campaign visual."
                )
            else:
                st.warning("AI image generation is currently unavailable. Using your uploaded photo.")

            # Attempt fallback to the uploaded product photo.
            if uploaded_photo_path is not None and uploaded_photo_path.exists():
                used_photo_fallback = True
            else:
                # No photo uploaded and AI failed — cannot continue.
                st.error(
                    "No campaign visual available. "
                    "Upload a product photo to generate a campaign without AI image generation."
                )
                st.stop()

    if not used_photo_fallback:
        # AI generation succeeded — download to local PNG for video fallback.
        hero_path = artifacts_dir / "hero_image.png"
        with st.spinner("Preparing hero image…"):
            try:
                hero_path = download_image(image_url, hero_path)
            except Exception as e:
                st.warning(f"Could not download hero image; showing remote preview only. {e}")
                # If the download fails but the user uploaded a photo, use it
                # as the local image source for Ken Burns video generation.
                hero_path = uploaded_photo_path if (
                    uploaded_photo_path is not None and uploaded_photo_path.exists()
                ) else None
    else:
        # Use the uploaded photo as the hero image.
        # Apply a light PIL presentation treatment: convert to RGB PNG, add a
        # subtle 6-pixel dark border so it reads as a "campaign visual" frame.
        # PIL is already a project dependency (Pillow); no new packages needed.
        from PIL import Image as _PILImage, ImageOps as _ImageOps

        hero_path = artifacts_dir / "hero_image.png"
        try:
            with _PILImage.open(uploaded_photo_path) as img:
                img = img.convert("RGB")
                # Resize to a standard 16:9 canvas (max 1280 wide) while keeping
                # the product centred — letterbox/pillarbox with a dark background.
                target_w, target_h = 1280, 720
                img.thumbnail((target_w, target_h), _PILImage.LANCZOS)
                canvas = _PILImage.new("RGB", (target_w, target_h), (18, 18, 18))
                offset_x = (target_w - img.width) // 2
                offset_y = (target_h - img.height) // 2
                canvas.paste(img, (offset_x, offset_y))
                # Thin dark border as a minimal "ad frame"
                canvas = _ImageOps.expand(canvas, border=6, fill=(30, 30, 30))
                canvas.save(hero_path, "PNG")
        except Exception as pil_err:
            # If PIL treatment fails, just copy the raw upload bytes as-is.
            st.warning(f"Could not apply image treatment: {pil_err}. Using raw photo.")
            hero_path.write_bytes(uploaded_photo_path.read_bytes())

    # ── Hero visual display ───────────────────────────────────────────────────
    st.markdown('<div class="s2c-section-label">Hero Visual</div>', unsafe_allow_html=True)

    # Cap the hero image at ~780px centred — avoids full-bleed stretch on wide screens.
    hero_col, _ = st.columns([2, 1])
    with hero_col:
        if used_photo_fallback:
            st.image(str(hero_path), use_container_width=True)
        else:
            st.image(image_url, use_container_width=True)
            with st.expander("View image prompt"):
                st.caption(image_prompt)

    st.divider()

    # ── Stage 2: Tagline ──────────────────────────────────────────────────────
    with st.spinner("Writing tagline…"):
        try:
            tagline = generate_tagline(product, audience, tone, ad_goal=ad_goal)
        except Exception as e:
            st.error(f"Tagline generation failed: {e}")
            st.stop()

    st.markdown('<div class="s2c-section-label">Campaign Tagline</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="s2c-tagline-display">{tagline}</div>', unsafe_allow_html=True)

    st.divider()

    # ── Stage 3: Social media copy ────────────────────────────────────────────
    # The blog intro is generated internally as context for social posts but is
    # not shown on its own – the output is social-first.
    with st.spinner("Writing social media copy…"):
        try:
            blog = generate_blog(product, audience, tone, tagline, ad_goal=ad_goal)
            posts = generate_social_posts(
                product, audience, tone, blog, tagline, ad_goal=ad_goal
            )
        except json.JSONDecodeError as e:
            st.error(f"Social media copy generation failed: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Social media copy generation failed: {e}")
            st.stop()

    st.markdown('<div class="s2c-section-label">Social Media Content</div>', unsafe_allow_html=True)

    # Social tabs in a readable column (not full bleed)
    social_col, _ = st.columns([2, 1])
    with social_col:
        tab_ig, tab_li, tab_tw = st.tabs(["Instagram", "LinkedIn", "X / Twitter"])
        with tab_ig:
            ig_text = posts.get("instagram", "")
            st.markdown(f'<div class="s2c-copy-card">{ig_text}</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇ Download Instagram copy",
                data=ig_text,
                file_name="instagram_copy.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with tab_li:
            li_text = posts.get("linkedin", "")
            st.markdown(f'<div class="s2c-copy-card">{li_text}</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇ Download LinkedIn copy",
                data=li_text,
                file_name="linkedin_copy.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with tab_tw:
            tw_text = posts.get("twitter", "")
            st.markdown(f'<div class="s2c-copy-card">{tw_text}</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇ Download X copy",
                data=tw_text,
                file_name="x_copy.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.divider()

    # ── Stage 4: Promotional video ────────────────────────────────────────────
    st.markdown('<div class="s2c-section-label">Promotional Video</div>', unsafe_allow_html=True)

    local_video_path = artifacts_dir / "hero_video.mp4"

    try:
        # Runway requires a publicly accessible image URL. Skip the cloud attempt
        # when we are in fallback mode (no remote URL exists) so we go straight to
        # the local Ken Burns render without surfacing a confusing Runway error.
        if image_url is None:
            raise RuntimeError("No remote image URL available; using local video fallback.")

        with st.spinner("Generating promotional video — this may take ~60 s…"):
            video_url = generate_video(
                image_url, product, tone, tagline, ad_goal=ad_goal
            )
        st.video(video_url)

    except Exception:
        if hero_path is not None and hero_path.exists():
            with st.spinner("Rendering video…"):
                try:
                    create_ken_burns(str(hero_path), str(local_video_path), duration=VIDEO_DURATION)
                    st.video(str(local_video_path))
                except Exception as fallback_error:
                    st.error(f"Video rendering failed: {fallback_error}")
        else:
            st.error("Video unavailable: hero image could not be prepared.")

    st.divider()

    # ── Download section ──────────────────────────────────────────────────────
    st.markdown('<div class="s2c-section-label">Download Assets</div>', unsafe_allow_html=True)

    dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 2])

    with dl_col1:
        if hero_path is not None and hero_path.exists():
            with open(hero_path, "rb") as f:
                st.download_button(
                    "⬇ Hero Image",
                    data=f,
                    file_name="hero_image.png",
                    mime="image/png",
                    use_container_width=True,
                )

    with dl_col2:
        if local_video_path.exists():
            with open(local_video_path, "rb") as f:
                st.download_button(
                    "⬇ Promo Video",
                    data=f,
                    file_name="promo_video.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                )

    st.write("")
    st.success("Campaign complete — ready to publish. ⚡")
