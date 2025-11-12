from __future__ import annotations

import os
import unicodedata
from typing import Dict, List, Optional, Callable

from PIL import ImageFont

try:
    import winreg
except Exception:
    winreg = None

try:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.ttCollection import TTCollection
except Exception:
    TTFont = None
    TTCollection = None


def loadFont(font_path: str, size_px: int) -> ImageFont.FreeTypeFont:
    index = None
    path = font_path
    if "|index=" in font_path:
        try:
            path, idx_str = font_path.split("|index=", 1)
            index = int(idx_str.strip())
        except Exception:
            path = font_path
            index = None
    try:
        if index is not None:
            return ImageFont.truetype(path, size_px, index=index)
    except Exception:
        pass
    return ImageFont.truetype(path, size_px)


def _canonicalizeFamily(name: str) -> str:
    s = name
    if "(" in s:
        s = s.split("(", 1)[0].strip()
    return s


def _candidateFontDirs() -> List[str]:
    dirs: List[str] = []
    windir = os.environ.get("WINDIR", r"C:\\Windows")
    dirs.append(os.path.join(windir, "Fonts"))
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        dirs.append(os.path.join(local_app, "Microsoft", "Windows", "Fonts"))
    return [d for d in dirs if os.path.isdir(d)]


def _getFamilyFromNameTable(tt: "TTFont") -> Optional[str]:
    name_tbl = tt.get("name")
    if not name_tbl:
        return None
    preferred = None
    fallback = None
    for rec in name_tbl.names:
        try:
            s = rec.toUnicode()
        except Exception:
            s = rec.string.decode(errors="ignore") if isinstance(rec.string, (bytes, bytearray)) else str(rec.string)
        if rec.nameID == 16 and s:
            preferred = s
            break
        if rec.nameID == 1 and s:
            fallback = s
    return preferred or fallback


def getFontCmapCodepoints(font_path: str) -> List[int]:
    tt: Optional[TTFont] = None
    try:
        if font_path.lower().endswith(".ttc") and TTCollection is not None:
            col = TTCollection(font_path)
            if col.fonts:
                tt = col.fonts[0]
        if tt is None and TTFont is not None:
            tt = TTFont(font_path, lazy=True)
        cmap = tt.getBestCmap() if tt else {}
        cps: List[int] = []
        for cp in sorted(cmap.keys()):
            try:
                cat = unicodedata.category(chr(cp))
            except Exception:
                continue
            if cat.startswith("C"):
                continue
            cps.append(cp)
        if hasattr(tt, "close") and callable(getattr(tt, "close")):
            try:
                tt.close()
            except Exception:
                pass
        return cps
    except Exception:
        return []


def safeCharFromCodepoint(cp: int) -> Optional[str]:
    try:
        return chr(cp)
    except Exception:
        return None


def enumerateFontVariantsWithProgress(
    progress_cb: Optional[Callable[[int, int], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Dict[str, Dict[str, str]]:
    variants: Dict[str, Dict[str, str]] = {}
    entries: List[tuple] = []
    if winreg is not None:
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Fonts"),
        ]
        for hive, subkey in keys:
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    i = 0
                    while True:
                        try:
                            name, value, _type = winreg.EnumValue(k, i)
                        except OSError:
                            break
                        i += 1
                        if not isinstance(value, str):
                            continue
                        p = value
                        if not os.path.isabs(p):
                            windir = os.environ.get("WINDIR", r"C:\\Windows")
                            p = os.path.join(windir, "Fonts", value)
                        if os.path.exists(p):
                            entries.append((name, p))
            except OSError:
                continue
    for name, path in entries:
        if should_cancel and should_cancel():
            break
        fam = _canonicalizeFamily(name)
        style = _normalizeSubfamily(name)
        variants.setdefault(fam, {})[style] = path
    files: List[str] = []
    for d in _candidateFontDirs():
        try:
            for fn in os.listdir(d):
                p = os.path.join(d, fn)
                if os.path.isfile(p) and os.path.splitext(fn)[1].lower() in {".ttf", ".otf", ".ttc"}:
                    files.append(p)
        except Exception:
            continue
    total = len(files)
    done = 0
    for p in files:
        if should_cancel and should_cancel():
            break
        try:
            if p.lower().endswith(".ttc") and TTCollection is not None:
                col = TTCollection(p)
                for idx, f in enumerate(col.fonts):
                    fam = _getFamilyFromNameTable(f)
                    subfam = None
                    nm = f.get("name")
                    if nm:
                        for rec in nm.names:
                            if rec.nameID == 2:
                                try:
                                    subfam = rec.toUnicode()
                                except Exception:
                                    subfam = rec.string.decode(errors="ignore") if isinstance(rec.string, (bytes, bytearray)) else str(rec.string)
                                break
                    if fam:
                        style = _normalizeSubfamily(subfam)
                        variants.setdefault(fam, {})[style] = f"{p}|index={idx}"
            elif TTFont is not None:
                tt = TTFont(p, lazy=True)
                fam = _getFamilyFromNameTable(tt)
                subfam = None
                nm = tt.get("name")
                if nm:
                    for rec in nm.names:
                        if rec.nameID == 2:
                            try:
                                subfam = rec.toUnicode()
                            except Exception:
                                subfam = rec.string.decode(errors="ignore") if isinstance(rec.string, (bytes, bytearray)) else str(rec.string)
                            break
                try:
                    tt.close()
                except Exception:
                    pass
                if fam:
                    style = _normalizeSubfamily(subfam)
                    variants.setdefault(fam, {})[style] = p
        except Exception:
            pass
        done += 1
        if progress_cb:
            try:
                progress_cb(done, total)
            except Exception:
                pass
    return variants


def _normalizeSubfamily(style_name: Optional[str]) -> str:
    s = (style_name or "").strip().lower()
    if "bold" in s and ("italic" in s or "oblique" in s):
        return "Bold Italic"
    if "bold" in s:
        return "Bold"
    if "italic" in s or "oblique" in s:
        return "Italic"
    return "Regular"