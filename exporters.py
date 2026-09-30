from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from PIL import Image

from app.config import BASE_DIR

EXPORT_DIR = BASE_DIR / "static" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_text(value):
    """Replace unsupported punctuation for FPDF's core fonts."""
    value = str(value or "")

    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
        "…": "...",
        "•": "*",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value.encode(
        "latin-1", "replace"
    ).decode("latin-1")


def save_pdf(layout, title="ComicCraft"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    microseconds = datetime.now().microsecond

    filename = (
        f"comiccraft_{timestamp}_{microseconds:06d}.pdf"
    )

    output = EXPORT_DIR / filename

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)

    for panel in layout:
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 19)
        pdf.multi_cell(
            0,
            11,
            _safe_text(
                f"Panel {panel['panel_number']}: {panel['title']}"
            ),
        )

        pdf.ln(2)

        image_path = panel.get("image_path", "")
        img_path = None

        if image_path and not image_path.startswith("http"):
            relative_path = image_path.lstrip("/")
            img_path = (BASE_DIR / relative_path).resolve()

        if img_path and img_path.is_file():
            try:
                with Image.open(img_path) as image:
                    image_width, image_height = image.size

                max_width = 180
                max_height = 105

                scale = min(
                    max_width / image_width,
                    max_height / image_height,
                )

                rendered_width = image_width * scale
                rendered_height = image_height * scale

                pdf.image(
                    str(img_path),
                    x=(210 - rendered_width) / 2,
                    y=pdf.get_y(),
                    w=rendered_width,
                    h=rendered_height,
                )

                pdf.ln(rendered_height + 4)

            except Exception:
                # Continue exporting the text if an image is unreadable.
                pass

        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(
            0,
            6,
            _safe_text(panel.get("scene_description", "")),
        )

        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(
            0,
            6,
            _safe_text(panel.get("caption", "")),
        )

        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(
            0,
            6,
            _safe_text(panel.get("narration", "")),
        )

        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(
            0,
            6,
            _safe_text(panel.get("dialogue", "")),
        )

    pdf.output(str(output))

    return f"/static/exports/{filename}"