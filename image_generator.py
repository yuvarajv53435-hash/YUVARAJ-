"""
app/image_generator.py

Image backends (choose with IMAGE_BACKEND in .env):
  gemini        Gemini image model (needs billing; free tier has 0 image quota)
  pollinations  Free, no API key
  sd            Local Stable Diffusion (slow without a GPU)
  placeholder   Simple drawn image, no network

If the chosen backend fails, the app falls back to the placeholder image.
"""

import os
import re
import uuid
import random
import urllib.parse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"

_pipe = None


def sanitize_filename(prompt: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", prompt)[:50].strip("_") or "panel"
    return f"{safe}_{uuid.uuid4().hex[:6]}.png"


# ---------------- Gemini ----------------

def generate_gemini_image(prompt: str, path: Path) -> bool:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ No GEMINI_API_KEY / GOOGLE_API_KEY found in environment")
        return False

    from google import genai

    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    client = genai.Client(api_key=api_key)

    full_prompt = (
        f"{prompt}. Comic book panel illustration, vibrant colors, "
        f"detailed, dramatic lighting. No text, no speech bubbles, no captions."
    )

    resp = client.models.generate_content(model=model, contents=full_prompt)

    if not resp.candidates:
        print(f"⚠️ Gemini returned no candidates (possibly blocked): {resp}")
        return False

    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            path.write_bytes(inline.data)
            print(f"✅ Gemini image saved: {path}")
            return True

    print("⚠️ Gemini response contained no image data")
    return False


# ---------------- Pollinations (free) ----------------

def generate_pollinations_image(prompt: str, path: Path) -> bool:
    import time
    import requests

    full_prompt = f"{prompt[:350]}, comic book panel illustration, vibrant colors, dramatic lighting"

    for attempt in range(1, 6):
        url = (
            "https://image.pollinations.ai/prompt/"
            + urllib.parse.quote(full_prompt)
            + "?width=768&height=512&nologo=true&model=flux"
            + f"&seed={random.randint(1, 999999)}"
        )
        try:
            r = requests.get(url, timeout=150)
        except requests.RequestException as e:
            print(f"⚠️ Pollinations request error (try {attempt}/5): {e}")
            time.sleep(15)
            continue

        ctype = r.headers.get("content-type", "")
        if r.status_code == 200 and ctype.startswith("image"):
            path.write_bytes(r.content)
            print(f"✅ Pollinations image saved: {path}")
            time.sleep(15)  # pause so the next panel isn't rate-limited
            return True

        print(f"⚠️ Pollinations HTTP {r.status_code} (try {attempt}/5): {r.text[:150]!r}")
        time.sleep(20 * attempt)

    return False


# ---------------- Local Stable Diffusion ----------------

def get_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe
    try:
        import torch
        from diffusers import AutoPipelineForText2Image

        model_id = os.getenv("SD_MODEL", "stabilityai/sd-turbo")
        use_cuda = torch.cuda.is_available()
        print(f"🔄 Loading {model_id} on {'GPU' if use_cuda else 'CPU'} (first run downloads ~2-3 GB)...")
        kwargs = {"torch_dtype": torch.float16, "variant": "fp16"} if use_cuda else {"torch_dtype": torch.float32}
        _pipe = AutoPipelineForText2Image.from_pretrained(model_id, **kwargs)
        _pipe = _pipe.to("cuda" if use_cuda else "cpu")
        return _pipe
    except Exception as e:
        print(f"⚠️ Local image model not available: {type(e).__name__}: {e}")
        return None


def generate_sd_image(prompt: str, path: Path) -> bool:
    pipe = get_pipeline()
    if not pipe:
        return False
    enhanced = (
        f"{prompt[:300]}, comic book panel illustration, "
        f"vibrant colors, bold outlines, dramatic lighting"
    )
    image = pipe(
        prompt=enhanced,
        num_inference_steps=2,
        guidance_scale=0.0,
        width=512,
        height=512,
    ).images[0]
    image.save(path)
    print(f"✅ Local image saved: {path}")
    return True
# ---------------- Placeholder ----------------

def generate_placeholder_image(prompt: str, path: Path):
    from PIL import Image, ImageDraw, ImageFont

    colors = [
        (255, 230, 109), (255, 111, 97), (93, 211, 158),
        (90, 155, 255), (255, 154, 60), (180, 120, 255),
    ]
    img = Image.new("RGB", (768, 512), color=random.choice(colors))
    draw = ImageDraw.Draw(img)

    for _ in range(300):
        x, y, r = random.randint(0, 768), random.randint(0, 512), random.randint(1, 3)
        draw.ellipse([x, y, x + r, y + r], fill=(0, 0, 0))

    draw.rectangle([0, 0, 767, 511], outline=(0, 0, 0), width=8)
    draw.rectangle([20, 20, 748, 80], fill=(0, 0, 0), outline=(0, 0, 0), width=3)
    draw.rectangle([20, 320, 748, 492], fill=(255, 255, 255), outline=(0, 0, 0), width=3)

    try:
        font_big = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((30, 30), "COMIC PANEL (placeholder)", fill=(255, 255, 255), font=font_big)

    def wrap(text, width=38):
        words, lines, cur = text.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 <= width:
                cur = f"{cur} {w}".strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines[:7]

    y = 330
    for line in wrap(prompt):
        draw.text((30, y), line, fill=(0, 0, 0), font=font_small)
        y += 20

    img.save(path)
    print(f"✅ Placeholder saved: {path}")


# ---------------- Entry point ----------------

def generate_image(prompt: str, filename: str = None) -> str:
    if not filename:
        filename = sanitize_filename(prompt)

    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    path = PANELS_DIR / filename
    rel_path = f"static/panels/{filename}"

    backend = os.getenv("IMAGE_BACKEND", "").strip().lower()
    if not backend:
        backend = "sd" if os.getenv("USE_SD", "false").lower() == "true" else "gemini"

    print(f"🖼️ Image backend: {backend!r}")

    generators = {
        "gemini": ("Gemini", generate_gemini_image),
        "pollinations": ("Pollinations", generate_pollinations_image),
        "sd": ("SD", generate_sd_image),
    }

    if backend in generators:
        label, fn = generators[backend]
        try:
            print(f"🎨 {label}: {prompt[:60]}...")
            if fn(prompt, path):
                return rel_path
        except Exception as e:
            print(f"❌ {label} image failed: {type(e).__name__}: {e}")

    print("⚠️ Falling back to placeholder image")
    generate_placeholder_image(prompt, path)
    return rel_path