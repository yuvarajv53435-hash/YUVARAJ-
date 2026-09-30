import io
import re
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
PANEL_DIR = BASE_DIR / "static" / "panels"
PANEL_DIR.mkdir(parents=True, exist_ok=True)


def _font(size):
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass

    return ImageFont.load_default()


def _placeholder(prompt: str, filename: str):
    """Create a local scene card for testing without external AI services."""
    img = Image.new("RGB", (768, 512), (24, 35, 66))
    draw = ImageDraw.Draw(img)

    for y in range(512):
        color = (
            int(28 + y * 0.12),
            int(44 + y * 0.10),
            int(83 + y * 0.16),
        )
        draw.line((0, y, 768, y), fill=color)

    draw.ellipse((520, 35, 640, 155), fill=(255, 216, 122))
    draw.polygon(
        [(0, 390), (180, 170), (330, 390)],
        fill=(47, 105, 91),
    )
    draw.polygon(
        [(180, 390), (420, 130), (650, 390)],
        fill=(31, 79, 81),
    )
    draw.polygon(
        [
            (430, 390),
            (620, 210),
            (768, 350),
            (768, 512),
            (0, 512),
            (0, 430),
        ],
        fill=(18, 49, 58),
    )

    draw.rounded_rectangle(
        (28, 350, 740, 480),
        radius=18,
        fill=(9, 17, 35),
    )

    draw.text(
        (48, 365),
        "COMICCRAFT - AI SCENE",
        font=_font(22),
        fill=(255, 215, 105),
    )

    words = re.sub(r"\s+", " ", prompt).strip()

    draw.text(
        (48, 405),
        words[:78],
        font=_font(17),
        fill="white",
    )

    path = PANEL_DIR / filename
    img.save(path, "JPEG", quality=90)

    return f"/static/panels/{filename}"


def _huggingface_image(prompt: str, filename: str):
    import requests

    url = (
        "https://api-inference.huggingface.co/models/"
        f"{settings.hf_image_model}"
    )

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.hf_api_key}"
        },
        json={"inputs": prompt},
        timeout=settings.request_timeout,
    )

    response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    if "image" not in content_type:
        raise RuntimeError(
            "Image provider did not return an image. "
            "Check HF_API_KEY and model access."
        )

    image = Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")

    image.save(PANEL_DIR / filename, "JPEG", quality=92)

    return f"/static/panels/{filename}"


def _diffusers_image(prompt: str, filename: str):
    import torch
    from diffusers import StableDiffusionPipeline

    model_id = settings.diffusers_model

    dtype = (
        torch.float16
        if torch.cuda.is_available()
        else torch.float32
    )

    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
        safety_checker=None,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = pipe.to(device)

    image = pipe(
        prompt,
        num_inference_steps=25,
        guidance_scale=7.0,
    ).images[0]

    image.save(PANEL_DIR / filename, "JPEG", quality=92)

    return f"/static/panels/{filename}"


def generate_image(
    prompt: str,
    art_style: str = "comic book",
):
    filename = f"panel_{uuid.uuid4().hex}.jpg"

    full_prompt = (
        f"{art_style} illustration, {prompt}, "
        "polished composition, vivid colors, "
        "no words, no watermark"
    )

    backend = settings.image_backend.lower()

    if backend == "placeholder":
        return _placeholder(full_prompt, filename)

    if backend == "diffusers" or settings.use_local_diffusers:
        try:
            return _diffusers_image(full_prompt, filename)
        except Exception:
            return _placeholder(full_prompt, filename)

    if settings.hf_api_key and backend in ("auto", "huggingface"):
        try:
            return _huggingface_image(full_prompt, filename)
        except Exception:
            if backend == "huggingface":
                return _placeholder(full_prompt, filename)

    return _placeholder(full_prompt, filename)