from app.config import settings


def generate_story(
    outline,
    prompt: str,
    character_name: str = "Alex",
    tone: str = "adventurous",
):
    if settings.gemini_api_key:
        try:
            import json
            import re

            from google import genai

            client = genai.Client(
                api_key=settings.gemini_api_key
            )

            instruction = f"""
Write short, lively comic narration for exactly these panels.

Original idea: {prompt}
Hero: {character_name}
Tone: {tone}

For each panel, return a JSON array item with:
- panel_number
- caption
- narration
- dialogue

Keep narration to 1-3 sentences.
Make dialogue natural and family-friendly.
Do not change the plot.

OUTLINE:
{outline}

Return only valid JSON.
"""

            response = client.models.generate_content(
                model=settings.gemini_story_model,
                contents=instruction,
            )

            raw = re.sub(
                r"^```(?:json)?\s*|\s*```$",
                "",
                (response.text or "").strip(),
                flags=re.I,
            )

            start = raw.find("[")
            end = raw.rfind("]")

            if start < 0 or end < start:
                raise ValueError("Gemini returned invalid JSON.")

            data = json.loads(raw[start : end + 1])

            by_num = {
                int(item.get("panel_number", i + 1)): item
                for i, item in enumerate(data)
            }

            story = []

            for i, panel in enumerate(outline):
                item = by_num.get(i + 1, {})

                story.append(
                    {
                        "panel_number": i + 1,
                        "caption": str(
                            item.get(
                                "caption",
                                "A moment that changes everything.",
                            )
                        ),
                        "narration": str(
                            item.get(
                                "narration",
                                panel["scene_description"],
                            )
                        ),
                        "dialogue": str(
                            item.get(
                                "dialogue",
                                f'{character_name}: "Let us see where this leads!"',
                            )
                        ),
                    }
                )

            return story

        except Exception:
            # Use local fallback if the API call fails.
            pass

    captions = [
        "A quiet day takes an unexpected turn.",
        "Every clue leads somewhere new.",
        "The stakes are higher than ever.",
        "A little creativity changes everything.",
        "And so, a new story begins.",
    ]

    dialogues = [
        "What is that?",
        "There has to be a clue.",
        "I will not give up now!",
        "I have an idea!",
        "This is only the beginning!",
    ]

    story = []

    for panel in outline:
        index = panel["panel_number"] - 1

        story.append(
            {
                "panel_number": panel["panel_number"],
                "caption": captions[index],
                "narration": panel["scene_description"],
                "dialogue": f"{character_name}: “{dialogues[index]}”",
            }
        )

    return story