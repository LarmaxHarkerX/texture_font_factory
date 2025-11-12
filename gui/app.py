from __future__ import annotations
import os
import logging
from typing import Dict, Optional
logger = logging.getLogger(__name__)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QProgressBar, QListWidget, QListWidgetItem, QScrollArea
from qfluentwidgets import FluentWindow, ComboBox, LineEdit, SpinBox, PrimaryPushButton, InfoBar, setTheme, Theme, FluentIcon, NavigationItemPosition, ToolButton, CheckBox, setCustomStyleSheet
from PIL.ImageQt import ImageQt
from PIL import Image
from ..core.fonts import enumerateFontVariantsWithProgress as enumerate_font_variants_with_progress, loadFont as load_font
from ..core.metrics import measureFontMetrics as measure_font_metrics
from ..core.glyphs import renderCharBitmap as render_char_bitmap
from ..core.export import generateAndSave as generate_and_save

class GenerateWorker(QThread):
    finishedOk = Signal(str)
    failed = Signal(str)
    progress = Signal(int, int)

    def __init__(self, font_path: str, size: int, padding: int, base: str, vertical: bool, max_chars_per_page: int, export_stroke_templates: bool, preset: str | None, redir_modes: dict | None=None, center_offset: int=0, top_offset: int=0, baseline_offset: int=0, left_overlap: int=0, right_overlap: int=0, advance_extra: int=0):
        super().__init__()
        self.font_path = font_path
        self.size = size
        self.padding = padding
        self.base = base
        self.vertical = vertical
        self.max_chars_per_page = max_chars_per_page
        self.export_stroke_templates = export_stroke_templates
        self.preset = preset
        self.redir_modes = redir_modes or {}
        self.center_offset = center_offset
        self.top_offset = top_offset
        self.baseline_offset = baseline_offset
        self.left_overlap = left_overlap
        self.right_overlap = right_overlap
        self.advance_extra = advance_extra

    def run(self):
        try:
            save_dir = os.path.dirname(self.base) or '.'
            group_name = os.path.basename(self.base)

            def _cb(done: int, total: int):
                self.progress.emit(done, total)
            ini_path = generate_and_save(font_path=self.font_path, size_px=self.size, padding=self.padding, base_path=self.base, vertical=self.vertical, max_chars_per_page=self.max_chars_per_page, export_stroke_templates=self.export_stroke_templates, preset=self.preset, redir_modes=self.redir_modes, center_offset=self.center_offset, top_offset=self.top_offset, baseline_offset=self.baseline_offset, left_overlap=self.left_overlap, right_overlap=self.right_overlap, advance_extra=self.advance_extra)
            self.finishedOk.emit(ini_path)
        except Exception as e:
            self.failed.emit(str(e))

class PreviewPagesWorker(QThread):
    finishedOk = Signal(object, object)
    failed = Signal(str)
    progress = Signal(int, int)

    def __init__(self, font_path: str, size: int, padding: int, vertical: bool, max_chars_per_page: int, center_offset: int=0, top_offset: int=0, baseline_offset: int=0, left_overlap: int=0, right_overlap: int=0, advance_extra: int=0):
        super().__init__()
        self.font_path = font_path
        self.size = size
        self.padding = padding
        self.vertical = vertical
        self.max_chars_per_page = max_chars_per_page
        self.center_offset = center_offset
        self.top_offset = top_offset
        self.baseline_offset = baseline_offset
        self.left_overlap = left_overlap
        self.right_overlap = right_overlap
        self.advance_extra = advance_extra

    def run(self):
        try:

            def _cb(d, t):
                self.progress.emit(d, t)
            from ..core.pages import safeGeneratePages as safe_generate_pages
            metrics, pages = safe_generate_pages(font_path=self.font_path, size_px=self.size, padding=self.padding, save_dir=os.getcwd(), group_name='Preview', max_texture_size=4096, progress_cb=_cb, vertical=self.vertical, max_chars_per_page=self.max_chars_per_page, center_offset=self.center_offset, top_offset=self.top_offset, baseline_offset=self.baseline_offset, left_overlap=self.left_overlap, right_overlap=self.right_overlap, advance_extra=self.advance_extra, should_cancel=lambda: self.isInterruptionRequested())
            self.finishedOk.emit(metrics, pages)
        except Exception as e:
            self.failed.emit(str(e))

class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        setTheme(Theme.LIGHT)
        self.lang = 'en'
        self.i18n = {'en': {'main_title': 'TEXTURE FONT FACTORY', 'main_subtitle': 'A tool to generate texture fonts for the Etterna Rebirth theme.', 'app_title': 'TEXTURE FONT FACTORY — Python', 'select_font_label': 'Select Font:', 'choose_font_button': 'Choose Font…', 'selected_none': '(Not selected)', 'save_placeholder': 'Choose output folder (auto file name)', 'choose_save_path_button': 'Choose Output Folder…', 'generate_button': 'Generate Font and Config', 'err_select_font': 'Please select a font first', 'err_select_save': 'Please choose a save location first', 'gen_success_title': 'Generation Succeeded', 'gen_success_saved': 'Saved: {path}', 'gen_failed_title': 'Generation Failed', 'vertical': 'Vertical', 'style': 'Style:', 'search_placeholder': 'Search fonts…', 'dlg_title_choose_font': 'Choose Font', 'dlg_loading_fonts': 'Loading system fonts…', 'dlg_refresh_tip': 'Refresh font list', 'dlg_choose_file_tip': 'Choose font file', 'dlg_size_px': 'Size (px):', 'dlg_padding': 'Padding:', 'dlg_chars_per_page': 'Chars per page:', 'dlg_select_font_tip': 'Please choose a system font:', 'dlg_ok': 'OK', 'dlg_cancel': 'Cancel', 'dlg_preview_generating': 'Generating preview…', 'dlg_preview_complete': 'Preview complete', 'dlg_preview_failed_prefix': 'Preview failed: ', 'dlg_no_font_selected_title': 'No font selected', 'dlg_no_font_selected_content': 'Please choose a system font', 'dlg_choose_file_title': 'Choose Font File', 'dlg_preview_group': 'Preview', 'toggle_theme_tip': 'Toggle light/dark', 'nav_text_icon': 'Generate', 'nav_generate': 'Generate', 'gen_generating': 'Generating…', 'gen_generating_pct': 'Generating… {pct}%', 'opt_export_stroke': 'Export Stroke Templates', 'opt_double_res': 'Double Resolution', 'opt_preset_label': 'Preset:', 'preset_none': 'None', 'preset_numbers': 'Numbers', 'preset_plane2': 'Plane 2', 'redir_default': 'default', 'redir_2x': '2x', 'redir_common_normal': 'Common Normal', 'redir_common_large': 'Common Large', 'redir_menu_normal': 'Menu Normal', 'redir_menu_bold': 'Menu Bold'}}
        self.setWindowTitle(self._t('app_title'))
        logging.getLogger('fontTools').setLevel(logging.ERROR)
        logging.getLogger('fontTools.ttLib').setLevel(logging.ERROR)
        self.selectedFamilyLabel = QLabel(self._t('selected_none'))
        try:
            self.navigationInterface.setDefaultRouteKey(btn.routeKey())
        except Exception:
            pass
        self.system_fonts: Dict[str, str] = {}
        self.selected_font_path: str | None = None
        self.fonts_loaded: bool = False
        self.size_px: int = 32
        self.padding_px: int = 2
        self.vertical_mode: bool = False
        self.max_chars_per_page: int = 100
        self.export_stroke_templates: bool = False
        self.preset_mode: str | None = None
        self._init_text_icon_nav()

    class FontsWorker(QThread):
        finishedOk = Signal(dict)
        failed = Signal(str)
        progress = Signal(int, int)

        def run(self):
            try:

                def _cb(d, t):
                    self.progress.emit(d, t)
                fonts = enumerate_font_variants_with_progress(_cb)
                self.finishedOk.emit(fonts)
            except Exception as e:
                self.failed.emit(str(e))

    def _open_system_font_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self._t('dlg_title_choose_font'))
        dlg.setSizeGripEnabled(True)
        dlg.resize(1000, 640)
        root = QVBoxLayout(dlg)
        dlg_light_qss = 'QDialog{background-color: rgb(249,249,249);}QDialog QLabel{color: black;}QDialog LineEdit{color: black;}QDialog ComboBox{color: black;}QDialog CheckBox{color: black;}'
        setCustomStyleSheet(dlg, dlg_light_qss, dlg_light_qss)
        top = QHBoxLayout()
        tip = QLabel(self._t('dlg_loading_fonts'))
        refreshBtn = ToolButton(FluentIcon.SYNC, dlg)
        refreshBtn.setToolTip(self._t('dlg_refresh_tip'))
        fileBtn = ToolButton(FluentIcon.DOCUMENT, dlg)
        fileBtn.setToolTip(self._t('dlg_choose_file_tip'))
        top.addWidget(tip)
        top.addStretch(1)
        top.addWidget(refreshBtn)
        top.addWidget(fileBtn)
        root.addLayout(top)
        bar = QProgressBar(dlg)
        bar.setRange(0, 100)
        bar.setValue(0)
        root.addWidget(bar)
        mainArea = QHBoxLayout()
        leftBox = QVBoxLayout()
        leftCtrlRow = QHBoxLayout()
        leftCtrlRow.setSpacing(6)
        verticalChk = CheckBox(self._t('vertical'), dlg)
        verticalChk.setChecked(self.vertical_mode)
        leftCtrlRow.addWidget(verticalChk)
        styleLabel = QLabel(self._t('style'), dlg)
        leftCtrlRow.addWidget(styleLabel)
        styleCombo = ComboBox(dlg)
        styleCombo.addItems(['Regular', 'Bold', 'Italic', 'Bold Italic'])
        styleCombo.setFixedWidth(160)
        leftCtrlRow.addWidget(styleCombo)
        leftCtrlRow.addStretch(1)
        leftBox.addLayout(leftCtrlRow)
        searchEdit = LineEdit(dlg)
        searchEdit.setPlaceholderText(self._t('search_placeholder'))
        searchEdit.setClearButtonEnabled(True)
        leftBox.addWidget(searchEdit)
        listw = QListWidget(dlg)
        listw.setVisible(False)
        listw.setMinimumSize(QSize(320, 420))
        leftBox.addWidget(listw, 1)
        mainArea.addLayout(leftBox, 1)
        previewPanel = QVBoxLayout()
        ctrlRow = QHBoxLayout()
        ctrlRow.addWidget(QLabel(self._t('dlg_size_px'), dlg))
        sizeSpin = SpinBox(dlg)
        sizeSpin.setRange(8, 256)
        sizeSpin.setValue(self.size_px)
        ctrlRow.addWidget(sizeSpin)
        ctrlRow.addWidget(QLabel(self._t('dlg_padding'), dlg))
        paddingSpin = SpinBox(dlg)
        paddingSpin.setRange(0, 16)
        paddingSpin.setValue(self.padding_px)
        ctrlRow.addWidget(paddingSpin)
        ctrlRow.addWidget(QLabel(self._t('dlg_chars_per_page'), dlg))
        perPageSpin = SpinBox(dlg)
        perPageSpin.setRange(10, 2048)
        perPageSpin.setValue(self.max_chars_per_page)
        ctrlRow.addWidget(perPageSpin)
        ctrlRow.addStretch(1)
        prevBtn = ToolButton(FluentIcon.LEFT_ARROW, dlg)
        nextBtn = ToolButton(FluentIcon.RIGHT_ARROW, dlg)
        pageLabel = QLabel('0/0', dlg)
        ctrlRow.addWidget(prevBtn)
        ctrlRow.addWidget(pageLabel)
        ctrlRow.addWidget(nextBtn)
        previewPanel.addLayout(ctrlRow)
        previewLabel = QLabel(dlg)
        previewLabel.setAlignment(Qt.AlignCenter)
        scroll = QScrollArea(dlg)
        scroll.setWidget(previewLabel)
        scroll.setWidgetResizable(True)
        previewPanel.addWidget(scroll, 1)
        mainArea.addLayout(previewPanel, 2)
        root.addLayout(mainArea)
        btns = QHBoxLayout()
        okBtn = PrimaryPushButton(self._t('dlg_ok'), dlg)
        okBtn.setEnabled(False)
        cancelBtn = PrimaryPushButton(self._t('dlg_cancel'), dlg)
        btns.addWidget(okBtn)
        btns.addWidget(cancelBtn)
        root.addLayout(btns)
        chosen_path = {'path': None, 'family': None}

        def render_list(filter_text: str=''):
            listw.clear()
            ft = (filter_text or '').strip().lower()
            fams = sorted((getattr(self, 'system_fonts', {}) or {}).keys())
            if ft:
                fams = [f for f in fams if ft in f.lower()]
            for fam in fams:
                path = getattr(self, 'system_fonts', {}).get(fam)
                item = QListWidgetItem(fam)
                item.setData(Qt.UserRole, path)
                listw.addItem(item)
        searchEdit.textChanged.connect(lambda t: render_list(t))
        worker = None

        def on_list_clicked():
            item = listw.currentItem()
            if not item:
                return
            fam = item.text()
            chosen_path['family'] = fam

            def _update_styles_for_family(f: str):
                styles = list((getattr(self, 'font_variants', {}).get(f) or {}).keys())
                if not styles:
                    styles = ['Regular']
                styleCombo.blockSignals(True)
                styleCombo.clear()
                for s in ['Regular', 'Bold', 'Italic', 'Bold Italic']:
                    if s in styles:
                        styleCombo.addItem(s)
                for s in styles:
                    if styleCombo.findText(s) < 0:
                        styleCombo.addItem(s)
                styleCombo.blockSignals(False)
                if styleCombo.count() > 0 and styleCombo.findText(styleCombo.currentText()) < 0:
                    styleCombo.setCurrentIndex(0)
            _update_styles_for_family(fam)
            p = resolve_path_for_style(fam, styleCombo.currentText())
            chosen_path['path'] = p or item.data(Qt.UserRole)
            verticalChk.setChecked(chosen_path['family'].startswith('@'))
            schedule_preview()
        listw.itemSelectionChanged.connect(on_list_clicked)

        def on_ok():
            if chosen_path['path']:
                self.selected_font_path = chosen_path['path']
                self.selectedFamilyLabel.setText(chosen_path['family'])
                self.vertical_mode = bool(verticalChk.isChecked())
                self.max_chars_per_page = int(perPageSpin.value())
                self.size_px = int(sizeSpin.value())
                self.padding_px = int(paddingSpin.value())
                cancel_preview_worker()
                self._update_gen_enabled()
                dlg.accept()
            else:
                InfoBar.warning(title=self._t('dlg_no_font_selected_title'), content=self._t('dlg_no_font_selected_content'), parent=self, duration=4000)
        okBtn.clicked.connect(on_ok)
        cancelBtn.clicked.connect(lambda: (cancel_font_worker(), cancel_preview_worker(), dlg.reject()))

        def start_load():
            nonlocal worker
            tip.setText(self._t('dlg_loading_fonts'))
            listw.setVisible(False)
            listw.clear()
            bar.setValue(0)
            okBtn.setEnabled(False)
            refreshBtn.setEnabled(False)
            worker = MainWindow.FontsWorker()

            def on_progress(d, t):
                pct = int(d * 100 / max(t, 1))
                bar.setValue(pct)

            def on_loaded(fonts: dict):
                tip.setText(self._t('dlg_select_font_tip'))
                listw.setVisible(True)
                listw.clear()
                if fonts and isinstance(next(iter(fonts.values())), dict):
                    self.font_variants = fonts
                    self.system_fonts = {fam: vals.get('Regular') or next(iter(vals.values())) for fam, vals in fonts.items()}
                else:
                    self.font_variants = {}
                    self.system_fonts = fonts
                render_list(searchEdit.text())
                okBtn.setEnabled(True)
                refreshBtn.setEnabled(True)

            def on_failed(msg: str):
                tip.setText(self._t('dlg_preview_failed_prefix') + msg)
                okBtn.setEnabled(False)
                refreshBtn.setEnabled(True)
            worker.progress.connect(on_progress)
            worker.finishedOk.connect(on_loaded)
            worker.failed.connect(on_failed)
            worker.start()
        refreshBtn.clicked.connect(start_load)

        def on_style_changed(_):
            item = listw.currentItem()
            if not item:
                return
            fam = item.text()
            p = resolve_path_for_style(fam, styleCombo.currentText())
            if p:
                chosen_path['path'] = p
                schedule_preview()
        styleCombo.currentTextChanged.connect(on_style_changed)

        def on_pick_file():
            path, _ = QFileDialog.getOpenFileName(dlg, self._t('dlg_choose_file_title'), '', 'Font Files (*.ttf *.otf *.ttc)')
            if path:
                chosen_path['path'] = path
                chosen_path['family'] = os.path.basename(path)
                self.selectedFamilyLabel.setText(chosen_path['family'])
                schedule_preview()
        fileBtn.clicked.connect(on_pick_file)
        preview_worker = {'worker': None}
        preview_state = {'cancelled': False}
        current_pages = {'pix': [], 'index': 0}

        def resolve_path_for_style(fam: str, style: str) -> Optional[str]:
            variants = getattr(self, 'font_variants', {}).get(fam) or {}
            if style in variants:
                return variants[style]
            if 'Regular' in variants:
                return variants['Regular']
            sys_fonts = getattr(self, 'system_fonts', {})
            if fam in sys_fonts:
                return sys_fonts[fam]
            return next(iter(variants.values()), None)

        def cancel_preview_worker():
            w = preview_worker['worker']
            if w is not None:
                preview_state['cancelled'] = True
                try:
                    if hasattr(w, 'requestInterruption'):
                        w.requestInterruption()
                except Exception:
                    pass
                if w.isRunning():
                    try:
                        w.wait()
                    except Exception:
                        pass
                preview_worker['worker'] = None

        def update_page_view():
            if not current_pages['pix']:
                previewLabel.clear()
                pageLabel.setText('0/0')
                return
            idx = max(0, min(current_pages['index'], len(current_pages['pix']) - 1))
            previewLabel.setPixmap(current_pages['pix'][idx])
            pageLabel.setText(f"{idx + 1}/{len(current_pages['pix'])}")
        debounce = QTimer(dlg)
        debounce.setSingleShot(True)
        debounce.setInterval(250)

        def schedule_preview():
            debounce.stop()
            debounce.start()

        def start_preview_now():
            if not chosen_path['path']:
                return
            tip.setText(self._t('dlg_preview_generating'))
            bar.setValue(0)
            okBtn.setEnabled(False)
            previewLabel.clear()
            current_pages['pix'] = []
            current_pages['index'] = 0
            cancel_preview_worker()
            preview_state['cancelled'] = False
            center_offset = int(getattr(self, 'applied_center_offset', 0))
            top_offset = int(getattr(self, 'applied_top_offset', 0))
            baseline_offset = int(getattr(self, 'applied_baseline_offset', 0))
            left_applied = int(getattr(self, 'applied_left_overlap', 0))
            right_applied = int(getattr(self, 'applied_right_overlap', 0))
            adv_applied = int(getattr(self, 'applied_advance_extra', 0))
            w = PreviewPagesWorker(font_path=chosen_path['path'], size=int(sizeSpin.value()), padding=int(paddingSpin.value()), vertical=bool(verticalChk.isChecked()), max_chars_per_page=int(perPageSpin.value()), center_offset=center_offset, top_offset=top_offset, baseline_offset=baseline_offset, left_overlap=left_applied, right_overlap=right_applied, advance_extra=adv_applied)

            def on_p(d, t):
                bar.setValue(int(d * 100 / max(t, 1)))

            def on_ok(metrics, pages):
                tip.setText(self._t('dlg_preview_complete'))
                okBtn.setEnabled(True)
                pix = []
                for p in pages:
                    bg = Image.new('RGBA', p.image.size, (40, 40, 40, 255))
                    bg.alpha_composite(p.image)
                    qimg = ImageQt(bg).copy()
                    pix.append(QPixmap.fromImage(qimg))
                current_pages['pix'] = pix
                current_pages['index'] = 0
                update_page_view()

            def on_fail(msg: str):
                if preview_state.get('cancelled'):
                    return
                tip.setText(self._t('dlg_preview_failed_prefix') + msg)
                okBtn.setEnabled(False)
            w.progress.connect(on_p)
            w.finishedOk.connect(on_ok)
            w.failed.connect(on_fail)
            preview_worker['worker'] = w
            w.start()
        debounce.timeout.connect(start_preview_now)

        def go_prev():
            if current_pages['pix']:
                current_pages['index'] = max(0, current_pages['index'] - 1)
                update_page_view()

        def go_next():
            if current_pages['pix']:
                current_pages['index'] = min(len(current_pages['pix']) - 1, current_pages['index'] + 1)
                update_page_view()
        prevBtn.clicked.connect(go_prev)
        nextBtn.clicked.connect(go_next)
        perPageSpin.valueChanged.connect(lambda _: schedule_preview())
        verticalChk.toggled.connect(lambda _: schedule_preview())
        sizeSpin.valueChanged.connect(lambda _: schedule_preview())
        paddingSpin.valueChanged.connect(lambda _: schedule_preview())
        cancelBtn.clicked.connect(lambda: (cancel_font_worker(), cancel_preview_worker(), dlg.reject()))
        dlg.finished.connect(lambda _: cancel_preview_worker())
        start_load()
        dlg.exec()

    def _choose_save_path(self):
        folder = QFileDialog.getExistingDirectory(self, self._t('choose_save_path_button'), '')
        if folder:
            self.saveEdit.setText(folder)
            self._update_gen_enabled()

    def _update_gen_enabled(self):
        base = self.saveEdit.text().strip()
        can = bool(self.selected_font_path) and bool(base)
        self.genBtn.setEnabled(can)

    def _generate(self):
        if not self.selected_font_path:
            InfoBar.error(self._t('err_select_font'), parent=self)
            return
        base_input = self.saveEdit.text().strip()
        if not base_input:
            InfoBar.error(self._t('err_select_save'), parent=self)
            return
        size = int(self.size_px)
        padding = int(self.padding_px)

        def _sanitize_name(s: str) -> str:
            return ''.join((c if c not in '<>:"/\\|?*' else ' ' for c in s)).strip()
        if os.path.isdir(base_input):
            family = self.selectedFamilyLabel.text().strip() or 'Font'
            if family.startswith('@'):
                family = family[1:]
            base_name = f'_{_sanitize_name(family)} {size}px'
            base = os.path.join(base_input, base_name)
        else:
            base = base_input
        save_dir = os.path.dirname(base) or '.'
        group_name = os.path.basename(base)
        self.genBtn.setEnabled(False)
        self.genBtn.setText(self._t('gen_generating'))
        self.export_stroke_templates = bool(self.strokeChk.isChecked())
        self.preset_mode = None
        center_applied = int(getattr(self, 'applied_center_offset', 0))
        top_applied = int(getattr(self, 'applied_top_offset', 0))
        baseline_applied = int(getattr(self, 'applied_baseline_offset', 0))
        left_applied = int(getattr(self, 'applied_left_overlap', 0))
        right_applied = int(getattr(self, 'applied_right_overlap', 0))
        adv_applied = int(getattr(self, 'applied_advance_extra', 0))
        redir_modes_main = {'Common Normal': 'default', 'Common Large': 'default', 'Menu Normal': 'default', 'Menu Bold': 'default'}
        self.worker = GenerateWorker(self.selected_font_path, size, padding, base, self.vertical_mode, self.max_chars_per_page, self.export_stroke_templates, self.preset_mode, redir_modes=redir_modes_main, center_offset=center_applied, top_offset=top_applied, baseline_offset=baseline_applied, left_overlap=left_applied, right_overlap=right_applied, advance_extra=adv_applied)
        self.worker.progress.connect(lambda d, t: self._on_progress(d, t))
        self.worker.finishedOk.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, done: int, total: int):
        pct = int(done * 100 / max(total, 1))
        self.genBtn.setText(self._t('gen_generating_pct').format(pct=pct))

    def _on_finished(self, ini_path: str):
        InfoBar.success(title=self._t('gen_success_title'), content=self._t('gen_success_saved').format(path=ini_path), parent=self, duration=6000)
        self.genBtn.setEnabled(True)
        self.genBtn.setText(self._t('generate_button'))
        self.worker = None

    def _on_failed(self, msg: str):
        InfoBar.error(title=self._t('gen_failed_title'), content=msg, parent=self, duration=8000)
        self.genBtn.setEnabled(True)
        self.genBtn.setText(self._t('generate_button'))
        self.worker = None

    def _t(self, key: str) -> str:
        m = self.i18n.get(self.lang, {})
        return m.get(key, key)

    def _init_text_icon_nav(self):
        self.textIconPage = QWidget(self)
        self.textIconPage.setObjectName('textIconInterface')
        root = QVBoxLayout(self.textIconPage)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        mainArea = QHBoxLayout()
        leftBox = QVBoxLayout()
        topCtrlRow = QHBoxLayout()
        topCtrlRow.setSpacing(6)
        self.textVerticalChk = CheckBox(self._t('vertical'), self.textIconPage)
        self.textVerticalChk.setChecked(bool(getattr(self, 'vertical_mode', False)))
        topCtrlRow.addWidget(self.textVerticalChk)
        styleLabel2 = QLabel(self._t('style'), self.textIconPage)
        topCtrlRow.addWidget(styleLabel2)
        self.textStyleCombo = ComboBox(self.textIconPage)
        self.textStyleCombo.addItems(['Regular', 'Bold', 'Italic', 'Bold Italic'])
        self.textStyleCombo.setFixedWidth(160)
        topCtrlRow.addWidget(self.textStyleCombo)
        topCtrlRow.addStretch(1)
        leftBox.addLayout(topCtrlRow)
        searchRow = QHBoxLayout()
        searchRow.setSpacing(6)
        self.textSearchEdit = LineEdit(self.textIconPage)
        self.textSearchEdit.setPlaceholderText(self._t('search_placeholder'))
        self.textSearchEdit.setClearButtonEnabled(True)
        searchRow.addWidget(self.textSearchEdit, 1)
        self.textRefreshBtn = ToolButton(FluentIcon.SYNC, self.textIconPage)
        self.textRefreshBtn.setToolTip(self._t('dlg_refresh_tip'))
        searchRow.addWidget(self.textRefreshBtn)
        self.textFileBtn = ToolButton(FluentIcon.DOCUMENT, self.textIconPage)
        self.textFileBtn.setToolTip(self._t('dlg_choose_file_tip'))
        searchRow.addWidget(self.textFileBtn)
        leftBox.addLayout(searchRow)
        self.textListWidget = QListWidget(self.textIconPage)
        self.textListWidget.setVisible(False)
        self.textListWidget.setMinimumSize(QSize(320, 420))
        leftBox.addWidget(self.textListWidget, 1)
        self.fontsProgress = QProgressBar(self.textIconPage)
        self.fontsProgress.setVisible(False)
        self.fontsProgress.setTextVisible(False)
        leftBox.addWidget(self.fontsProgress)
        mainArea.addLayout(leftBox, 1)
        previewPanel = QVBoxLayout()
        ctrlRow = QHBoxLayout()
        ctrlRow.addWidget(QLabel(self._t('dlg_size_px'), self.textIconPage))
        self.textSizeSpin = SpinBox(self.textIconPage)
        self.textSizeSpin.setRange(8, 256)
        self.textSizeSpin.setValue(self.size_px)
        ctrlRow.addWidget(self.textSizeSpin)
        ctrlRow.addWidget(QLabel(self._t('dlg_padding'), self.textIconPage))
        self.textPaddingSpin = SpinBox(self.textIconPage)
        self.textPaddingSpin.setRange(0, 16)
        self.textPaddingSpin.setValue(self.padding_px)
        ctrlRow.addWidget(self.textPaddingSpin)
        ctrlRow.addWidget(QLabel(self._t('dlg_chars_per_page'), self.textIconPage))
        self.textPerPageSpin = SpinBox(self.textIconPage)
        self.textPerPageSpin.setRange(10, 2048)
        self.textPerPageSpin.setValue(int(getattr(self, 'max_chars_per_page', 100)))
        ctrlRow.addWidget(self.textPerPageSpin)
        ctrlRow.addStretch(1)
        self.textPrevBtn = ToolButton(FluentIcon.LEFT_ARROW, self.textIconPage)
        self.textNextBtn = ToolButton(FluentIcon.RIGHT_ARROW, self.textIconPage)
        self.textPageLabel = QLabel('0/0', self.textIconPage)
        ctrlRow.addWidget(self.textPrevBtn)
        ctrlRow.addWidget(self.textPageLabel)
        ctrlRow.addWidget(self.textNextBtn)
        previewPanel.addLayout(ctrlRow)
        self.textPreviewLabel = QLabel(self.textIconPage)
        self.textPreviewLabel.setAlignment(Qt.AlignCenter)
        self.textScroll = QScrollArea(self.textIconPage)
        self.textScroll.setWidget(self.textPreviewLabel)
        self.textScroll.setWidgetResizable(True)
        previewPanel.addWidget(self.textScroll, 1)
        self._init_simple_fine_tune_controls(previewPanel)
        self.previewProgress = QProgressBar(self.textIconPage)
        self.previewProgress.setVisible(False)
        self.previewProgress.setTextVisible(False)
        previewPanel.addWidget(self.previewProgress)
        mainArea.addLayout(previewPanel, 2)
        root.addLayout(mainArea)
        saveRow2 = QHBoxLayout()
        self.textSaveEdit = LineEdit(self.textIconPage)
        self.textSaveEdit.setPlaceholderText(self._t('save_placeholder'))
        saveRow2.addWidget(self.textSaveEdit)
        self.textSaveBtn = PrimaryPushButton(self._t('choose_save_path_button'), self.textIconPage)
        saveRow2.addWidget(self.textSaveBtn)
        root.addLayout(saveRow2)
        redirRow2 = QHBoxLayout()
        redirRow2.setSpacing(6)
        redirRow2.addWidget(QLabel(self._t('redir_common_normal'), self.textIconPage))
        self.textRedirCommonNormal = ComboBox(self.textIconPage)
        self.textRedirCommonNormal.addItems([self._t('redir_default'), self._t('redir_2x')])
        self.textRedirCommonNormal.setCurrentIndex(0)
        redirRow2.addWidget(self.textRedirCommonNormal)
        redirRow2.addWidget(QLabel(self._t('redir_common_large'), self.textIconPage))
        self.textRedirCommonLarge = ComboBox(self.textIconPage)
        self.textRedirCommonLarge.addItems([self._t('redir_default'), self._t('redir_2x')])
        self.textRedirCommonLarge.setCurrentIndex(0)
        redirRow2.addWidget(self.textRedirCommonLarge)
        redirRow2.addWidget(QLabel(self._t('redir_menu_normal'), self.textIconPage))
        self.textRedirMenuNormal = ComboBox(self.textIconPage)
        self.textRedirMenuNormal.addItems([self._t('redir_default'), self._t('redir_2x')])
        self.textRedirMenuNormal.setCurrentIndex(0)
        redirRow2.addWidget(self.textRedirMenuNormal)
        redirRow2.addWidget(QLabel(self._t('redir_menu_bold'), self.textIconPage))
        self.textRedirMenuBold = ComboBox(self.textIconPage)
        self.textRedirMenuBold.addItems([self._t('redir_default'), self._t('redir_2x')])
        self.textRedirMenuBold.setCurrentIndex(0)
        redirRow2.addWidget(self.textRedirMenuBold)
        root.addLayout(redirRow2)
        btnRow2 = QHBoxLayout()
        self.textGenBtn = PrimaryPushButton(self._t('generate_button'), self.textIconPage)
        btnRow2.addWidget(self.textGenBtn)
        self.textStrokeChk = CheckBox(self._t('opt_export_stroke'), self.textIconPage)
        btnRow2.addWidget(self.textStrokeChk)
        root.addLayout(btnRow2)
        self.genProgress = QProgressBar(self.textIconPage)
        self.genProgress.setVisible(False)
        self.genProgress.setTextVisible(False)
        root.addWidget(self.genProgress)
        self._text_preview_worker = None
        self._text_current_pages = {'pix': [], 'index': 0}

        def render_list(filter_text: str=''):
            self.textListWidget.clear()
            ft = (filter_text or '').strip().lower()
            fams = sorted((getattr(self, 'system_fonts', {}) or {}).keys())
            if ft:
                fams = [f for f in fams if ft in f.lower()]
            for fam in fams:
                path = getattr(self, 'system_fonts', {}).get(fam)
                item = QListWidgetItem(fam)
                item.setData(Qt.UserRole, path)
                self.textListWidget.addItem(item)

        def resolve_path_for_style(fam: str, style: str) -> Optional[str]:
            variants = getattr(self, 'font_variants', {}).get(fam) or {}
            if style in variants:
                return variants[style]
            if 'Regular' in variants:
                return variants['Regular']
            sys_fonts = getattr(self, 'system_fonts', {})
            if fam in sys_fonts:
                return sys_fonts[fam]
            return next(iter(variants.values()), None)

        def cancel_preview_worker():
            w = self._text_preview_worker
            if w is not None:
                self._text_preview_cancelled = True
                try:
                    if hasattr(w, 'requestInterruption'):
                        w.requestInterruption()
                except Exception:
                    pass
                if w.isRunning():
                    try:
                        w.wait()
                    except Exception:
                        pass
                self._text_preview_worker = None

        def update_page_view():
            if not self._text_current_pages['pix']:
                self.textPreviewLabel.clear()
                self.textPageLabel.setText('0/0')
                return
            idx = max(0, min(self._text_current_pages['index'], len(self._text_current_pages['pix']) - 1))
            self.textPreviewLabel.setPixmap(self._text_current_pages['pix'][idx])
            self.textPageLabel.setText(f"{idx + 1}/{len(self._text_current_pages['pix'])}")
        text_debounce = QTimer(self.textIconPage)
        text_debounce.setSingleShot(True)
        text_debounce.setInterval(250)

        def schedule_preview():
            text_debounce.stop()
            text_debounce.start()
        self._schedule_text_preview = schedule_preview

        def start_preview_now():
            if not self.selected_font_path:
                return
            self.textPreviewLabel.clear()
            self._text_current_pages['pix'] = []
            self._text_current_pages['index'] = 0
            cancel_preview_worker()
            self._text_preview_cancelled = False
            center_applied = int(getattr(self, 'applied_center_offset', 0))
            top_applied = int(getattr(self, 'applied_top_offset', 0))
            baseline_applied = int(getattr(self, 'applied_baseline_offset', 0))
            left_applied = int(getattr(self, 'applied_left_overlap', 0))
            right_applied = int(getattr(self, 'applied_right_overlap', 0))
            adv_applied = int(getattr(self, 'applied_advance_extra', 0))
            w = PreviewPagesWorker(font_path=self.selected_font_path, size=int(self.textSizeSpin.value()), padding=int(self.textPaddingSpin.value()), vertical=bool(self.textVerticalChk.isChecked()), max_chars_per_page=int(self.textPerPageSpin.value()), center_offset=center_applied, top_offset=top_applied, baseline_offset=baseline_applied, left_overlap=left_applied, right_overlap=right_applied, advance_extra=adv_applied)

            def on_ok(metrics, pages):
                pix = []
                for p in pages:
                    bg = Image.new('RGBA', p.image.size, (40, 40, 40, 255))
                    bg.alpha_composite(p.image)
                    qimg = ImageQt(bg).copy()
                    pix.append(QPixmap.fromImage(qimg))
                self._text_current_pages['pix'] = pix
                self._text_current_pages['index'] = 0
                update_page_view()

            def on_fail(msg: str):
                if getattr(self, '_text_preview_cancelled', False):
                    return
                InfoBar.error(title=self._t('gen_failed_title'), content=msg, parent=self, duration=6000)

            def on_p(d, t):
                try:
                    self.previewProgress.setVisible(True)
                    if t and t > 0:
                        self.previewProgress.setRange(0, int(t))
                        self.previewProgress.setValue(int(d))
                    else:
                        self.previewProgress.setRange(0, 0)
                except Exception:
                    pass
            w.progress.connect(on_p)

            def _finish_cleanup(*args, **kwargs):
                try:
                    self.previewProgress.setVisible(False)
                    self.previewProgress.setRange(0, 100)
                    self.previewProgress.setValue(0)
                except Exception:
                    pass
            w.finishedOk.connect(lambda metrics, pages: (_finish_cleanup(), on_ok(metrics, pages)))
            w.failed.connect(lambda msg: (_finish_cleanup(), on_fail(msg)))
            self._text_preview_worker = w
            w.start()
        text_debounce.timeout.connect(start_preview_now)

        def on_list_clicked(*_args):
            item = self.textListWidget.currentItem()
            if not item:
                return
            fam = item.text()
            styles = list((getattr(self, 'font_variants', {}).get(fam) or {}).keys())
            if not styles:
                styles = ['Regular']
            self.textStyleCombo.blockSignals(True)
            self.textStyleCombo.clear()
            for s in ['Regular', 'Bold', 'Italic', 'Bold Italic']:
                if s in styles:
                    self.textStyleCombo.addItem(s)
            for s in styles:
                if self.textStyleCombo.findText(s) < 0:
                    self.textStyleCombo.addItem(s)
            self.textStyleCombo.blockSignals(False)
            if self.textStyleCombo.count() > 0 and self.textStyleCombo.findText(self.textStyleCombo.currentText()) < 0:
                self.textStyleCombo.setCurrentIndex(0)
            path = resolve_path_for_style(fam, self.textStyleCombo.currentText())
            self.selected_font_path = path or item.data(Qt.UserRole)
            try:
                self._update_char_preview()
            except Exception:
                pass
            schedule_preview()
            self.selectedFamilyLabel.setText(fam)
            self.textVerticalChk.setChecked(fam.startswith('@'))
            schedule_preview()
        self.textListWidget.itemSelectionChanged.connect(on_list_clicked)
        self.textListWidget.itemClicked.connect(on_list_clicked)

        def on_style_changed(_):
            item = self.textListWidget.currentItem()
            if not item:
                return
            fam = item.text()
            p = resolve_path_for_style(fam, self.textStyleCombo.currentText())
            if p:
                self.selected_font_path = p
                try:
                    self._update_char_preview()
                except Exception:
                    pass
                schedule_preview()
        self.textStyleCombo.currentTextChanged.connect(on_style_changed)

        def on_pick_file():
            path, _ = QFileDialog.getOpenFileName(self, self._t('dlg_choose_file_title'), '', 'Font Files (*.ttf *.otf *.ttc)')
            if path:
                self.selected_font_path = path
                self.selectedFamilyLabel.setText(os.path.basename(path))
                try:
                    self._update_char_preview()
                except Exception:
                    pass
                schedule_preview()
        self.textFileBtn.clicked.connect(on_pick_file)

        def start_load():
            self.textListWidget.setVisible(False)
            self.textListWidget.clear()
            self.textRefreshBtn.setEnabled(False)
            self._text_fonts_worker = MainWindow.FontsWorker()
            try:
                self._text_fonts_worker.setParent(self)
            except Exception:
                pass

            def on_progress(d, t):
                try:
                    self.fontsProgress.setVisible(True)
                    if t and t > 0:
                        self.fontsProgress.setRange(0, int(t))
                        self.fontsProgress.setValue(int(d))
                    else:
                        self.fontsProgress.setRange(0, 0)
                except Exception:
                    pass

            def on_loaded(fonts: dict):
                self.textListWidget.setVisible(True)
                self.textListWidget.clear()
                if fonts and isinstance(next(iter(fonts.values())), dict):
                    self.font_variants = fonts
                    self.system_fonts = {fam: vals.get('Regular') or next(iter(vals.values())) for fam, vals in fonts.items()}
                else:
                    self.font_variants = {}
                    self.system_fonts = fonts
                render_list(self.textSearchEdit.text())
                self.textRefreshBtn.setEnabled(True)
                self.fontsProgress.setVisible(False)
                self.fontsProgress.setRange(0, 100)
                self.fontsProgress.setValue(0)
                self._text_fonts_worker = None

            def on_failed(msg: str):
                InfoBar.error(title=self._t('gen_failed_title'), content=msg, parent=self, duration=6000)
                self.textRefreshBtn.setEnabled(True)
                self.fontsProgress.setVisible(False)
                self.fontsProgress.setRange(0, 100)
                self.fontsProgress.setValue(0)
                self._text_fonts_worker = None
            self._text_fonts_worker.progress.connect(on_progress)
            self._text_fonts_worker.finishedOk.connect(on_loaded)
            self._text_fonts_worker.failed.connect(on_failed)
            self._text_fonts_worker.start()
        self.textRefreshBtn.clicked.connect(start_load)
        self.textSearchEdit.textChanged.connect(lambda t: render_list(t))

        def go_prev():
            if self._text_current_pages['pix']:
                self._text_current_pages['index'] = max(0, self._text_current_pages['index'] - 1)
                update_page_view()

        def go_next():
            if self._text_current_pages['pix']:
                self._text_current_pages['index'] = min(len(self._text_current_pages['pix']) - 1, self._text_current_pages['index'] + 1)
                update_page_view()
        self.textPrevBtn.clicked.connect(go_prev)
        self.textNextBtn.clicked.connect(go_next)
        self.textPerPageSpin.valueChanged.connect(lambda _: schedule_preview())
        self.textVerticalChk.toggled.connect(lambda _: schedule_preview())
        try:
            self.textVerticalChk.toggled.connect(lambda _: self._update_char_preview())
        except Exception:
            pass
        self.textSizeSpin.valueChanged.connect(lambda _: schedule_preview())
        self.textPaddingSpin.valueChanged.connect(lambda _: schedule_preview())
        self.textSaveBtn.clicked.connect(self._choose_save_path_text)
        self.textGenBtn.clicked.connect(self._generate_from_text_page)
        QTimer.singleShot(0, start_load)
        try:
            QTimer.singleShot(0, lambda: self._update_char_preview())
        except Exception:
            pass
        try:
            self.textIconNavBtn = self.addSubInterface(self.textIconPage, FluentIcon.DOCUMENT, self._t('nav_text_icon'), NavigationItemPosition.TOP)
        except Exception:
            self.textIconNavBtn = None

    def _choose_save_path_text(self):
        folder = QFileDialog.getExistingDirectory(self, self._t('choose_save_path_button'), '')
        if folder:
            self.textSaveEdit.setText(folder)

    def _on_progress_text(self, done: int, total: int):
        pct = int(done * 100 / max(total, 1))
        self.textGenBtn.setText(self._t('gen_generating_pct').format(pct=pct))
        try:
            self.genProgress.setVisible(True)
            if total and total > 0:
                self.genProgress.setRange(0, int(total))
                self.genProgress.setValue(int(done))
            else:
                self.genProgress.setRange(0, 0)
        except Exception:
            pass

    def _on_finished_text(self, ini_path: str):
        InfoBar.success(title=self._t('gen_success_title'), content=self._t('gen_success_saved').format(path=ini_path), parent=self, duration=6000)
        self.textGenBtn.setEnabled(True)
        self.textGenBtn.setText(self._t('generate_button'))
        self.worker = None
        try:
            self.genProgress.setVisible(False)
            self.genProgress.setRange(0, 100)
            self.genProgress.setValue(0)
        except Exception:
            pass

    def _on_failed_text(self, msg: str):
        InfoBar.error(title=self._t('gen_failed_title'), content=msg, parent=self, duration=8000)
        self.textGenBtn.setEnabled(True)
        self.textGenBtn.setText(self._t('generate_button'))
        self.worker = None
        try:
            self.genProgress.setVisible(False)
            self.genProgress.setRange(0, 100)
            self.genProgress.setValue(0)
        except Exception:
            pass

    def _generate_from_text_page(self):
        if not self.selected_font_path:
            InfoBar.error(self._t('err_select_font'), parent=self)
            return
        base_input = self.textSaveEdit.text().strip()
        if not base_input:
            InfoBar.error(self._t('err_select_save'), parent=self)
            return
        size = int(self.textSizeSpin.value())
        padding = int(self.textPaddingSpin.value())

        def _sanitize_name(s: str) -> str:
            return ''.join((c if c not in '<>:"/\\|?*' else ' ' for c in s)).strip()
        if os.path.isdir(base_input):
            family = self.selectedFamilyLabel.text().strip() or 'Font'
            if family.startswith('@'):
                family = family[1:]
            base_name = f'_{_sanitize_name(family)} {size}px'
            base = os.path.join(base_input, base_name)
        else:
            base = base_input
        export_stroke = bool(self.textStrokeChk.isChecked())
        preset_mode = None
        if not self.selected_font_path:
            InfoBar.error('No font selected', 'Please choose a font file on the generation page', parent=self)
            self.textGenBtn.setEnabled(True)
            self.textGenBtn.setText(self._t('generate_button'))
            return
        center_applied = int(getattr(self, 'applied_center_offset', 0))
        top_applied = int(getattr(self, 'applied_top_offset', 0))
        baseline_applied = int(getattr(self, 'applied_baseline_offset', 0))
        left_applied = int(getattr(self, 'applied_left_overlap', 0))
        right_applied = int(getattr(self, 'applied_right_overlap', 0))
        adv_applied = int(getattr(self, 'applied_advance_extra', 0))
        self.textGenBtn.setEnabled(False)
        self.textGenBtn.setText(self._t('gen_generating'))
        redir_modes = {'Common Normal': '2x' if self.textRedirCommonNormal.currentIndex() == 1 else 'default', 'Common Large': '2x' if self.textRedirCommonLarge.currentIndex() == 1 else 'default', 'Menu Normal': '2x' if self.textRedirMenuNormal.currentIndex() == 1 else 'default', 'Menu Bold': '2x' if self.textRedirMenuBold.currentIndex() == 1 else 'default'}
        self.worker = GenerateWorker(self.selected_font_path, size, padding, base, bool(self.textVerticalChk.isChecked()), int(self.textPerPageSpin.value()), export_stroke, preset_mode, redir_modes=redir_modes, center_offset=center_applied, top_offset=top_applied, baseline_offset=baseline_applied, left_overlap=left_applied, right_overlap=right_applied, advance_extra=adv_applied)
        try:
            self.genProgress.setVisible(True)
            self.genProgress.setRange(0, 0)
        except Exception:
            pass
        self.worker.progress.connect(lambda d, t: self._on_progress_text(d, t))
        self.worker.finishedOk.connect(self._on_finished_text)
        self.worker.failed.connect(self._on_failed_text)
        self.worker.start()

    def _init_simple_fine_tune_controls(self, parent_layout):
        tune_wrapper = QWidget(self.textIconPage)
        tune_wrapper.setContentsMargins(0, 0, 0, 0)
        tune_wrapper.setMinimumHeight(90)
        tune_layout = QHBoxLayout(tune_wrapper)
        tune_layout.setContentsMargins(8, 4, 8, 4)
        tune_layout.setSpacing(12)
        left_box = QVBoxLayout()
        left_box.setSpacing(6)
        title = QLabel('Tuning Preview', tune_wrapper)
        left_box.addWidget(title)
        self.charInput = LineEdit(self.textIconPage)
        self.charInput.setPlaceholderText('Test character (default X)')
        try:
            self.charInput.setMaxLength(1)
        except Exception:
            pass
        self.charInput.setText('X')
        left_box.addWidget(self.charInput)
        row = QHBoxLayout()
        row.setSpacing(8)
        center_label = QLabel('Center:', tune_wrapper)
        self.center_spin = SpinBox(tune_wrapper)
        self.center_spin.setRange(-50, 50)
        self.center_spin.setValue(0)
        self.center_spin.setFixedWidth(60)
        row.addWidget(center_label)
        row.addWidget(self.center_spin)
        top_label = QLabel('Top:', tune_wrapper)
        self.top_spin = SpinBox(tune_wrapper)
        self.top_spin.setRange(-50, 50)
        self.top_spin.setValue(0)
        self.top_spin.setFixedWidth(60)
        row.addWidget(top_label)
        row.addWidget(self.top_spin)
        baseline_label = QLabel('Baseline:', tune_wrapper)
        self.baseline_spin = SpinBox(tune_wrapper)
        self.baseline_spin.setRange(-50, 50)
        self.baseline_spin.setValue(0)
        self.baseline_spin.setFixedWidth(60)
        row.addWidget(baseline_label)
        row.addWidget(self.baseline_spin)
        left_label = QLabel('Left extra:', tune_wrapper)
        self.left_overlap_spin = SpinBox(tune_wrapper)
        self.left_overlap_spin.setRange(0, 64)
        self.left_overlap_spin.setValue(0)
        self.left_overlap_spin.setFixedWidth(60)
        row.addWidget(left_label)
        row.addWidget(self.left_overlap_spin)
        right_label = QLabel('Right extra:', tune_wrapper)
        self.right_overlap_spin = SpinBox(tune_wrapper)
        self.right_overlap_spin.setRange(0, 64)
        self.right_overlap_spin.setValue(0)
        self.right_overlap_spin.setFixedWidth(60)
        row.addWidget(right_label)
        row.addWidget(self.right_overlap_spin)
        adv_label = QLabel('Advanced:', tune_wrapper)
        self.advance_extra_spin = SpinBox(tune_wrapper)
        self.advance_extra_spin.setRange(0, 128)
        self.advance_extra_spin.setValue(0)
        self.advance_extra_spin.setFixedWidth(60)
        row.addWidget(adv_label)
        row.addWidget(self.advance_extra_spin)
        row.addStretch(1)
        left_box.addLayout(row)
        self.applyTuneBtn = PrimaryPushButton('Apply Tuning', tune_wrapper)
        left_box.addWidget(self.applyTuneBtn)
        tune_layout.addLayout(left_box, 1)
        self.charPreviewLabel = QLabel(self.textIconPage)
        self.charPreviewLabel.setAlignment(Qt.AlignCenter)
        self.charPreviewLabel.setFixedSize(QSize(70, 70))
        self.charPreviewLabel.setStyleSheet('QLabel { border: 1px solid #404040; border-radius: 4px; background-color: #000000; }')
        tune_layout.addWidget(self.charPreviewLabel, 0)
        parent_layout.addWidget(tune_wrapper)
        if not hasattr(self, 'applied_center_offset'):
            self.applied_center_offset = 0
        if not hasattr(self, 'applied_top_offset'):
            self.applied_top_offset = 0
        if not hasattr(self, 'applied_baseline_offset'):
            self.applied_baseline_offset = 0
        try:
            self.charInput.textChanged.connect(self._update_char_preview)
            self.textSizeSpin.valueChanged.connect(self._update_char_preview)
            if hasattr(self, 'textPaddingSpin'):
                self.textPaddingSpin.valueChanged.connect(self._update_char_preview)
            if hasattr(self, 'textVerticalChk'):
                self.textVerticalChk.toggled.connect(self._update_char_preview)
        except Exception:
            pass
        self.center_spin.valueChanged.connect(self._on_fine_tune_changed)
        self.top_spin.valueChanged.connect(self._on_fine_tune_changed)
        self.baseline_spin.valueChanged.connect(self._on_fine_tune_changed)
        self.left_overlap_spin.valueChanged.connect(self._on_fine_tune_changed)
        self.right_overlap_spin.valueChanged.connect(self._on_fine_tune_changed)
        self.advance_extra_spin.valueChanged.connect(self._on_fine_tune_changed)
        try:
            self.center_spin.valueChanged.connect(self._update_char_preview)
            self.top_spin.valueChanged.connect(self._update_char_preview)
            self.baseline_spin.valueChanged.connect(self._update_char_preview)
            self.left_overlap_spin.valueChanged.connect(self._update_char_preview)
            self.right_overlap_spin.valueChanged.connect(self._update_char_preview)
            self.advance_extra_spin.valueChanged.connect(self._update_char_preview)
        except Exception:
            pass
        self.applyTuneBtn.clicked.connect(self._on_apply_tune)

    def _on_fine_tune_changed(self):
        if hasattr(self, 'center_offset'):
            self.center_offset = self.center_spin.value()
        if hasattr(self, 'top_offset'):
            self.top_offset = self.top_spin.value()
        if hasattr(self, 'baseline_offset'):
            self.baseline_offset = self.baseline_spin.value()
        if hasattr(self, 'left_overlap'):
            self.left_overlap = self.left_overlap_spin.value()
        else:
            self.left_overlap = self.left_overlap_spin.value()
        if hasattr(self, 'right_overlap'):
            self.right_overlap = self.right_overlap_spin.value()
        else:
            self.right_overlap = self.right_overlap_spin.value()
        if hasattr(self, 'advance_extra'):
            self.advance_extra = self.advance_extra_spin.value()
        else:
            self.advance_extra = self.advance_extra_spin.value()

    def _on_apply_tune(self):
        try:
            center = int(self.center_spin.value())
            top = int(self.top_spin.value())
            base = int(self.baseline_spin.value())
            l_overlap = int(self.left_overlap_spin.value())
            r_overlap = int(self.right_overlap_spin.value())
            adv_extra = int(self.advance_extra_spin.value())
        except Exception:
            center, top, base, l_overlap, r_overlap, adv_extra = (0, 0, 0, 0, 0, 0)
        self.applied_center_offset = center
        self.applied_top_offset = top
        self.applied_baseline_offset = base
        self.applied_left_overlap = l_overlap
        self.applied_right_overlap = r_overlap
        self.applied_advance_extra = adv_extra
        try:
            InfoBar.success(title='Tuning applied', content='Overall preview will refresh after applying', parent=self, duration=2500)
        except Exception:
            pass
        try:
            if hasattr(self, '_schedule_text_preview') and callable(self._schedule_text_preview):
                self._schedule_text_preview()
        except Exception:
            pass

    def _update_char_preview(self):
        try:
            from PIL import ImageDraw
            if not getattr(self, 'selected_font_path', None):
                self.charPreviewLabel.setText('No font selected')
                return
            ch = self.charInput.text() or 'X'
            if len(ch) > 1:
                ch = ch[0]
            size_px = int(self.textSizeSpin.value())
            font = load_font(self.selected_font_path, size_px)
            baseline, top, _ = measure_font_metrics(font)
            cb = render_char_bitmap(font, ch)
            glyph = cb.image
            W = 70
            H = 70
            base_y = H // 2
            center_offset = int(self.center_spin.value()) if hasattr(self, 'center_spin') else 0
            top_offset = int(self.top_spin.value()) if hasattr(self, 'top_spin') else 0
            baseline_offset = int(self.baseline_spin.value()) if hasattr(self, 'baseline_spin') else 0
            left_overlap = int(self.left_overlap_spin.value()) if hasattr(self, 'left_overlap_spin') else 0
            right_overlap = int(self.right_overlap_spin.value()) if hasattr(self, 'right_overlap_spin') else 0
            advance_extra = int(self.advance_extra_spin.value()) if hasattr(self, 'advance_extra_spin') else 0
            ascend = baseline - top
            try:
                padding_px = int(self.textPaddingSpin.value())
            except Exception:
                padding_px = 0
            top_padding = int(padding_px / 2)
            w_char, h_char = glyph.size
            scale = min((W - 8) / max(w_char, 1), (H - 8) / max(h_char, 1), 1.0)
            if scale < 1.0:
                from PIL import Image as _PIL_Image
                glyph = glyph.resize((max(1, int(round(w_char * scale))), max(1, int(round(h_char * scale)))), _PIL_Image.LANCZOS)
                w_char, h_char = glyph.size
            ascend_scaled = int(round(ascend * scale))
            top_padding_scaled = int(round(top_padding * scale))
            if bool(self.textVerticalChk.isChecked()):
                glyph = glyph.rotate(90, expand=True)
                w_char, h_char = glyph.size
            w_char, h_char = glyph.size
            x = (W - w_char) // 2
            y = (H - h_char) // 2
            half_asc = max(0, int(round(ascend_scaled / 2)))
            center_line_y = base_y + top_padding_scaled - center_offset
            top_line_y = center_line_y - half_asc - top_offset
            baseline_line_y = center_line_y + half_asc - baseline_offset
            img = Image.new('RGBA', (W, H), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)
            try:
                if glyph.mode in ('RGBA', 'LA'):
                    mask = glyph.split()[3] if glyph.mode == 'RGBA' else glyph.split()[1]
                else:
                    mask = None
                if mask is not None:
                    glyph_white = Image.new('RGBA', glyph.size, (255, 255, 255, 255))
                    glyph_white.putalpha(mask)
                    img.alpha_composite(glyph_white, (x, y))
                else:
                    draw.text((x, y), ch, font=font, fill=(255, 255, 255, 255))
            except Exception:
                img.alpha_composite(glyph, (x, y))
            bly = min(H - 1, max(0, int(baseline_line_y)))
            tly = min(H - 1, max(0, int(top_line_y)))
            draw.line([(4, bly), (W - 4, bly)], fill=(255, 64, 64, 255), width=1)
            draw.line([(4, tly), (W - 4, tly)], fill=(64, 160, 255, 255), width=1)
            for i in range(4, W - 4, 6):
                draw.line([(i, int(center_line_y)), (i + 3, int(center_line_y))], fill=(0, 180, 0, 255), width=1)
            left_scaled = int(round(left_overlap * scale))
            right_scaled = int(round(right_overlap * scale))
            left_line_x = int(x - left_scaled)
            right_line_x = int(x + w_char + right_scaled)
            y1 = min(max(tly, 0), H - 1)
            y2 = min(max(bly, 0), H - 1)
            if left_scaled > 0:
                lx = min(W - 1, max(0, left_line_x))
                draw.line([(lx, y1), (lx, y2)], fill=(255, 200, 0, 255), width=1)
            else:
                lx = min(W - 1, max(0, int(x)))
                draw.line([(lx, y1), (lx, y2)], fill=(255, 200, 0, 128), width=1)
            if right_scaled > 0:
                rx = min(W - 1, max(0, right_line_x))
                draw.line([(rx, y1), (rx, y2)], fill=(255, 200, 0, 255), width=1)
            else:
                rx = min(W - 1, max(0, int(x + w_char)))
                draw.line([(rx, y1), (rx, y2)], fill=(255, 200, 0, 128), width=1)
            adv_scaled = int(round(advance_extra * scale))
            if adv_scaled > 0:
                rect_x1 = min(W - 1, max(0, right_line_x))
                rect_x2 = min(W - 1, max(0, right_line_x + adv_scaled))
                rx1 = min(rect_x1, rect_x2)
                rx2 = max(rect_x1, rect_x2)
                top_y = min(y1, y2)
                bot_y = max(y1, y2)
                for xx in range(rx1, rx2 + 1):
                    draw.line([(xx, top_y), (xx, bot_y)], fill=(255, 0, 255, 128), width=1)
            qimg = ImageQt(img).copy()
            self.charPreviewLabel.setPixmap(QPixmap.fromImage(qimg))
        except Exception as e:
            try:
                self.charPreviewLabel.setText(f'Preview error: {str(e)}')
            except Exception:
                pass

def launch():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.resize(720, 520)
    w.show()
    return app