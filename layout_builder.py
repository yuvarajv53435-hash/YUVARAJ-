def build_comic_layout(outline, story, image_paths):
    story_by_num = {
        int(item["panel_number"]): item
        for item in story
    }

    layout = []

    for index, panel in enumerate(outline):
        story_item = story_by_num.get(index + 1, {})

        layout.append(
            {
                "panel_number": index + 1,
                "title": panel.get(
                    "title", f"Panel {index + 1}"
                ),
                "scene_description": panel.get(
                    "scene_description", ""
                ),
                "image_prompt": panel.get("image_prompt", ""),
                "image_path": image_paths[index],
                "caption": story_item.get("caption", ""),
                "narration": story_item.get("narration", ""),
                "dialogue": story_item.get("dialogue", ""),
            }
        )

    return layout