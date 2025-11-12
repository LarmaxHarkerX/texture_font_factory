from __future__ import annotations

from typing import Tuple
from PIL import Image, ImageDraw, ImageFont

from ..types.models import CharBitmap


def _measureCharSize(font: ImageFont.FreeTypeFont, ch: str) -> Tuple[int, int]:
    try:
        bbox = font.getbbox(ch)
        if bbox:
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            return max(w, 1), max(h, 1)
    except Exception:
        pass
    try:
        w, h = font.getsize(ch)
        return max(w, 1), max(h, 1)
    except Exception:
        return 1, 1


def renderCharBitmap(font: ImageFont.FreeTypeFont, ch: str) -> CharBitmap:
    try:
        width_adv = int(round(font.getlength(ch)))
    except Exception:
        width_adv = font.getsize(ch)[0]
    est_w, est_h = _measureCharSize(font, ch)
    canvas_w = max(est_w + 4, width_adv)
    canvas_h = max(est_h + 4, font.size + 8)
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), ch, font=font, fill=(255, 255, 255, 255))
    bbox = img.getbbox()
    if bbox is None:
        cropped = Image.new("RGBA", (max(width_adv, 1), 1), (0, 0, 0, 0))
        bbox_w, bbox_h = cropped.size
    else:
        cropped = img.crop((0, 0, bbox[2], bbox[3]))
        bbox_w, bbox_h = cropped.size
    return CharBitmap(codepoint=ord(ch), image=cropped, width_adv=width_adv, bbox_w=bbox_w, bbox_h=bbox_h)