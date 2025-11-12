from __future__ import annotations

import os
from typing import List, Optional, Tuple
from PIL import Image

from ..types.models import FontMetrics, PageLayout
from .pages import safeGeneratePages
from .fonts import getFontCmapCodepoints


def writeIni(path: str, metrics: FontMetrics, pages: List[PageLayout]) -> None:
    out_lines: List[str] = []
    out_lines.append("[common]")
    out_lines.append(f"Baseline={metrics.baseline}")
    out_lines.append(f"Top={metrics.top}")
    out_lines.append(f"LineSpacing={metrics.line_spacing}")
    out_lines.append(f"DrawExtraPixelsLeft={metrics.left_overlap}")
    out_lines.append(f"DrawExtraPixelsRight={metrics.right_overlap}")
    out_lines.append(f"AdvanceExtraPixels={metrics.advance_extra}")
    out_lines.append("DefaultStrokeColor=#FFFFFF00")
    out_lines.append("")
    for page in pages:
        out_lines.append(f"[{page.name}]")
        for i, text in enumerate(page.lines):
            out_lines.append(f"Line {i}={text}")
        flattened = "".join(page.lines)
        widths = list(page.widths)
        if page.name.strip().lower() == "numbers":
            max_num_w = 0
            for idx, ch in enumerate(flattened):
                if ch.isdigit():
                    max_num_w = max(max_num_w, widths[idx])
            if max_num_w > 0:
                for idx, ch in enumerate(flattened):
                    if ch.isdigit():
                        widths[idx] = max_num_w
        for i, w in enumerate(widths):
            out_lines.append(f"{i}={w}")
        out_lines.append("")
    content = "\n".join(out_lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def savePagesAndIni(
    save_base_path: str,
    metrics: FontMetrics,
    pages: List[PageLayout],
    export_stroke_templates: bool = False,
    bitmap_append_suffix: str = "",
) -> str:
    ini_path = f"{save_base_path}.ini"
    for page in pages:
        suffix = bitmap_append_suffix or ""
        file_name = f"{save_base_path} [{page.name}] {page.num_cols}x{page.num_rows}{suffix}.png"
        page.image.save(file_name, format="PNG")
        if export_stroke_templates:
            stroke_name = f"{save_base_path} [{page.name}-stroke] {page.num_cols}x{page.num_rows}{suffix}.png"
            src = page.image.convert("L")
            rgba = Image.new("RGBA", page.image.size, (255, 255, 255, 0))
            rgba.putalpha(src)
            rgba.save(stroke_name, format="PNG")
    writeIni(ini_path, metrics, pages)
    return ini_path


def saveBitmapsOnly(
    save_base_path: str,
    pages: List[PageLayout],
    export_stroke_templates: bool = False,
    bitmap_append_suffix: str = "",
) -> None:
    for page in pages:
        suffix = bitmap_append_suffix or ""
        file_name = f"{save_base_path} [{page.name}] {page.num_cols}x{page.num_rows}{suffix}.png"
        page.image.save(file_name, format="PNG")
        if export_stroke_templates:
            stroke_name = f"{save_base_path} [{page.name}-stroke] {page.num_cols}x{page.num_rows}{suffix}.png"
            src = page.image.convert("L")
            rgba = Image.new("RGBA", page.image.size, (255, 255, 255, 0))
            rgba.putalpha(src)
            rgba.save(stroke_name, format="PNG")


def _makeBaseWithSize(base_path: str, new_size_px: int) -> str:
    base_dir = os.path.dirname(base_path)
    base_name = os.path.basename(base_path)
    import re
    m = re.search(r"^(.*)\s(\d+)px$", base_name)
    if m:
        prefix = m.group(1).rstrip()
        return os.path.join(base_dir, f"{prefix} {new_size_px}px")
    return os.path.join(base_dir, f"{base_name} {new_size_px}px")


def generateAndSave(
    font_path: str,
    size_px: int,
    padding: int,
    base_path: str,
    vertical: bool = False,
    max_chars_per_page: Optional[int] = None,
    export_stroke_templates: bool = False,
    preset: Optional[str] = None,
    write_redir_files: bool = True,
    redir_modes: Optional[dict] = None,
    center_offset: int = 0,
    top_offset: int = 0,
    baseline_offset: int = 0,
    left_overlap: int = 0,
    right_overlap: int = 0,
    advance_extra: int = 0,
) -> str:
    save_dir = os.path.dirname(base_path) or "."
    group_name = os.path.basename(base_path) or "main"
    cps = getFontCmapCodepoints(font_path)
    metrics, pages = safeGeneratePages(
        font_path=font_path,
        size_px=size_px,
        padding=padding,
        save_dir=save_dir,
        group_name=group_name,
        codepoints=cps,
        max_texture_size=4096,
        progress_cb=None,
        vertical=vertical,
        max_chars_per_page=max_chars_per_page,
        preset=preset,
        center_offset=center_offset,
        top_offset=top_offset,
        baseline_offset=baseline_offset,
        left_overlap=left_overlap,
        right_overlap=right_overlap,
        advance_extra=advance_extra,
    )
    ini_path = savePagesAndIni(base_path, metrics, pages, export_stroke_templates=export_stroke_templates)
    need_double = False
    if write_redir_files:
        modes = redir_modes or {}
        for k in ("Common Normal", "Common Large", "Menu Normal", "Menu Bold"):
            if str(modes.get(k, "default")).lower() == "2x":
                need_double = True
                break
    if need_double:
        fixed_cols = pages[0].num_cols if pages else None
        fixed_rows = pages[0].num_rows if pages else None
        _metrics2, pages2 = safeGeneratePages(
            font_path=font_path,
            size_px=size_px * 2,
            padding=padding,
            save_dir=save_dir,
            group_name=group_name,
            codepoints=cps,
            max_texture_size=4096,
            progress_cb=None,
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
        )
        doubled_base = _makeBaseWithSize(base_path, size_px * 2)
        savePagesAndIni(doubled_base, _metrics2, pages2, export_stroke_templates=export_stroke_templates)
    if write_redir_files:
        base_dir = os.path.dirname(base_path) or "."
        small_name = os.path.basename(_makeBaseWithSize(base_path, size_px))
        large_name = os.path.basename(_makeBaseWithSize(base_path, size_px * 2))
        def _writeRedir(filename: str, target_name: str):
            try:
                with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
                    f.write(target_name + "\n")
            except Exception:
                pass
        modes = redir_modes or {}
        def _target(for_key: str) -> str:
            m = str(modes.get(for_key, "default")).lower()
            return large_name if (m == "2x") else small_name
        _writeRedir("Common Normal.redir", _target("Common Normal"))
        _writeRedir("Common Large.redir", _target("Common Large"))
        _writeRedir("Menu Normal.redir", _target("Menu Normal"))
        _writeRedir("Menu Bold.redir", _target("Menu Bold"))
    return ini_path