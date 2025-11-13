> Warning: This application is currently in beta. Features and stability may change; do not use in production.

A desktop tool to generate texture fonts for the Etterna Rebirth theme. Inspired by Texture-Font-Generator-2020-Squirrel releases and reimplemented in Python with PySide6 and QFluentWidgets.

## Installation (Windows)
- Install the latest Python (3.11+ recommended).
- Clone the repo and enter the package directory:
  ```powershell
  git clone https://github.com/LarmaxHarkerX/texture_font_factory.git
  cd texture_font_factory
  ```
- Create and activate a virtual environment:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install -U pip
  ```
- Install dependencies:
  ```powershell
  pip install -r requirements.txt
  ```
- Launch the GUI:
  ```powershell
  python main.py
  ```
## Run Again
- Activate the existing virtual environment:
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - CMD: `.\.venv\Scripts\activate.bat`
  - Git Bash: `source .venv/Scripts/activate`
- Launch the GUI: `python main.py`
- Exit the environment: `deactivate`

## Features
- Generate PNG texture pages and config files for Etterna Rebirth.
- Choose a system font or a font file (.ttf/.otf); search by name.
- Live preview of generated glyph pages with progress feedback.
- Controls for size (px), padding, and characters per page.
- Vertical mode toggle and double-resolution output.
- Stroke template export option.
- Fine-tuning: baseline/top offsets, center offset, left/right overlap, advance spacing.
- Automatic file naming with the selected save folder.
- Clear error notifications on failures.

## Project Layout
- `main.py`: single entry point (run directly).
- `gui`: UI layer built with QFluentWidgets.
- `core`: font processing and export logic.
- `types`: models and configuration types.

## Notes
- QFluentWidgets may print an informational tip about its Pro edition on startup; this is expected.
- Some fonts may emit warnings (e.g., `'name' table stringOffset incorrect`); these are harmless.

## Acknowledgements
- EtternaOnline: https://etternaonline.com/
- QFluentWidgets: https://qfluentwidgets.com/zh/
- Texture-Font-Generator-2020-Squirrel (TeamRizu): https://github.com/TeamRizu/Texture-Font-Generator-2020-Squirrel
  - Releases: https://github.com/TeamRizu/Texture-Font-Generator-2020-Squirrel/releases



