from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


# --------------------------------------------------
# Router / Templates
# --------------------------------------------------

router = APIRouter()

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


# --------------------------------------------------
# Request model
# --------------------------------------------------

class PromptRequest(BaseModel):
    story_prompt: str
    character_name: str = "Hero"
    setting: str = "fantasy world"
    tone: str = "adventurous"
    art_style: str = "comic book"


# --------------------------------------------------
# Home page
# --------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# --------------------------------------------------
# Generate comic - HTML form
# --------------------------------------------------

@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form("Hero"),
    setting: str = Form("fantasy world"),
    tone: str = Form("adventurous"),
    art_style: str = Form("comic book")
):

    try:

        # Generate story outline
        outline = generate_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style
        )

        # Check for errors from Gemini
        if (
            outline
            and isinstance(outline, list)
            and len(outline) > 0
            and isinstance(outline[0], dict)
            and "error" in outline[0]
        ):

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "request": request,
                    "error": outline[0]["error"]
                }
            )

        # Generate full story
        full_story = generate_story(
            outline,
            character_name,
            setting,
            tone,
            art_style
        )

        # Generate images
        image_paths = []

        for panel in outline:

            img_prompt = panel.get(
                "image_prompt",
                story_prompt
            )

            enhanced_prompt = (
                f"{img_prompt}, "
                f"{art_style} style, "
                f"{tone} tone"
            )

            path = generate_image(enhanced_prompt)

            image_paths.append(path)

        # Build comic layout
        layout = build_comic_layout(
            image_paths,
            full_story,
            outline
        )

        # Save PDF
        pdf_path = save_pdf(
            layout,
            story_prompt
        )

         # Show preview
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "request": request,
                "layout": layout,
                "pdf_path": pdf_path,
                "story_prompt": story_prompt,
                "character_name": character_name,
                "setting": setting,
                "tone": tone,
                "art_style": art_style
            }
        )

    except Exception as e:
        
        print(f"❌ Error generating comic: {e}")

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "error": f"Failed: {str(e)}"
            }
        )


# --------------------------------------------------
# Generate comic - JSON API
# --------------------------------------------------

@router.post("/generate-comic/json")
async def generate_comic_json(
    data: PromptRequest
):

    try:

        # Generate outline
        outline = generate_outline(
            data.story_prompt,
            data.character_name,
            data.setting,
            data.tone,
            data.art_style
        )

        # Generate story
        full_story = generate_story(
            outline,
            data.character_name,
            data.setting,
            data.tone,
            data.art_style
        )

        # Generate images
        image_paths = []

        for panel in outline:

            image_prompt = panel.get(
                "image_prompt",
                data.story_prompt
            )

            prompt = (
                f"{image_prompt}, "
                f"{data.art_style} style, "
                f"{data.tone} tone"
            )

            path = generate_image(prompt)

            image_paths.append(path)

        # Build layout
        layout = build_comic_layout(
            image_paths,
            full_story,
            outline
        )

        # Save PDF
        pdf_path = save_pdf(
            layout,
            data.story_prompt
        )

        return JSONResponse(
            {
                "outline": outline,
                "story": full_story,
                "layout": layout,
                "pdf_path": pdf_path
            }
        )

    except Exception as e:

        return JSONResponse(
            {
                "error": str(e)
            },
            status_code=500
        )


# --------------------------------------------------
# Export success page
# --------------------------------------------------

@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "request": request
        }
    )


# --------------------------------------------------
# Test image generation
# --------------------------------------------------

@router.post("/test-image")
async def test_image(
    prompt: str = Form(...)
):

    try:

        path = generate_image(prompt)

        return JSONResponse(
            {
                "image_path": path,
                "message": "Image generated"
            }
        )

    except Exception as e:

        return JSONResponse(
            {
                "error": str(e)
            },
            status_code=500
        )