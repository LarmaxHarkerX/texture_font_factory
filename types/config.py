from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Callable


@dataclass
class GenerateConfig:
    font_path: str
    size_px: int
    padding: int
    save_dir: str
    group_name: str = "main"
    codepoints: Optional[List[int]] = None
    max_texture_size: int = 4096
    vertical: bool = False
    max_chars_per_page: Optional[int] = None
    preset: Optional[str] = None
    fixed_cols: Optional[int] = None
    fixed_rows: Optional[int] = None
    center_offset: int = 0
    top_offset: int = 0
    baseline_offset: int = 0
    left_overlap: int = 0
    right_overlap: int = 0
    advance_extra: int = 0
    progress_cb: Optional[Callable[[int, int], None]] = None
    should_cancel: Optional[Callable[[], bool]] = None