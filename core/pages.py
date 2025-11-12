from __future__ import annotations

import math
import os
import logging
from typing import List, Optional, Callable, Tuple

from PIL import Image

from ..types.models import FontMetrics, PageLayout
from .fonts import loadFont, getFontCmapCodepoints, safeCharFromCodepoint
from .metrics import measureFontMetrics
from .glyphs import renderCharBitmap
from .layout import computeGlobalBoundsByMeasure, chooseColumns


logger = logging.getLogger(__name__)


def _filterCodepointsByPreset(cps: List[int], preset: Optional[str]) -> Tuple[List[int], str]:
    if not preset:
        return cps, "main"
    p = preset.lower().strip()
    if p == "numbers":
        kept: List[int] = []
        common_punct = {0x0025, 0x002E, 0x0021, 0x003A, 0x0078, 0x003F}
        for cp in cps:
            if 0x30 <= cp <= 0x39 or cp in common_punct:
                kept.append(cp)
        return kept, "numbers"
    if p == "plane2":
        import unicodedata
        prefixes = ("GREEK", "CYRILLIC", "ARMENIAN", "HEBREW", "ARROW", "COMBINING")
        kept2: List[int] = []
        for cp in cps:
            try:
                nm = unicodedata.name(chr(cp))
            except Exception:
                continue
            up = nm.upper()
            if up.startswith(prefixes) or " ARROW" in up or "COMBINING" in up:
                kept2.append(cp)
        return kept2, "plane-2"
    return cps, "main"


def generatePages(
    font_path: str,
    size_px: int,
    padding: int,
    save_dir: str,
    group_name: str = "main",
    codepoints: Optional[List[int]] = None,
    max_texture_size: int = 4096,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    vertical: bool = False,
    max_chars_per_page: Optional[int] = None,
    preset: Optional[str] = None,
    fixed_cols: Optional[int] = None,
    fixed_rows: Optional[int] = None,
    center_offset: int = 0,
    top_offset: int = 0,
    baseline_offset: int = 0,
    left_overlap: int = 0,
    right_overlap: int = 0,
    advance_extra: int = 0,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Tuple[FontMetrics, List[PageLayout]]:
    os.makedirs(save_dir, exist_ok=True)
    font = loadFont(font_path, size_px)
    cps = codepoints if codepoints is not None else getFontCmapCodepoints(font_path)
    cps, suggested_name = _filterCodepointsByPreset(cps, preset)
    if group_name == "main":
        group_name = suggested_name
    baseline, top, line_spacing = measureFontMetrics(font)
    ascent = baseline - top
    descent = line_spacing - baseline
    logger.info(f"gen: path={font_path}, size={size_px}, pad={padding}")
    logger.info(f"tune: center={center_offset}, top={top_offset}, baseline={baseline_offset}")
    left_overlap = int(max(0, left_overlap))
    right_overlap = int(max(0, right_overlap))
    advance_extra = int(max(0, advance_extra))
    max_w, max_h = computeGlobalBoundsByMeasure(font, cps)
    frame_w = math.ceil((max_w + padding) / 4.0) * 4
    frame_h = math.ceil((max_h + padding) / 4.0) * 4
    pages: List[PageLayout] = []
    total_chars = len(cps)
    col = fixed_cols if fixed_cols else min(chooseColumns(total_chars), max(1, max_texture_size // frame_w))
    max_rows_per_page = fixed_rows if fixed_rows else max(1, max_texture_size // frame_h)
    capacity = col * max_rows_per_page
    if max_chars_per_page is not None:
        capacity = max(1, int(max_chars_per_page))
    batches: List[List[int]] = []
    for i in range(0, total_chars, capacity):
        batches.append(cps[i:i + capacity])
    processed = 0
    for page_index, batch in enumerate(batches):
        if should_cancel and should_cancel():
            raise RuntimeError("Cancelled")
        page_name = group_name if len(batches) == 1 else f"{group_name} {page_index + 1}"
        num_cols = col
        num_rows = math.ceil(len(batch) / num_cols) if len(batch) else 1
        if fixed_rows:
            num_rows = fixed_rows
        page_img = Image.new("RGBA", (num_cols * frame_w, num_rows * frame_h), (0, 0, 0, 0))
        widths: List[int] = []
        lines: List[str] = []
        i = 0
        for r in range(num_rows):
            if should_cancel and should_cancel():
                raise RuntimeError("Cancelled")
            line_chars: List[str] = []
            for c in range(num_cols):
                if i >= len(batch):
                    break
                cp = batch[i]
                ch = safeCharFromCodepoint(cp)
                if not ch:
                    i += 1
                    continue
                cb = renderCharBitmap(font, ch)
                img = cb.image
                if vertical:
                    img = img.rotate(90, expand=True)
                adv_w = cb.width_adv if not vertical else cb.bbox_h
                widths.append(adv_w)
                line_chars.append(ch)
                w = cb.width_adv if not vertical else img.size[0]
                h = cb.bbox_h if not vertical else img.size[1]
                offset_x = int((frame_w / 2.0) - (w / 2.0))
                top_padding = int(padding / 2)
                offset_y = int(top_padding + int(center_offset) - int(baseline_offset))
                x = c * frame_w + offset_x
                y = r * frame_h + offset_y
                page_img.alpha_composite(img, (x, y))
                i += 1
            lines.append("".join(line_chars))
        pages.append(PageLayout(
            name=page_name,
            num_cols=num_cols,
            num_rows=num_rows,
            frame_w=frame_w,
            frame_h=frame_h,
            image=page_img,
            lines=lines,
            widths=widths,
        ))
        processed += len(batch)
        if progress_cb:
            try:
                progress_cb(processed, total_chars)
            except Exception:
                pass
        if should_cancel and should_cancel():
            raise RuntimeError("Cancelled")
    metrics = FontMetrics(
        ascent=baseline,
        descent=line_spacing - baseline,
        baseline=baseline + int(padding / 2) + int(center_offset) - int(baseline_offset),
        top=top + int(padding / 2) + int(center_offset) - int(top_offset),
        line_spacing=line_spacing,
        left_overlap=left_overlap,
        right_overlap=right_overlap,
        advance_extra=advance_extra,
    )
    return metrics, pages


def safeGeneratePages(
    font_path: str,
    size_px: int,
    padding: int,
    save_dir: str,
    group_name: str = "main",
    codepoints: Optional[List[int]] = None,
    max_texture_size: int = 4096,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    vertical: bool = False,
    max_chars_per_page: Optional[int] = None,
    preset: Optional[str] = None,
    fixed_cols: Optional[int] = None,
    fixed_rows: Optional[int] = None,
    center_offset: int = 0,
    top_offset: int = 0,
    baseline_offset: int = 0,
    left_overlap: int = 0,
    right_overlap: int = 0,
    advance_extra: int = 0,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Tuple[FontMetrics, List[PageLayout]]:
    try:
        logger.info(f"safe gen: {font_path}")
        if not font_path or not os.path.exists(font_path):
            raise ValueError(f"font not found: {font_path}")
        if size_px <= 0:
            raise ValueError(f"size must > 0: {size_px}")
        if padding < 0:
            raise ValueError(f"padding must >= 0: {padding}")
        center_offset = max(-100, min(100, center_offset))
        top_offset = max(-100, min(100, top_offset))
        baseline_offset = max(-100, min(100, baseline_offset))
        left_overlap = max(0, min(64, int(left_overlap)))
        right_overlap = max(0, min(64, int(right_overlap)))
        advance_extra = max(0, min(128, int(advance_extra)))
        return generatePages(
            font_path=font_path,
            size_px=size_px,
            padding=padding,
            save_dir=save_dir,
            group_name=group_name,
            codepoints=codepoints,
            max_texture_size=max_texture_size,
            progress_cb=progress_cb,
            vertical=vertical,
            max_chars_per_page=max_chars_per_page,
            preset=preset,
            fixed_cols=fixed_cols,
            fixed_rows=fixed_rows,
            center_offset=center_offset,
            top_offset=top_offset,
            baseline_offset=baseline_offset,
            left_overlap=left_overlap,
            right_overlap=right_overlap,
            advance_extra=advance_extra,
            should_cancel=should_cancel,
        )
    except Exception as e:
        if top_offset != 0 or baseline_offset != 0:
            try:
                return generatePages(
                    font_path=font_path,
                    size_px=size_px,
                    padding=padding,
                    save_dir=save_dir,
                    group_name=group_name,
                    codepoints=codepoints,
                    max_texture_size=max_texture_size,
                    progress_cb=progress_cb,
                    vertical=vertical,
                    max_chars_per_page=max_chars_per_page,
                    preset=preset,
                    fixed_cols=fixed_cols,
                    fixed_rows=fixed_rows,
                    center_offset=0,
                    top_offset=0,
                    baseline_offset=0,
                    left_overlap=left_overlap,
                    right_overlap=right_overlap,
                    advance_extra=advance_extra,
                    should_cancel=should_cancel,
                )
            except Exception:
                raise e
        else:
            raise e