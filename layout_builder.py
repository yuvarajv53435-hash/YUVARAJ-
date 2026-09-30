def build_comic_layout(image_paths, full_story, outline):
    panels = [p for p in full_story.split("**Panel") if p.strip()]
    if len(panels) < len(image_paths):
        panels = full_story.split("\n\n")
        if len(panels) < len(image_paths):
            panels = [full_story] * len(image_paths)

    layout = []
    for idx, (image, text, info) in enumerate(zip(image_paths, panels, outline), start=1):
        clean = "\n".join([l.strip() for l in text.strip().splitlines() if l.strip()]).strip()
        if not clean.startswith("**Panel"):
            clean = f"**Panel {idx}: {info.get('title','')}**\n{clean}"
        layout.append({
            "panel": idx,
            "title": info.get("title", f"Panel {idx}"),
            "image_path": image,
            "text": clean,
            "scene_description": info.get("scene_description",""),
            "image_prompt": info.get("image_prompt","")
        })
    return layout