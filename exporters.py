import os
from datetime import datetime
from pathlib import Path
from fpdf import FPDF


def pdf_safe(text) -> str:
    """Make text safe for the built-in Helvetica font (Latin-1 only)."""
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u00a0": " ",
        "\u2022": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove markdown bold markers left over from the AI text
    text = text.replace("**", "")
    # Anything else the font can't draw (emoji etc.) becomes "?"
    return text.encode("latin-1", "replace").decode("latin-1")


class ComicPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'ComicCraft - AI Generated Comic', align='C',
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} - ComicCraft', align='C')


def _mc(pdf, h, text):
    """multi_cell that always returns to the left margin."""
    pdf.multi_cell(0, h, pdf_safe(text), new_x="LMARGIN", new_y="NEXT")


def save_pdf(layout, story_prompt="My Comic"):
    base_dir = Path(__file__).resolve().parent.parent
    export_dir = base_dir / "static" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    filepath = export_dir / filename

    pdf = ComicPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 28)
    pdf.ln(40)
    pdf.multi_cell(0, 15, pdf_safe(story_prompt[:100]), align='C',
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%B %d, %Y')}",
             align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Total Panels: {len(layout)}", align='C',
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 12)
    pdf.cell(0, 10, "Powered by Gemini + AI images", align='C',
             new_x="LMARGIN", new_y="NEXT")

    # Panels
    for panel in layout:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12,
                 pdf_safe(f"Panel {panel.get('panel')}: {panel.get('title', '')}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "I", 11)
        _mc(pdf, 7, panel.get('scene_description', ''))
        pdf.ln(3)

        img_path = panel.get('image_path', '')
        if img_path:
            full_img = Path(img_path)
            if not full_img.is_absolute():
                full_img = base_dir / img_path
            if full_img.exists():
                try:
                    pdf.image(str(full_img), x=20, w=170)
                    pdf.ln(5)
                except Exception as e:
                    pdf.cell(0, 10, pdf_safe(f"[Image error: {e}]"),
                             new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 11)
        _mc(pdf, 6, panel.get('text', ''))
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        _mc(pdf, 5, f"Art Prompt: {str(panel.get('image_prompt', ''))[:300]}")
        pdf.set_text_color(0, 0, 0)

    pdf.output(str(filepath))
    print(f"✅ PDF saved: {filepath}")
    return str(filepath)