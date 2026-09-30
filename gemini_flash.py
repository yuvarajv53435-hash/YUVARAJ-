import os
import json
import re
import time


def generate_with_retry(model, prompt, tries=4):
    """Call Gemini; if the per-minute rate limit is hit, wait and try again."""
    for attempt in range(1, tries + 1):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            msg = str(e)
            per_minute = "429" in msg and "PerDay" not in msg
            if per_minute and attempt < tries:
                print(f"⏳ Rate limited, waiting 40s (try {attempt}/{tries})...")
                time.sleep(40)
                continue
            raise


def get_gemini_model(model_name="models/gemini-3.5-flash-lite"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "demo_mode" or api_key.startswith("your_"):
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Gemini init failed: {e}")
        return None


def generate_outline(user_prompt: str, character: str="Hero", setting: str="fantasy world", tone: str="adventurous", art_style: str="comic book") -> list:
    model = get_gemini_model("models/gemini-3.5-flash-lite")
    full_prompt = f"""
You are a professional AI comic planner.
Generate a strictly formatted JSON array containing 5 panel descriptions.

STORY: "{user_prompt}"
MAIN CHARACTER: {character}
SETTING: {setting}
TONE: {tone}
ART STYLE: {art_style}

Each object must include:
- "panel" (1-5)
- "title" (short catchy)
- "scene_description" (1-2 sentences)
- "image_prompt" (detailed Stable Diffusion prompt with {art_style}, {character}, {setting}, {tone})

Respond ONLY in valid JSON format:
[
  {{
    "panel": 1,
    "title": "Title",
    "scene_description": "Description",
    "image_prompt": "Image prompt"
  }}
]
"""
    if model is None:
        print("⚠️ Using MOCK outline (no API key)")
        titles = ["The Beginning", "The Challenge", "The Twist", "The Climax", "The Resolution"]
        return [{
            "panel": i,
            "title": titles[i-1],
            "scene_description": f"Panel {i}: {character} begins adventure in {setting}. {user_prompt[:80]}. Tone: {tone}.",
            "image_prompt": f"{art_style} comic style, {character} in {setting}, {tone} mood, panel {i}: {user_prompt}, dramatic lighting, highly detailed"
        } for i in range(1,6)]

    try:
        response = generate_with_retry(model, full_prompt)
        text = response.text.strip()
        if "```json" in text: text = text.replace("```json","").replace("```","").strip()
        elif "```" in text: text = text.replace("```","").strip()
        m = re.search(r'\[.*\]', text, re.DOTALL)
        if m: text = m.group(0)
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"❌ Outline Error: {e}")
        return [{
            "panel": i,
            "title": f"Panel {i}",
            "scene_description": f"Error fallback: {character} in {setting}",
            "image_prompt": f"{art_style} comic, {character}, {setting}"
        } for i in range(1,6)]