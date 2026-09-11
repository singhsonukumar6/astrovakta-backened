"""Phase-1 social media pipeline: branded image cards and slideshow videos.

Generates share-ready media for queued social posts using the astrologer's
theme colors — no external services. Images are Pillow cards (1080x1080);
videos are short ffmpeg slideshows (square, h264, silent) built from the same
cards. Output is base64 so nothing touches disk.
"""
import base64
import io
import os
import subprocess
import tempfile
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]


def _font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _hex(color, fallback):
    c = str(color or fallback).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) if len(c) >= 6 else tuple(fallback)


def _card(site, headline, lines, footer):
    """Render one 1080x1080 branded card and return it as a PIL image."""
    theme = site.get("theme") or {}
    c1 = _hex(theme.get("primaryColor"), (79, 70, 229))
    c2 = _hex(theme.get("accentColor"), (217, 119, 6))
    name = site.get("name") or "AstroVakta"

    img = Image.new("RGB", (1080, 1080))
    # vertical gradient background
    for y in range(1080):
        t = y / 1079
        img.paste(tuple(round(a + (b - a) * t) for a, b in zip(c1, c2)), (0, y, 1080, y + 1))
    draw = ImageDraw.Draw(img)
    # inner border frame
    draw.rounded_rectangle([36, 36, 1044, 1044], radius=42, outline=(255, 255, 255), width=4)
    # translucent panel for text
    panel = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle([64, 64, 1016, 1016], radius=34, fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
    draw = ImageDraw.Draw(img)

    # headline (wrapped, up to 3 lines)
    y = 130
    for line in textwrap.wrap(headline, width=24)[:3]:
        draw.text((100, y), line, font=_font(64), fill=(255, 255, 255))
        y += 84
    # body lines
    y += 20
    for line in lines[:7]:
        for sub in textwrap.wrap(line, width=40) or [""]:
            draw.text((100, y), sub, font=_font(34), fill=(245, 243, 255))
            y += 46
        y += 8
    # footer brand
    draw.text((100, 950), f"— {name}", font=_font(38), fill=(255, 255, 255))
    draw.text((100, 1002), footer, font=_font(26), fill=(235, 232, 255))
    return img


def _b64(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, fmt)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def render_image(site, headline, lines, footer="Book your reading today"):
    return _b64(_card(site, headline, lines, footer))


def render_video(site, headline, lines, footer="Book your reading today", seconds=6):
    """Square silent slideshow: 3 branded cards with a slow zoom, h264 mp4."""
    cards = [
        _card(site, headline, lines[:3], footer),
        _card(site, headline, lines, footer),
        _card(site, headline, list(reversed(lines))[:3], footer),
    ]
    workdir = tempfile.mkdtemp(prefix="socialvid_")
    paths = []
    for i, card in enumerate(cards):
        p = os.path.join(workdir, f"f{i}.png")
        card.save(p)
        paths.append(p)
    out = os.path.join(workdir, "out.mp4")
    per = max(1.5, seconds / 3)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p in paths:
        cmd += ["-loop", "1", "-t", f"{per}", "-i", p]
    n = len(paths)
    cmd += ["-filter_complex",
            f"concat=n={n}:v=1:a=0,scale=720:720,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, timeout=90)
    with open(out, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    for p in paths + [out]:
        try:
            os.remove(p)
        except OSError:
            pass
    os.rmdir(workdir)
    return "data:video/mp4;base64," + data
