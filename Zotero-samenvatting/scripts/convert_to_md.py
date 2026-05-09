#!/usr/bin/env python3
"""
convert_to_md.py — PDF naar markdown conversie.

Gebruikt tekst-extractie waar mogelijk; valt terug op OCR (Tesseract) voor
image-heavy PDFs.

Gebruik:
  python3 convert_to_md.py <pdf-pad> [output-map]

Geeft het pad naar het gegenereerde .md-bestand terug op stdout.
"""

import sys
import os
import shutil
from pathlib import Path

os.environ["ORT_DISABLE_GPU"] = "1"

import pymupdf
import pymupdf4llm
from PIL import Image
import io

# ── Tesseract: optioneel, niet beschikbaar op Windows zonder aparte installer ──

def _find_tesseract():
    """Zoek Tesseract-executable op; geef None terug als niet gevonden."""
    # Expliciete instelling via omgeving
    env_path = os.environ.get("TESSERACT_CMD")
    if env_path and Path(env_path).exists():
        return env_path

    # Standaard Windows-installatiepad
    win_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(win_default).exists():
        return win_default

    # PATH
    if shutil.which("tesseract"):
        return shutil.which("tesseract")

    return None


TESSERACT_CMD = _find_tesseract()

if TESSERACT_CMD:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    OCR_AVAILABLE = True
else:
    OCR_AVAILABLE = False
    print(
        "⚠️  Tesseract niet gevonden — image-heavy PDFs worden zonder OCR verwerkt.\n"
        "   Installeer Tesseract (https://github.com/UB-Mannheim/tesseract/wiki)\n"
        "   of stel TESSERACT_CMD in als omgevingsvariabele.",
        file=sys.stderr,
    )


def is_image_heavy(pdf_path, threshold=0.3):
    """True als meer dan threshold van de pagina's weinig tekst bevatten."""
    doc = pymupdf.open(str(pdf_path))
    if len(doc) == 0:
        return False
    image_pages = sum(1 for p in doc if len(p.get_text().strip()) < 50)
    return (image_pages / len(doc)) > threshold


def ocr_pdf_pages(pdf_path):
    """Converteer elke pagina via tekst-extractie; OCR waar beschikbaar."""
    doc = pymupdf.open(str(pdf_path))
    text_parts = []

    for page in doc:
        text = page.get_text().strip()
        if len(text) > 50:
            text_parts.append(text)
        elif OCR_AVAILABLE:
            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img, lang="nld+eng")
            text_parts.append(ocr_text)
        else:
            # Zonder OCR: extraheer wat er is (leeg of weinig)
            text_parts.append(text or "[pagina niet leesbaar zonder OCR]")

    return "\n\n---\n\n".join(text_parts)


def convert_smart(pdf_path, output_dir="./output"):
    """Converteer PDF naar markdown; geef pad naar .md-bestand terug."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem = Path(pdf_path).stem
    out_file = Path(output_dir) / f"{stem}.md"

    if is_image_heavy(pdf_path):
        method = "OCR" if OCR_AVAILABLE else "tekst-extractie (geen OCR)"
        print(f"{method}: {stem}", file=sys.stderr)
        md_text = ocr_pdf_pages(pdf_path)
    else:
        print(f"Extract: {stem}", file=sys.stderr)
        md_text = pymupdf4llm.to_markdown(
            str(pdf_path),
            write_images=True,
            image_path=output_dir,
            image_format="png",
            dpi=150,
        )

    out_file.write_text(md_text, encoding="utf-8")
    print(str(out_file))
    return str(out_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Gebruik: python3 convert_to_md.py <pdf-pad> [output-map]", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    convert_smart(pdf_path, output_dir)
