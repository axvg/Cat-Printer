#!/usr/bin/env python3
"""Print .txt .md .png .jpg .pdf on a Cat-Printer (MX10, 384 px wide).

Usage: uv run python imprimir.py FILE [--dry] [--energy 0.0-1.0]
"""
import argparse
import io
import os
import sys
import tempfile
import urllib.request
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

from printer import PrinterDriver
from printer_lib.models import Models

WIDTH = 384
FONTS = {
    "verdana": "C:/Windows/Fonts/verdana.ttf",
    "arial": "C:/Windows/Fonts/arial.ttf",
    "georgia": "C:/Windows/Fonts/georgia.ttf",
    "consola": "C:/Windows/Fonts/consola.ttf",
}
FONT_PATH = FONTS["verdana"]
FONT_SIZE = 20
MARGIN = 0
MODEL = "MX10"


def font(size=FONT_SIZE, name=None):
    try:
        return ImageFont.truetype(FONTS.get(name, FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def wrap(text, fnt, max_width):
    lines = []
    for raw in text.splitlines() or [""]:
        if not raw.strip():
            lines.append("")
            continue
        line = ""
        for word in raw.split(" "):
            trial = f"{line} {word}".strip()
            if fnt.getlength(trial) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def ascii_to_image(text):
    """Monospace, no wrapping, font scaled so the widest line fills the paper."""
    lines = text.splitlines() or [""]
    cols = max(len(line) for line in lines)
    size = 4
    while size < 64 and font(size + 1, "consola").getlength("M" * cols) <= WIDTH:
        size += 1
    fnt = font(size, "consola")
    step = size + 2
    img = Image.new("1", (WIDTH, step * len(lines) + 8), 1)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((0, 4 + i * step), line, font=fnt, fill=0)
    return [img]


def text_to_image(text, size=FONT_SIZE, name=None):
    fnt = font(size, name)
    lines = wrap(text, fnt, WIDTH - 2 * MARGIN)
    step = size + 6
    img = Image.new("1", (WIDTH, max(step * len(lines) + 2 * MARGIN, 40)), 1)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((MARGIN, MARGIN + i * step), line, font=fnt, fill=0)
    return [img]


def fit(img):
    img = img.convert("L")
    height = max(1, round(img.height * WIDTH / img.width))
    img = img.resize((WIDTH, height), Image.LANCZOS)
    return img.convert("1")  # Floyd-Steinberg dither, PIL default


def pdf_to_images(path):
    import pypdfium2

    pdf = pypdfium2.PdfDocument(path)
    return [fit(page.render(scale=2).to_pil()) for page in pdf]


CONTENT_TYPES = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
    "image/webp": ".webp", "image/bmp": ".bmp", "application/pdf": ".pdf",
    "text/plain": ".txt", "text/markdown": ".md",
}


def download(url):
    """Fetch url into a temp file named by its content type. Returns the path."""
    # many sites reject urllib's default User-Agent with HTTP 403
    request = urllib.request.Request(url, headers={"User-Agent": "imprimir.py"})
    with urllib.request.urlopen(request, timeout=30) as response:
        ext = (os.path.splitext(urlparse(url).path)[1].lower()
               or CONTENT_TYPES.get(response.headers.get_content_type(), ""))
        data = response.read()
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


def load(path, size=FONT_SIZE, name=None, ascii_art=False):
    if path.startswith(("http://", "https://")):
        path = download(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        return ascii_to_image(text) if ascii_art else text_to_image(text, size, name)
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        img = Image.open(path)
        img.seek(0)  # animated gif/webp: first frame
        return [fit(img)]
    if ext == ".pdf":
        return pdf_to_images(path)
    sys.exit(f"unsupported extension: {ext or path}")


def to_pbm(img):
    out = io.BytesIO()
    img.save(out, format="PPM")  # P4 for mode "1"
    return out.getvalue()


def stack(images):
    # ponytail: one tall bitmap instead of per-page PBM blocks
    total = sum(i.height for i in images) + 32 * (len(images) - 1)
    sheet = Image.new("1", (WIDTH, total), 1)
    y = 0
    for i, img in enumerate(images):
        sheet.paste(img, (0, y))
        y += img.height + (32 if i < len(images) - 1 else 0)
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="path or http(s) URL")
    ap.add_argument("--dry", action="store_true", help="print process only, no paper")
    ap.add_argument("--fake", action="store_true", help="no printer, no bluetooth")
    ap.add_argument("--size", type=int, default=FONT_SIZE, help="font size for txt/md")
    ap.add_argument("--quality", type=int, choices=[1, 2, 3, 4], default=1,
                    help="1 prints most evenly on this MX10")
    ap.add_argument("--speed", type=int, help="raw speed, overrides --quality")
    ap.add_argument("--ascii", action="store_true", help="ASCII art: no wrap, fit to width")
    ap.add_argument("--font", choices=sorted(FONTS), help="font for txt/md")
    ap.add_argument("--addr", help="MAC address, when several printers answer")
    ap.add_argument("--energy", type=float, default=0.5, help="0.0-1.0 thermal strength")
    args = ap.parse_args()

    sheet = stack(load(args.file, args.size, args.font, args.ascii))
    print(f"{args.file}: {sheet.width}x{sheet.height} px")

    printer = PrinterDriver()
    printer.dry_run = args.dry
    printer.energy = int(args.energy * 0xFFFF)
    printer.scan_time = 5.0
    printer.speed = args.speed or 4 * (args.quality + 5)  # same mapping as printer.py -q
    printer.fake = args.fake
    printer.model = Models[MODEL]
    # Windows needs a fresh scan before connecting, so --addr filters the scan
    # instead of connecting straight to the address
    printer.print(io.BytesIO(to_pbm(sheet)), mode="pbm", identifier=args.addr or MODEL)
    printer.unload()


def demo():
    assert wrap("a b c", font(), 10_000) == ["a b c"]
    assert len(wrap("word " * 200, font(), 100)) > 10
    img = text_to_image("hola")
    assert img[0].width == WIDTH
    assert to_pbm(img[0]).startswith(b"P4")
    assert stack([img[0], img[0]]).height == 2 * img[0].height + 32
    assert fit(Image.new("RGB", (100, 50))).size == (WIDTH, 192)
    art = ascii_to_image(("M" * 35) + chr(10) + "x")[0]
    assert art.width == WIDTH
    assert CONTENT_TYPES["image/png"] == ".png"
    assert font(1, "consola").getlength("M" * 35) < WIDTH  # fit loop has room to grow
    print("ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
