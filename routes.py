from pathlib import Path

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.schemas import PromptRequest, ImageTestRequest

from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout
from app.services.exporters import save_pdf

router = APIRouter()

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def create_comic(data: PromptRequest):
    outline = generate_outline(
        data.prompt,
        data.character_name,
        data.setting,
        data.tone,
        data.art_style,
    )

    story = generate_story(
        outline,
        data.prompt,
        data.character_name,
        data.tone,
    )

    images = [
        generate_image(panel["image_prompt"], data.art_style)
        for panel in outline
    ]

    layout = build_comic_layout(outline, story, images)
    pdf_url = save_pdf(layout, data.prompt[:60])

    return layout, pdf_url


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_form(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form("Alex"),
    setting: str = Form("enchanted forest"),
    tone: str = Form("adventurous"),
    art_style: str = Form("comic book"),
):
    form_data = {
        "prompt": prompt,
        "character_name": character_name,
        "setting": setting,
        "tone": tone,
        "art_style": art_style,
    }

    try:
        data = PromptRequest(**form_data)
        layout, pdf_url = create_comic(data)

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_url": pdf_url,
                "prompt": data.prompt,
                "character_name": data.character_name,
            },
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": f"Comic generation failed: {str(exc)[:300]}",
                "form": form_data,
            },
            status_code=500,
        )


@router.post("/generate-comic/json")
async def generate_json(data: PromptRequest):
    try:
        layout, pdf_url = create_comic(data)

        return {
            "status": "success",
            "panels": layout,
            "pdf_url": pdf_url,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Comic generation failed: {str(exc)[:300]}",
        ) from exc


@router.post("/test-image")
async def test_image(data: ImageTestRequest):
    try:
        image_url = generate_image(data.prompt, data.art_style)

        return {
            "status": "success",
            "image_url": image_url,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(exc)[:300]}",
        ) from exc


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, file: str = ""):
    filename = Path(file).name

    exists = (
        bool(filename)
        and filename.endswith(".pdf")
        and (
            BASE_DIR / "static" / "exports" / filename
        ).is_file()
    )

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "download_url": (
                f"/static/exports/{filename}" if exists else ""
            ),
            "exists": exists,
        },
    )


@router.get("/download/{filename}")
async def download_pdf(filename: str):
    safe_name = Path(filename).name
    path = BASE_DIR / "static" / "exports" / safe_name

    if not safe_name.endswith(".pdf") or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="PDF not found",
        )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=safe_name,
    )