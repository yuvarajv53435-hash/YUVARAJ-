import os
import time
from .gemini_flash import generate_with_retry

def get_gemini_model(model_name="gemini-2.0-flash"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "demo_mode" or api_key.startswith("your_"):
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Gemini Pro init failed: {e}")
        return None

def generate_story(
    outline: list, 
    character: str = "Hero", 
    setting: str = "fantasy world", 
    tone: str = "adventurous", 
    art_style: str = "comic book"
) -> str:
    # Use standard gemini-2.0-flash or gemini-1.5-flash
    model = get_gemini_model("gemini-2.0-flash")
    
    formatted = "\n".join([
        f"{i+1}. {o.get('title','Panel')} - {o.get('scene_description','')}" 
        for i, o in enumerate(outline)
    ])
    
    prompt = f"""
You are a comic book writer.
Given panel breakdown, write comic story with narration and dialogues.

Character: {character}
Setting: {setting}
Tone: {tone}
Art Style: {art_style}

Outline:
{formatted}

Format exactly like:
**Panel 1: Title**
Caption:...
Narration:...
{character}: "dialogue"

**Panel 2: Title**
...
"""

    if model is None:
        print("⚠️ Using MOCK story")
        parts = []
        for o in outline:
            p = o.get('panel', 1)
            title = o.get('title', f'Panel {p}')
            desc = o.get('scene_description', '')
            parts.append(f"""**Panel {p}: {title}**
Caption: The scene opens in {setting}, with {tone} atmosphere.
Narration: {desc} {character} is feeling determined.
{character}: "This is just the beginning of something amazing!"
Image Prompt Reference: {o.get('image_prompt', '')}""")
        return "\n\n".join(parts)

    try:
        # Use generate_with_retry instead of raw model.generate_content
        response = generate_with_retry(model, prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ API Call Failed with error: {e}. Falling back to mock story.")
        
        # Fallback to mock text if API fails/quota runs out
        parts = []
        for o in outline:
            p = o.get('panel', 1)
            title = o.get('title', f'Panel {p}')
            desc = o.get('scene_description', '')
            parts.append(f"""**Panel {p}: {title}**
Caption: The scene opens in {setting}, with {tone} atmosphere.
Narration: {desc} {character} is feeling determined.
{character}: "This is just the beginning of something amazing!"
Image Prompt Reference: {o.get('image_prompt', '')}""")
        return "\n\n".join(parts)