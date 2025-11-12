from __future__ import annotations

import logging
from typing import Tuple
from PIL import ImageFont

logger = logging.getLogger(__name__)


def measureFontMetrics(font: ImageFont.FreeTypeFont) -> Tuple[int, int, int]:
    ascent, descent = font.getmetrics()
    baseline = ascent
    top = 0
    line_spacing = ascent + descent
    logger.info(f"metrics: baseline={baseline}, top={top}, line_spacing={line_spacing}")
    return baseline, top, line_spacing