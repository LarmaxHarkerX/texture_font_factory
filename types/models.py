from __future__ import annotations

from dataclasses import dataclass
from typing import List
from PIL import Image


@dataclass
class FontMetrics:
    ascent: int
    descent: int
    baseline: int
    top: int
    line_spacing: int
    left_overlap: int
    right_overlap: int
    advance_extra: int


@dataclass
class CharBitmap:
    codepoint: int
    image: Image.Image
    width_adv: int
    bbox_w: int
    bbox_h: int


@dataclass
class PageLayout:
    name: str
    num_cols: int
    num_rows: int
    frame_w: int
    frame_h: int
    image: Image.Image
    lines: List[str]
    widths: List[int]