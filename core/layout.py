from __future__ import annotations

import math
from typing import List, Tuple
from PIL import ImageFont

from .fonts import safeCharFromCodepoint
from .glyphs import _measureCharSize


def computeGlobalBoundsByMeasure(font: ImageFont.FreeTypeFont, cps: List[int]) -> Tuple[int, int]:
    max_w = 0
    max_h = 0
    for cp in cps:
        ch = safeCharFromCodepoint(cp)
        if not ch:
            continue
        w, h = _measureCharSize(font, ch)
        max_w = max(max_w, w)
        max_h = max(max_h, h)
    return max_w, max_h


def chooseColumns(n_chars: int) -> int:
    if n_chars == 78:
        return 26
    if n_chars > 256:
        return 32
    if n_chars > 64:
        return 16
    if n_chars > 16:
        return 8
    return 4