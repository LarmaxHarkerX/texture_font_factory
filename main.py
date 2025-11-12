from __future__ import annotations

import sys
from pathlib import Path

_parent = Path(__file__).resolve().parents[1]
_p = str(_parent)
if _p not in sys.path:
    sys.path.insert(0, _p)

from texture_font_factory.gui.main import main as gui_main


def main() -> int:
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
