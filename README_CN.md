> [!WARNING]\r\n> 本应用仍处于 Beta 阶段，功能与稳定性可能变动，请勿用于生产环境。\r\n\r\n本工具用于为 Etterna Rebirth 主题生成材质字体（纹理字体）。受 Texture-Font-Generator-2020-Squirrel 的发布版本启发，用 Python（PySide6 + QFluentWidgets）实现。

## 安装（Windows）
- 安装最新版 Python（建议 3.11+）。
- 克隆仓库并进入包目录：
  ```powershell
  git clone https://github.com/LarmaxHarkerX/Texture-Font-Factory.git
  cd Texture-Font-Factory\texture_font_factory
  ```
- 在包目录下创建并激活虚拟环境：
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install -U pip
  ```
- 安装依赖：
  ```powershell
  pip install -r requirements.txt
  ```
- 启动 GUI：
  ```powershell
  python main.py
  ```

## 功能
- 生成用于 Etterna Rebirth 的 PNG 字体纹理页与配置文件。
- 可选择系统字体或字体文件（.ttf/.otf），支持名称搜索。
- 实时预览生成的字形页面，带有进度提示。
- 可调节字号（px）、内边距以及每页字符数。
- 支持垂直模式与双倍分辨率输出。
- 可导出笔画模板（Stroke Templates）。
- 精细参数调节：基线/顶部偏移、居中偏移、左右重叠、字距扩展等。
- 选择输出目录并自动生成文件名。
- 失败时通过明确的消息进行提示。

## 项目结构
- `main.py`：唯一入口（直接运行）。
- `gui`：基于 QFluentWidgets 的界面层。
- `core`：字体处理与导出逻辑。
- `types`：模型与配置类型。

## 说明
- 启动时若看到 QFluentWidgets 的 Pro 信息提示，这是正常现象。
- 某些字体可能会出现警告（如 `'name' table stringOffset incorrect`），通常不影响使用。

## 致谢
- EtternaOnline：https://etternaonline.com/
- QFluentWidgets：https://qfluentwidgets.com/zh/
- Texture-Font-Generator-2020-Squirrel（TeamRizu）：https://github.com/TeamRizu/Texture-Font-Generator-2020-Squirrel
  - Releases：https://github.com/TeamRizu/Texture-Font-Generator-2020-Squirrel/releases


