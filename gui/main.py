from __future__ import annotations

from .app import launch


def main() -> int:
    app = launch()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())