import json
import re

from app.config import settings


def _fallback_outline(
    prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
):
    beats = [
        (
            "The Unexpected Beginning",
            f"{character_name} discovers something unusual in {setting}.",
        ),
        (
            "A Curious Clue",
            f"A strange clue reveals that the adventure is only beginning for {character_name}.",
        ),
        (
            "Trouble Appears",
            f"An unexpected obstacle challenges {character_name}, testing their courage and wit.",
        ),
        (
            "A Clever Plan",
            f"{character_name} finds a creative way to solve the problem and help those around them.",
        ),
        (
            "A New Legend",
            "The adventure ends with a meaningful discovery and a hint of future adventures.",
        ),
    ]

    return [
        {
            "panel_number": i + 1,
            "title": title,
            "scene_description": description,
            "image_prompt": (
                f"{art_style} illustration, {setting}, {description} "
                f"Main character: {character_name}. "
                f"{tone} mood, expressive faces, cinematic composition, "
                "no text, no lettering."
            ),
        }
        for i, (title, description) in enumerate(beats)
    ]


def generate_outline(
    prompt: str,
    character_name: str = "Alex",
    setting: str = "enchanted forest",
    tone: str = "adventurous",
    art_style: str = "comic book",
):
    if not settings.gemini_api_key:
        return _fallback_outline(
            prompt, character_name, setting, tone, art_style
        )

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)

        instruction = f"""
Create exactly 5 coherent comic panels for this idea: {prompt}

Hero: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}

Return ONLY a valid JSON array.
Each item must contain:
- panel_number (integer)
- title
- scene_description
- image_prompt

Make the plot have a beginning, development, obstacle,
resolution, and satisfying ending.

Image prompts must describe one clear visual scene,
repeat the character's visual identity, and request no
text or lettering.
"""

        response = client.models.generate_content(
            model=settings.gemini_outline_model,
            contents=instruction,
        )

        raw = response.text or ""
        raw = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw.strip(),
            flags=re.I,
        )

        start = raw.find("[")
        end = raw.rfind("]")

        if start < 0 or end < start:
            raise ValueError("Gemini returned invalid JSON.")

        data = json.loads(raw[start : end + 1])

        if not isinstance(data, list) or len(data) < 5:
            raise ValueError("Model did not return five panels.")

        result = []

        for i, panel in enumerate(data[:5]):
            result.append(
                {
                    "panel_number": i + 1,
                    "title": str(
                        panel.get("title", f"Panel {i + 1}")
                    )[:120],
                    "scene_description": str(
                        panel.get("scene_description", "")
                    )[:1200],
                    "image_prompt": str(
                        panel.get(
                            "image_prompt",
                            f"{art_style} illustration of "
                            f"{character_name} in {setting}",
                        )
                    )[:1500],
                }
            )

        return result

    except Exception:
        # Fallback keeps the basic application workflow usable.
        return _fallback_outline(
            prompt, character_name, setting, tone, art_style
        )