# -*- coding: utf-8 -*-
import sys, os, re, json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QMessageBox, QTabWidget, QListWidget, QAbstractItemView,
    QMainWindow, QStatusBar, QFileDialog, QDialog, QGridLayout,
    QColorDialog, QTextEdit, QRadioButton, QButtonGroup, QSpinBox, QFrame,
    QMenu, QProgressBar
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QColor, QFont, QDesktopServices

VERSION = "V0.84"

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config.json")



DEFAULT_THEME = {
    'bg':          '#1e1e2e',
    'tab_btn':     '#007AAE',
    'bottom_btn':  '#3F45AA',
    'inactive_btn':'#808080',
    'text':        '#E0E0E0',
    'tab_selected':'#00A2E8',
    'pane':        '#005174',
    'input_bg':    '#2b2b3b',
    'input_text':  '#E0E0E0',
    'list_bg':     '#2b2b2b',
    'list_text':   '#E0E0E0',
    'popup_bg':    '#2b2b2b',
    'popup_text':  '#FFFFFF',
}

DEFAULT_CONFIG = {
    'theme': DEFAULT_THEME,
    'duplicate': 'numbering',
    'editor': '',
}

class FolderScanWorker(QThread):
    path_found = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def run(self):
        for root, _, files in os.walk(self.folder):
            for f in files:
                full_path = os.path.join(root, f)
                self.path_found.emit(full_path)
        self.finished.emit()

# ==============================
# 1. Worker Thread 추가
# ==============================
class FileSearchWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, file_list, keyword):
        super().__init__()
        self.file_list = file_list
        self.keyword = keyword

    def run(self):
        results = []
        total = max(len(self.file_list), 1)

        for i, path in enumerate(self.file_list):
            try:
                count = 0
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        count += line.count(self.keyword)

                if count > 0:
                    results.append((path, count))
            except Exception as e:
                print(e)

            percent = int((i + 1) / total * 100)
            self.progress.emit(percent)

        self.finished.emit(results)


# ==============================
# 2. 로딩 팝업 추가
# ==============================
class LoadingDialog(QDialog):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.setWindowTitle("처리 중")
        self.setFixedSize(360, 140)

        layout = QVBoxLayout(self)

        self.label = QLabel("파일 목록 불러오는 중...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.percent_label)

        self.setStyleSheet(dialog_style(theme))

    def set_progress(self, value):
        self.progress.setValue(value)
        self.percent_label.setText(f"{value}%")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cfg = dict(DEFAULT_CONFIG)
                cfg['duplicate'] = data.get('duplicate', DEFAULT_CONFIG['duplicate'])
                cfg['editor'] = data.get('editor', DEFAULT_CONFIG['editor'])
                t = dict(DEFAULT_THEME)
                t.update(data.get('theme', {}))
                cfg['theme'] = t
                return cfg        
        except Exception as e:
            print(e)

    return dict(DEFAULT_CONFIG)

def save_config(config):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except: pass

def dialog_style(theme):
    return f"""
        QDialog {{ background-color: {theme['popup_bg']}; }}
        QWidget {{ background-color: {theme['popup_bg']}; }}
        QLabel {{ color: {theme['popup_text']}; font-weight: bold; }}
        QLineEdit {{ background-color: {theme['input_bg']}; color: {theme['input_text']};
            border: 1px solid {theme['tab_btn']}; border-radius: 4px; padding: 4px; }}
        QSpinBox {{ background-color: {theme['input_bg']}; color: {theme['input_text']};
            border: 1px solid {theme['tab_btn']}; border-radius: 4px; padding: 4px; }}
        QRadioButton {{ color: {theme['popup_text']}; spacing: 6px; }}
        QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 7px;
            border: 2px solid {theme['tab_btn']}; background: {theme['input_bg']}; }}
        QRadioButton::indicator:checked {{ background: {theme['tab_selected']};
            border: 2px solid {theme['tab_selected']}; }}
        QRadioButton::indicator:hover {{ border: 2px solid {theme['tab_selected']}; }}
        QPushButton {{ background-color: {theme['tab_btn']}; color: white;
            font-weight: bold; border-radius: 4px; padding: 6px 12px; }}
        QPushButton:hover {{ background-color: {theme['tab_selected']}; }}
        QFrame[frameShape="4"] {{ border: 1px solid {theme['tab_btn']}; }}
        QLabel {{ border: none; }}
    """

def preview_label_style(theme):
    return f"background-color: {theme['input_bg']}; color: {theme['tab_selected']}; border: 1px solid {theme['tab_btn']}; border-radius: 4px; padding: 4px; font-weight: normal;"

def get_list_style(theme):
    return f"""
        QListWidget {{
            background-color: {theme['input_bg']};
            color: {theme['text']};
            border: 1px solid {theme['tab_btn']};
            outline: none;
        }}
        QListWidget::item {{
            height: 20px; 
            padding: 0px; 
            margin: 0px;
        }}
        QListWidget::item:selected {{
            background-color: {theme['tab_selected']};
            color: white;
        }}
    """

def get_preview_name(list_w):
    if list_w.count() == 0:
        return None
    return os.path.splitext(os.path.basename(list_w.item(0).text()))

def make_separator():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line

def set_elided(lbl, text):
    fm = lbl.fontMetrics()
    elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, max(lbl.width(), 300))
    lbl.setText(elided)
    lbl.setToolTip(text)


class FileListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.all_paths = set()  # 중복 체크용 세트 초기화 (에러 방지)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSpacing(0)      # 아이템 간 추가 간격 제거
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def _existing_paths(self):
        return {self.item(i).text() for i in range(self.count())}

    def add_path(self, path):
        if not hasattr(self, 'all_paths'):
            self.all_paths = set()

        # 실제 전체 경로로 중복 체크
        if path in self.all_paths:
            return

        from PyQt6.QtWidgets import QListWidgetItem
        from PyQt6.QtCore import QSize, Qt

        parent_dir = os.path.basename(os.path.dirname(path))
        display_name = os.path.join(parent_dir, os.path.basename(path))

        item = QListWidgetItem(display_name)
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setSizeHint(QSize(0, 18))
        item.setToolTip(path)

        self.addItem(item)
        self.all_paths.add(path)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(e)

    def delete_selected(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    def _context_menu(self, pos):
        if self.count() == 0: return
        menu = QMenu(self)
        act_del = QAction("🗑 선택 항목 삭제  (Delete)", self)
        act_del.triggered.connect(self.delete_selected)
        act_all = QAction("☑ 전체 선택  (Ctrl+A)", self)
        act_all.triggered.connect(self.selectAll)
        act_clear = QAction("✖ 목록 전체 초기화", self)
        act_clear.triggered.connect(self.clear)
        menu.addAction(act_del)
        menu.addAction(act_all)
        menu.addSeparator()
        menu.addAction(act_clear)
        menu.exec(self.mapToGlobal(pos))

    def dragEnterEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dragMoveEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            for url in e.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for f in files: self.add_path(os.path.join(root, f))
                elif os.path.isfile(path):
                    self.add_path(path)
        else: e.ignore()


def add_preview_widgets(layout, obj, theme):
    layout.addWidget(QLabel("미리보기:"))
    lbl_title_b = QLabel("수정 전")
    lbl_title_b.setStyleSheet(f"color: {theme['inactive_btn']}; font-size: 8pt; font-weight: normal;")
    layout.addWidget(lbl_title_b)
    obj.prev_before = QLabel("─")
    obj.prev_before.setStyleSheet(preview_label_style(theme))
    obj.prev_before.setMinimumWidth(300)
    layout.addWidget(obj.prev_before)
    lbl_title_a = QLabel("수정 후")
    lbl_title_a.setStyleSheet(f"color: {theme['tab_selected']}; font-size: 8pt; font-weight: normal;")
    layout.addWidget(lbl_title_a)
    obj.prev_after = QLabel("─")
    obj.prev_after.setStyleSheet(preview_label_style(theme))
    obj.prev_after.setMinimumWidth(300)
    layout.addWidget(obj.prev_after)


class RemoveBracketDialog(QDialog):
    def __init__(self, parent, theme, list_w):
        super().__init__(parent)
        self.setWindowTitle("묶인곳 지우기")
        self.setFixedSize(360, 320)
        self.theme = theme
        self.list_w = list_w
        self.result_confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("지정된 문자로 묶인 부분을 삭제합니다"))
        layout.addWidget(make_separator())

        rh1 = QHBoxLayout()
        rh1.addWidget(QLabel("시작 문자"))
        self.start_edit = QLineEdit(); self.start_edit.setPlaceholderText("예: (")
        self.start_edit.setFixedWidth(200)
        rh1.addWidget(self.start_edit)
        layout.addLayout(rh1)
        rh2 = QHBoxLayout()
        rh2.addWidget(QLabel("끝 문자"))
        self.end_edit = QLineEdit(); self.end_edit.setPlaceholderText("예: )")
        self.end_edit.setFixedWidth(200)
        rh2.addWidget(self.end_edit)
        layout.addLayout(rh2)

        self.bg_all = QRadioButton("전부 삭제")
        self.bg_first = QRadioButton("첫 번째만 삭제")
        self.bg_all.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.bg_all); grp.addButton(self.bg_first)
        rh = QHBoxLayout()
        rh.addWidget(self.bg_all); rh.addWidget(self.bg_first)
        layout.addLayout(rh)

        layout.addWidget(make_separator())
        add_preview_widgets(layout, self, theme)

        bh = QHBoxLayout()
        btn_ok = QPushButton("확인"); btn_cancel = QPushButton("취소")
        btn_ok.clicked.connect(self.confirm); btn_cancel.clicked.connect(self.reject)
        bh.addWidget(btn_ok); bh.addWidget(btn_cancel)
        layout.addLayout(bh)

        self.start_edit.textChanged.connect(self.update_preview)
        self.end_edit.textChanged.connect(self.update_preview)
        self.bg_all.toggled.connect(self.update_preview)
        self.setStyleSheet(dialog_style(theme))
        self.update_preview()

    def transform(self, name):
        s, e = self.start_edit.text(), self.end_edit.text()
        if not s or not e: return name
        pat = re.escape(s) + '.*?' + re.escape(e)
        return re.sub(pat, '', name) if self.bg_all.isChecked() else re.sub(pat, '', name, count=1)

    def update_preview(self):
        result = get_preview_name(self.list_w)
        if result is None:
            self.prev_before.setText("파일 없음"); self.prev_after.setText("─"); return
        n, ext = result
        set_elided(self.prev_before, n + ext)
        set_elided(self.prev_after, self.transform(n) + ext)

    def confirm(self):
        self.result_confirmed = True; self.accept()


class NumberFilterDialog(QDialog):
    def __init__(self, parent, theme, list_w):
        super().__init__(parent)
        self.setWindowTitle("숫자 남기기/삭제")
        self.setFixedSize(360, 260)
        self.theme = theme
        self.list_w = list_w
        self.result_confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("선택에 따라 숫자를 남기거나 삭제합니다"))
        layout.addWidget(make_separator())

        self.rb_keep = QRadioButton("숫자만 남기기")
        self.rb_del = QRadioButton("숫자 모두 삭제")
        self.rb_keep.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_keep); grp.addButton(self.rb_del)
        rh = QHBoxLayout()
        rh.addWidget(self.rb_keep); rh.addWidget(self.rb_del)
        layout.addLayout(rh)

        layout.addWidget(make_separator())
        add_preview_widgets(layout, self, theme)

        bh = QHBoxLayout()
        btn_ok = QPushButton("확인"); btn_cancel = QPushButton("취소")
        btn_ok.clicked.connect(self.confirm); btn_cancel.clicked.connect(self.reject)
        bh.addWidget(btn_ok); bh.addWidget(btn_cancel)
        layout.addLayout(bh)

        self.rb_keep.toggled.connect(self.update_preview)
        self.setStyleSheet(dialog_style(theme))
        self.update_preview()

    def transform(self, name):
        return re.sub(r'\D', '', name) if self.rb_keep.isChecked() else re.sub(r'\d', '', name)

    def update_preview(self):
        result = get_preview_name(self.list_w)
        if result is None:
            self.prev_before.setText("파일 없음"); self.prev_after.setText("─"); return
        n, ext = result
        set_elided(self.prev_before, n + ext)
        set_elided(self.prev_after, self.transform(n) + ext)

    def confirm(self):
        self.result_confirmed = True; self.accept()


class PadNumberDialog(QDialog):
    def __init__(self, parent, theme, list_w):
        super().__init__(parent)
        self.setWindowTitle("자리수 맞추기")
        self.setFixedSize(380, 380)
        self.theme = theme
        self.list_w = list_w
        self.result_confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("숫자 부분의 자리수를 맞춰 0을 붙입니다"))
        layout.addWidget(make_separator())

        gh = QHBoxLayout()
        gh.addWidget(QLabel("자리수"))
        self.spin = QSpinBox(); self.spin.setRange(1, 10); self.spin.setValue(3)
        self.spin.setFixedWidth(70)
        gh.addWidget(self.spin); gh.addStretch()
        layout.addLayout(gh)

        self.rb_all = QRadioButton("모든 숫자 적용")
        self.rb_last = QRadioButton("마지막 숫자만")
        self.rb_all.setChecked(True)
        grp1 = QButtonGroup(self); grp1.addButton(self.rb_all); grp1.addButton(self.rb_last)
        rh1 = QHBoxLayout(); rh1.addWidget(self.rb_all); rh1.addWidget(self.rb_last)
        layout.addLayout(rh1)

        self.rb_front = QRadioButton("앞번호 맞춤 (앞에 0 추가)")
        self.rb_back = QRadioButton("뒷번호 맞춤 (뒤에 0 추가)")
        self.rb_front.setChecked(True)
        grp2 = QButtonGroup(self); grp2.addButton(self.rb_front); grp2.addButton(self.rb_back)
        rh2 = QHBoxLayout(); rh2.addWidget(self.rb_front); rh2.addWidget(self.rb_back)
        layout.addLayout(rh2)

        layout.addWidget(QLabel("자리수 초과 시:"))
        self.rb_keep_over = QRadioButton("그냥 놔두기")
        self.rb_trim = QRadioButton("앞자리 삭제해서 맞추기")
        self.rb_keep_over.setChecked(True)
        grp3 = QButtonGroup(self); grp3.addButton(self.rb_keep_over); grp3.addButton(self.rb_trim)
        rh3 = QHBoxLayout(); rh3.addWidget(self.rb_keep_over); rh3.addWidget(self.rb_trim)
        layout.addLayout(rh3)

        layout.addWidget(make_separator())
        add_preview_widgets(layout, self, theme)

        bh = QHBoxLayout()
        btn_ok = QPushButton("확인"); btn_cancel = QPushButton("취소")
        btn_ok.clicked.connect(self.confirm); btn_cancel.clicked.connect(self.reject)
        bh.addWidget(btn_ok); bh.addWidget(btn_cancel)
        layout.addLayout(bh)

        self.spin.valueChanged.connect(self.update_preview)
        self.rb_all.toggled.connect(self.update_preview)
        self.rb_front.toggled.connect(self.update_preview)
        self.rb_keep_over.toggled.connect(self.update_preview)
        self.setStyleSheet(dialog_style(theme))
        self.update_preview()

    def pad_num(self, m):
        n = m.group(); w = self.spin.value()
        if len(n) > w:
            return n if self.rb_keep_over.isChecked() else n[-w:]
        return n.zfill(w) if self.rb_front.isChecked() else n.ljust(w, '0')

    def transform(self, name):
        if self.rb_all.isChecked():
            return re.sub(r'\d+', self.pad_num, name)
        nums = list(re.finditer(r'\d+', name))
        if not nums: return name
        last = nums[-1]
        return name[:last.start()] + self.pad_num(last) + name[last.end():]

    def update_preview(self):
        result = get_preview_name(self.list_w)
        if result is None:
            self.prev_before.setText("파일 없음"); self.prev_after.setText("─"); return
        n, ext = result
        set_elided(self.prev_before, n + ext)
        set_elided(self.prev_after, self.transform(n) + ext)

    def confirm(self):
        self.result_confirmed = True; self.accept()


class AddNumberDialog(QDialog):
    def __init__(self, parent, theme, list_w):
        super().__init__(parent)
        self.setWindowTitle("번호 붙이기")
        self.setFixedSize(400, 460)
        self.theme = theme
        self.list_w = list_w
        self.result_confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("붙일 숫자의 자리수와 시작값을 지정합니다"))
        layout.addWidget(make_separator())

        gh = QHBoxLayout()
        gh.addWidget(QLabel("자리수"))
        self.spin_w = QSpinBox(); self.spin_w.setRange(1, 10); self.spin_w.setValue(3); self.spin_w.setFixedWidth(75)
        gh.addWidget(self.spin_w)
        gh.addSpacing(8)
        gh.addWidget(QLabel("시작값"))
        self.spin_s = QSpinBox(); self.spin_s.setRange(0, 99999); self.spin_s.setValue(1); self.spin_s.setFixedWidth(75)
        gh.addWidget(self.spin_s)
        gh.addSpacing(8)
        gh.addWidget(QLabel("구분자"))
        self.sep_edit = QLineEdit("_"); self.sep_edit.setFixedWidth(45)
        gh.addWidget(self.sep_edit)
        gh.addStretch()
        layout.addLayout(gh)

        layout.addWidget(QLabel("번호 위치:"))
        self.rb_after = QRadioButton("이름 뒤에 번호 붙임")
        self.rb_before = QRadioButton("이름 앞에 번호 붙임")
        self.rb_folder_after = QRadioButton("폴더별로 뒤 번호 붙임")
        self.rb_folder_before = QRadioButton("폴더별로 앞 번호 붙임")
        self.rb_after.setChecked(True)
        grp1 = QButtonGroup(self)
        for rb in [self.rb_after, self.rb_before, self.rb_folder_after, self.rb_folder_before]:
            grp1.addButton(rb)
        rh1 = QHBoxLayout(); rh1.addWidget(self.rb_after); rh1.addWidget(self.rb_before)
        rh2 = QHBoxLayout(); rh2.addWidget(self.rb_folder_after); rh2.addWidget(self.rb_folder_before)
        layout.addLayout(rh1)
        layout.addLayout(rh2)

        layout.addWidget(make_separator())
        layout.addWidget(QLabel("번호 붙이는 방식:"))
        self.rb_add = QRadioButton("추가로 붙임")
        self.rb_replace = QRadioButton("기존 번호 교체")
        self.rb_add.setChecked(True)
        grp2 = QButtonGroup(self); grp2.addButton(self.rb_add); grp2.addButton(self.rb_replace)
        rh3 = QHBoxLayout(); rh3.addWidget(self.rb_add); rh3.addWidget(self.rb_replace)
        layout.addLayout(rh3)

        layout.addWidget(make_separator())
        add_preview_widgets(layout, self, theme)

        bh = QHBoxLayout()
        btn_ok = QPushButton("확인"); btn_cancel = QPushButton("취소")
        btn_ok.clicked.connect(self.confirm); btn_cancel.clicked.connect(self.reject)
        bh.addWidget(btn_ok); bh.addWidget(btn_cancel)
        layout.addLayout(bh)

        for w in [self.spin_w, self.spin_s]: w.valueChanged.connect(self.update_preview)
        self.sep_edit.textChanged.connect(self.update_preview)
        for rb in [self.rb_after, self.rb_before, self.rb_folder_after,
                   self.rb_folder_before, self.rb_add, self.rb_replace]:
            rb.toggled.connect(self.update_preview)
        self.setStyleSheet(dialog_style(theme))
        self.update_preview()

    def make_num(self, n):
        return str(n).zfill(self.spin_w.value())

    def transform(self, name, idx):
        sep = self.sep_edit.text()
        num = self.make_num(self.spin_s.value() + idx)
        if self.rb_replace.isChecked():
            pat = re.escape(sep) + r'\d+$' if (self.rb_after.isChecked() or self.rb_folder_after.isChecked()) \
                  else r'^\d+' + re.escape(sep)
            name = re.sub(pat, '', name)
        if self.rb_after.isChecked() or self.rb_folder_after.isChecked():
            return f"{name}{sep}{num}"
        else:
            return f"{num}{sep}{name}"

    def update_preview(self):
        result = get_preview_name(self.list_w)
        if result is None:
            self.prev_before.setText("파일 없음"); self.prev_after.setText("─"); return
        n, ext = result
        set_elided(self.prev_before, n + ext)
        set_elided(self.prev_after, self.transform(n, 0) + ext)

    def confirm(self):
        self.result_confirmed = True; self.accept()


class DuplicateDialog(QDialog):
    def __init__(self, parent, theme, current):
        super().__init__(parent)
        self.setWindowTitle("중복 이름 처리 방식")
        self.setFixedSize(300, 200)
        self.result_confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("중복 파일 이름 발생 시 처리 방식"))
        layout.addWidget(make_separator())

        self.rb_over = QRadioButton("덮어쓰기")
        self.rb_num = QRadioButton("뒤에 숫자 붙이기  (예: 파일 (1).txt)")
        self.rb_skip = QRadioButton("건너뛰기")
        grp = QButtonGroup(self)
        for rb in [self.rb_over, self.rb_num, self.rb_skip]:
            grp.addButton(rb); layout.addWidget(rb)

        if current == 'overwrite': self.rb_over.setChecked(True)
        elif current == 'numbering': self.rb_num.setChecked(True)
        else: self.rb_skip.setChecked(True)

        bh = QHBoxLayout()
        btn_ok = QPushButton("확인"); btn_cancel = QPushButton("취소")
        btn_ok.clicked.connect(self.confirm); btn_cancel.clicked.connect(self.reject)
        bh.addWidget(btn_ok); bh.addWidget(btn_cancel)
        layout.addLayout(bh)
        self.setStyleSheet(dialog_style(theme))

    def get_value(self):
        if self.rb_over.isChecked(): return 'overwrite'
        if self.rb_num.isChecked(): return 'numbering'
        return 'skip'

    def confirm(self):
        self.result_confirmed = True; self.accept()


class ThemeDialog(QDialog):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.setWindowTitle("테마 변경")
        self.setFixedSize(400, 460)
        self.parent_window = parent
        self.theme = dict(theme)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("🎨  색상 설정")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.color_items = [
            ('bg',           '배경 색상'),
            ('tab_btn',      '탭 버튼 색상'),
            ('tab_selected', '선택된 탭 색상'),
            ('bottom_btn',   '하단 버튼 색상'),
            ('inactive_btn', '비활성 버튼 색상'),
            ('text',         '글자 색상'),
            ('input_bg',     '입력박스 배경'),
            ('input_text',   '입력박스 글자'),
            ('list_bg',      '리스트박스 배경'),
            ('list_text',    '리스트박스 글자'),
            ('popup_bg',     '팝업창 배경'),
            ('popup_text',   '팝업창 글자'),
        ]

        grid = QGridLayout(); grid.setSpacing(6)
        self.preview_btns = {}
        for row, (key, label) in enumerate(self.color_items):
            lbl = QLabel(label); lbl.setMinimumWidth(140)
            btn = QPushButton()
            btn.setFixedSize(80, 24)
            btn.setStyleSheet(f"background-color: {self.theme[key]}; border: 1px solid #555; border-radius: 4px;")
            btn.clicked.connect(lambda _, k=key: self.pick_color(k))
            self.preview_btns[key] = btn
            grid.addWidget(lbl, row, 0)
            grid.addWidget(btn, row, 1)
        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_dark = QPushButton("🌙 다크 블루")
        btn_system = QPushButton("🖥 시스템 테마")
        btn_reset = QPushButton("↺ 기본값 초기화")
        for b in [btn_dark, btn_system, btn_reset]:
            b.setFixedHeight(30)
            btn_row.addWidget(b)
        btn_dark.clicked.connect(self.apply_dark_blue)
        btn_system.clicked.connect(self.apply_system_theme)
        btn_reset.clicked.connect(self.reset_theme)
        layout.addLayout(btn_row)
        self._refresh_style()

    def _refresh_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.theme['popup_bg']}; }}
            QWidget {{ background-color: {self.theme['popup_bg']}; }}
            QLabel {{ color: {self.theme['popup_text']}; font-weight: bold; }}
            QPushButton {{ background-color: {self.theme['tab_btn']}; color: white;
                border-radius: 4px; padding: 4px; }}
            QPushButton:hover {{ background-color: {self.theme['tab_selected']}; }}
        """)

    def pick_color(self, key):
        dlg = QColorDialog(QColor(self.theme[key]), self)
        dlg.setWindowTitle("색상 선택")
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        from PyQt6.QtWidgets import QDialogButtonBox
        for box in dlg.findChildren(QDialogButtonBox):
            for btn in box.buttons():
                role = box.buttonRole(btn)
                if role == QDialogButtonBox.ButtonRole.AcceptRole: btn.setText("확인")
                elif role == QDialogButtonBox.ButtonRole.RejectRole: btn.setText("취소")
        for btn in dlg.findChildren(QPushButton):
            if "pick" in btn.text().lower(): btn.setText("스크린 컬러 선택")
            elif "add" in btn.text().lower(): btn.setText("색상 추가")
        if dlg.exec():
            color = dlg.selectedColor()
            self.theme[key] = color.name()
            self.preview_btns[key].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555; border-radius: 4px;")
            self.parent_window.apply_theme(self.theme)
            self._refresh_style()

    def reset_theme(self):
        self.theme = dict(DEFAULT_THEME)
        for key, _ in self.color_items:
            self.preview_btns[key].setStyleSheet(
                f"background-color: {self.theme[key]}; border: 1px solid #555; border-radius: 4px;")
        self.parent_window.apply_theme(self.theme)
        self._refresh_style()

    def apply_dark_blue(self):
        self.theme = dict(DEFAULT_THEME)
        for key, _ in self.color_items:
            self.preview_btns[key].setStyleSheet(
                f"background-color: {self.theme[key]}; border: 1px solid #555; border-radius: 4px;")
        self.parent_window.apply_theme(self.theme)
        self._refresh_style()

    def apply_system_theme(self):
        palette = QApplication.palette()
        is_dark = palette.color(palette.ColorRole.Window).lightness() < 128

        if is_dark:
            self.theme.update({
                'bg':          palette.color(palette.ColorRole.Window).name(),
                'tab_btn':     palette.color(palette.ColorRole.Highlight).name(),
                'bottom_btn':  palette.color(palette.ColorRole.Button).name(),
                'inactive_btn': palette.color(palette.ColorRole.Mid).name(),
                'text':        palette.color(palette.ColorRole.WindowText).name(),
                'tab_selected': palette.color(palette.ColorRole.Highlight).name(),
                'pane':        palette.color(palette.ColorRole.Dark).name(),
                'input_bg':    palette.color(palette.ColorRole.Base).name(),
                'input_text':  palette.color(palette.ColorRole.Text).name(),
                'list_bg':     palette.color(palette.ColorRole.Base).name(),
                'list_text':   palette.color(palette.ColorRole.Text).name(),
                'popup_bg':    palette.color(palette.ColorRole.Window).name(),
                'popup_text':  palette.color(palette.ColorRole.WindowText).name(),
            })
        else:
            # 라이트 모드: 가독성 보장을 위해 고정 라이트 테마 적용
            self.theme.update({
                'bg':          '#F0F0F0',
                'tab_btn':     '#0078D4',
                'bottom_btn':  '#0078D4',
                'inactive_btn':'#AAAAAA',
                'text':        '#1A1A1A',
                'tab_selected':'#005A9E',
                'pane':        '#CCCCCC',
                'input_bg':    '#FFFFFF',
                'input_text':  '#1A1A1A',
                'list_bg':     '#FFFFFF',
                'list_text':   '#1A1A1A',
                'popup_bg':    '#F5F5F5',
                'popup_text':  '#1A1A1A',
            })

        for key, _ in self.color_items:
            self.preview_btns[key].setStyleSheet(
                f"background-color: {self.theme[key]}; border: 1px solid #555; border-radius: 4px;")
        self.parent_window.apply_theme(self.theme)
        self._refresh_style()
        for key, _ in self.color_items:
            self.preview_btns[key].setStyleSheet(
                f"background-color: {self.theme[key]}; border: 1px solid #555; border-radius: 4px;")
        self.parent_window.apply_theme(self.theme)
        self._refresh_style()

    def closeEvent(self, e):
        self.parent_window.save_current_config()
        super().closeEvent(e)


class AboutDialog(QDialog):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.setWindowTitle("프로그램 정보")
        self.setFixedSize(340, 200)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 타이틀
        title_lbl = QLabel("프로젝트 문서 관리툴")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #60C5F1; font-size: 15pt; font-weight: bold; border: none;")
        layout.addWidget(title_lbl)

        layout.addWidget(make_separator())

        # 아이콘 + 버전/만든이 행
        mid = QHBoxLayout()
        mid.setSpacing(16)

        # 아이콘
        icon_lbl = QLabel()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "icon.ico")
        from PyQt6.QtGui import QPixmap
        pix = QPixmap(icon_path)
        if not pix.isNull():
            icon_lbl.setPixmap(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
        else:
            icon_lbl.setText("📄")
            icon_lbl.setStyleSheet("font-size: 36pt; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mid.addWidget(icon_lbl)

        # 버전 + 만든이
        info = QVBoxLayout()
        info.setSpacing(6)
        ver_lbl = QLabel(f"버전:  {VERSION}")
        ver_lbl.setStyleSheet(f"color: {theme['text']}; font-size: 9pt; font-weight: normal; border: none;")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        author_lbl = QLabel("만든이:  by 재와니")
        author_lbl.setStyleSheet(f"color: {theme['popup_text']}; font-size: 11pt; font-weight: bold; border: none;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info.addWidget(ver_lbl)
        info.addWidget(author_lbl)
        mid.addLayout(info)
        mid.addStretch()
        layout.addLayout(mid)

        layout.addWidget(make_separator())

        # 버튼 한 행
        bh = QHBoxLayout()
        blog_btn = QPushButton("🔗 블로그 방문하기")
        blog_btn.setFixedHeight(32)
        blog_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://blog.naver.com/akrsodhk/")))
        close_btn = QPushButton("닫기")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.close)
        bh.addWidget(blog_btn); bh.addWidget(close_btn)
        layout.addLayout(bh)

        self.setStyleSheet(dialog_style(theme))


class SearchResultDialog(QDialog):
    """검색 결과 표시 + 파일 열기/경로 복사"""
    def __init__(self, parent, theme, results, editor_path):
        super().__init__(parent)
        self.setWindowTitle("검색 결과")
        self.setMinimumSize(520, 360)
        self.theme = theme
        self.editor_path = editor_path
        # results: list of (filepath, count)
        self.file_paths = [r[0] for r in results]
        total = sum(r[1] for r in results)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel(f"총 {total}개 발견  —  {len(results)}개 파일")
        title.setStyleSheet(f"color: {theme['tab_selected']}; font-size: 10pt; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(make_separator())

        self.list_w = QListWidget()
        self.list_w.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for fp, c in results:
            self.list_w.addItem(f"{os.path.basename(fp)}  ({c}개)  —  {fp}")
        self.list_w.setCurrentRow(0)
        self.list_w.itemDoubleClicked.connect(self._open_selected)
        layout.addWidget(self.list_w)

        btn_h = QHBoxLayout()
        btn_open = QPushButton("📂 열기")
        btn_folder = QPushButton("📁 폴더 이동")
        btn_copy = QPushButton("📋 파일명 복사")
        btn_close = QPushButton("닫기")
        for b in [btn_open, btn_folder, btn_copy, btn_close]:
            b.setFixedHeight(30)
            btn_h.addWidget(b)
        btn_open.clicked.connect(self._open_selected)
        btn_folder.clicked.connect(self._open_folder)
        btn_copy.clicked.connect(self._copy_path)
        btn_close.clicked.connect(self.close)
        layout.addLayout(btn_h)

        self.setStyleSheet(dialog_style(theme))

    def _open_folder(self):
        fp = self._selected_path()
        if not fp: return
        folder = os.path.dirname(fp)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _selected_path(self):
        row = self.list_w.currentRow()
        if row < 0 or row >= len(self.file_paths): return None
        return self.file_paths[row]

    def _open_selected(self):
        fp = self._selected_path()
        if not fp: return
        if self.editor_path and os.path.exists(self.editor_path):
            import subprocess
            try:
                subprocess.Popen([self.editor_path, fp])
                return
            except Exception as e:
                QMessageBox.warning(self, "오류", f"편집기 실행 실패:\n{e}")
        # 기본: 메모장 (Windows) / xdg-open (Linux/Mac)
        import subprocess
        if sys.platform == 'win32':
            subprocess.Popen(['notepad.exe', fp])
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(fp))
              
    def _copy_path(self):
        fp = self._selected_path()
        if not fp: return
        filename = os.path.basename(fp)
        QApplication.clipboard().setText(filename)
        self.parent().set_status(f"📋 복사됨: {filename}")


class EditorDialog(QDialog):
    """편집기 등록 다이얼로그"""
    def __init__(self, parent, theme, current_editor):
        super().__init__(parent)
        self.setWindowTitle("편집기 등록")
        self.setFixedSize(460, 180)
        self.result_confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("문서 열기에 사용할 편집기를 등록합니다"))
        layout.addWidget(QLabel("(비워두면 메모장/기본 앱으로 열림)"))
        layout.addWidget(make_separator())

        row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setText(current_editor)
        self.path_edit.setPlaceholderText("예: C:\\Program Files\\Notepad++\\notepad++.exe")
        btn_browse = QPushButton("찾아보기")
        btn_browse.setFixedWidth(80)
        btn_browse.clicked.connect(self._browse)
        row.addWidget(self.path_edit)
        row.addWidget(btn_browse)
        layout.addLayout(row)

        bh = QHBoxLayout()
        btn_ok = QPushButton("확인")
        btn_clear = QPushButton("초기화 (메모장)")
        btn_cancel = QPushButton("취소")
        btn_ok.clicked.connect(self.confirm)
        btn_clear.clicked.connect(self._clear)
        btn_cancel.clicked.connect(self.reject)
        bh.addWidget(btn_ok); bh.addWidget(btn_clear); bh.addWidget(btn_cancel)
        layout.addLayout(bh)

        self.setStyleSheet(dialog_style(theme))

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "편집기 선택", "",
                                              "실행 파일 (*.exe);;모든 파일 (*)")
        if path: self.path_edit.setText(path)

    def _clear(self):
        self.path_edit.clear()

    def get_value(self):
        return self.path_edit.text().strip()

    def confirm(self):
        self.result_confirmed = True; self.accept()


class FeaturesDialog(QDialog):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.setWindowTitle("주요 기능 안내")
        self.setFixedSize(440, 420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("📌  주요 기능 안내")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(f"""
<div style='font-family:맑은 고딕; font-size:10pt; line-height:1.8; color:{theme["popup_text"]};'>
<b>📂 문서 내용 교체</b><br>
선택한 파일 안의 특정 텍스트를 찾아 일괄 교체합니다.<br>
<span style='color:#FF9966;'>⚠ 주의:</span> <b>md, txt, csv, html</b> 등 텍스트 기반 파일만 수정 가능합니다.<br>
<b>hwp, doc, docx, xlsx</b> 등 바이너리 파일은 내용 수정이 불가합니다.<br><br>
<b>🔢 버전 변환 / 🔤 공백 변환</b><br>
파일명의 언더바를 버전 점(.) 또는 공백으로 일괄 변환합니다.<br><br>
<b>✂ 묶인곳 지우기</b><br>
시작~끝 문자 사이의 텍스트를 삭제합니다. 예) (임시) → 삭제<br><br>
<b>🔢 숫자 남기기/삭제</b><br>
파일명에서 숫자만 남기거나 모두 제거합니다.<br><br>
<b>🔣 자리수 맞추기</b><br>
숫자 부분에 0을 붙여 자리수를 통일합니다. 예) 3 → 003<br><br>
<b>🔖 번호 붙이기</b><br>
파일 이름 앞/뒤 또는 폴더별로 일련번호를 붙입니다.<br><br>
<b>↩ 되돌리기</b><br>
가장 최근 교체 작업 한 번을 이전 상태로 복구합니다.<br><br>
<b>⌨ 단축키</b><br>
<table style='width:100%; border-collapse:collapse;'>
<tr><td style='padding:2px 8px; color:{theme["tab_selected"]};'>Ctrl + Z</td><td>되돌리기 (현재 탭 기준)</td></tr>
<tr><td style='padding:2px 8px; color:{theme["tab_selected"]};'>Ctrl + F</td><td>찾기 (문서 내용 탭)</td></tr>
<tr><td style='padding:2px 8px; color:{theme["tab_selected"]};'>Ctrl + R</td><td>교체 실행 (현재 탭 기준)</td></tr>
<tr><td style='padding:2px 8px; color:{theme["tab_selected"]};'>Ctrl + D</td><td>목록 초기화 (현재 탭 기준)</td></tr>
<tr><td style='padding:2px 8px; color:{theme["tab_selected"]};'>Ctrl + A</td><td>목록 전체 선택</td></tr>
<tr><td style='padding:2px 8px; color:{theme["tab_selected"]};'>Delete</td><td>선택 항목 삭제</td></tr>
</table>
</div>""")
        text.setStyleSheet(f"QTextEdit {{ background-color: {theme['input_bg']}; border: 1px solid {theme['tab_btn']}; border-radius: 4px; padding: 8px; color: {theme['popup_text']}; }}")
        layout.addWidget(text)

        close_btn = QPushButton("닫기")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setStyleSheet(dialog_style(theme))


class SProjectManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'프로젝트 문서 관리툴 {VERSION}')
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.setWindowIcon(QIcon(os.path.join(base_path, "icon.ico")))
        self.setFixedSize(470, 560)
        self.undo_stack_content = []
        self.undo_stack_rename = []
        self.config = load_config()
        self.theme = self.config['theme']
        self.duplicate_mode = self.config['duplicate']
        self.editor_path = self.config.get('editor', '')
        self.init_ui()
        self.apply_theme(self.theme)
        self._setup_shortcuts()

    def init_ui(self):
        menubar = self.menuBar()

        menu_content = menubar.addMenu("📄 문서 내용")
        act = QAction("📂 폴더 추가 (전체 탭)", self)
        act.triggered.connect(lambda: self.add_folder_all())
        menu_content.addAction(act)

        menu_rename = menubar.addMenu("📝 파일 이름")
        a1 = QAction("📂 폴더 추가 (전체 탭)", self)
        a1.triggered.connect(lambda: self.add_folder_all())
        menu_rename.addAction(a1)
        menu_rename.addSeparator()
        a2 = QAction("🔢 버전 변환  (_ → .)", self); a2.triggered.connect(self.auto_version_convert)
        a3 = QAction("🔤 공백 변환  (_ → 공백)", self); a3.triggered.connect(self.auto_space_convert)
        menu_rename.addAction(a2); menu_rename.addAction(a3)
        menu_rename.addSeparator()
        a4 = QAction("✂  묶인곳 지우기", self); a4.triggered.connect(self.open_remove_bracket)
        a5 = QAction("🔢 숫자 남기기/삭제", self); a5.triggered.connect(self.open_number_filter)
        a6 = QAction("🔣 자리수 맞추기", self); a6.triggered.connect(self.open_pad_number)
        a7 = QAction("🔖 번호 붙이기", self); a7.triggered.connect(self.open_add_number)
        menu_rename.addAction(a4); menu_rename.addAction(a5)
        menu_rename.addAction(a6); menu_rename.addAction(a7)
        menu_rename.addSeparator()
        a8 = QAction("⚙  중복 이름 처리 방식", self); a8.triggered.connect(self.open_duplicate_dialog)
        menu_rename.addAction(a8)

        menu_setting = menubar.addMenu("⚙ 설정")
        at = QAction("🎨 테마 변경", self); at.triggered.connect(self.open_theme_dialog)
        ae = QAction("✏ 편집기 등록", self); ae.triggered.connect(self.open_editor_dialog)
        af = QAction("📌 주요 기능", self); af.triggered.connect(self.open_features_dialog)
        aa = QAction("…관하여", self); aa.triggered.connect(self.open_about_dialog)
        menu_setting.addAction(at); menu_setting.addAction(ae); menu_setting.addSeparator()
        menu_setting.addAction(af); menu_setting.addAction(aa)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)

        self.tabs = QTabWidget()
        self.list1, self.list2 = FileListWidget(), FileListWidget()
        tab1, tab2 = QWidget(), QWidget()
        self.init_tab_content(tab1, self.list1)
        self.init_tab_rename(tab2, self.list2)
        self.tabs.addTab(tab1, "문서 내용 교체")
        self.tabs.addTab(tab2, "파일 이름 교체")
        main_layout.addWidget(self.tabs)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)

    def _setup_shortcuts(self):
        from PyQt6.QtGui import QKeySequence, QShortcut

        def sc(key, fn): QShortcut(QKeySequence(key), self).activated.connect(fn)

        sc("Ctrl+Z", self._shortcut_undo)
        sc("Ctrl+F", self._shortcut_find)
        sc("Ctrl+R", self._shortcut_replace)
        sc("Ctrl+D", self._shortcut_clear)
        sc("Ctrl+A", self._shortcut_select_all)

    def _current_tab(self):
        return self.tabs.currentIndex()  # 0=문서내용, 1=파일이름

    def _shortcut_undo(self):
        if self._current_tab() == 0: self.undo_action(self.list1, 'content')
        else: self.undo_action(self.list2, 'rename')

    def _shortcut_find(self):
        if self._current_tab() == 0: self.run_find(self.list1)

    def _shortcut_replace(self):
        if self._current_tab() == 0: self.run_replace(self.list1)
        else: self.run_rename(self.list2)

    def _shortcut_clear(self):
        if self._current_tab() == 0: self.list1.clear()
        else: self.list2.clear()

    def _shortcut_select_all(self):
        if self._current_tab() == 0: self.list1.selectAll()
        else: self.list2.selectAll()

    def set_status(self, msg):
        self.status_bar.showMessage(msg, 4000)

    def get_button_style(self):
        t = self.theme
        return f"""
            QPushButton {{ background-color: {t['bottom_btn']}; color: {t['text']};
                font-weight: bold; border: 1px solid #005174; border-radius: 4px; padding: 6px; }}
            QPushButton:hover {{ background-color: {t['tab_selected']}; }}
            QPushButton:disabled {{ background-color: {t['inactive_btn']}; }}
        """

    def apply_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {theme['bg']}; }}
            QWidget {{ background-color: {theme['bg']}; }}
            QLabel {{ color: {theme['text']}; font-weight: bold; }}
            QLineEdit {{ background-color: {theme['input_bg']}; color: {theme['input_text']};
                border: 1px solid {theme['tab_btn']}; border-radius: 4px; padding: 4px; }}
            QTabWidget::pane {{ border: 2px solid {theme['pane']}; background-color: {theme['pane']}; }}
            QTabBar::tab {{ background: {theme['inactive_btn']}; color: {theme['text']};
                padding: 8px 15px; border: 2px solid {theme['pane']}; }}
            QTabBar::tab:hover {{ background: {theme['tab_selected']}; color: #ffffff; }}
            QTabBar::tab:selected {{ background: {theme['tab_btn']}; color: #ffffff; font-weight: bold; }}
            QMenuBar {{ background-color: {theme['bg']}; color: {theme['text']}; }}
            QMenuBar::item:selected {{ background-color: {theme['tab_btn']}; }}
            QMenu {{ background-color: {theme['input_bg']}; color: {theme['text']};
                border: 1px solid {theme['tab_btn']}; }}
            QMenu::item {{ padding: 6px 20px 6px 10px; }}
            QMenu::item:selected {{ background-color: {theme['tab_btn']}; }}
            QListWidget {{ background-color: {theme['list_bg']}; color: {theme['list_text']};
                border: 2px solid {theme['tab_btn']}; border-radius: 4px; }}
            QStatusBar {{ background-color: {theme['bg']}; color: {theme['text']}; }}
            QMessageBox {{ background-color: {theme['popup_bg']}; }}
            QMessageBox QLabel {{ color: {theme['popup_text']}; }}
            QMessageBox QPushButton {{ background-color: {theme['tab_btn']}; color: white; }}
        """)

    def save_current_config(self):
        self.config['theme'] = self.theme
        self.config['duplicate'] = self.duplicate_mode
        self.config['editor'] = self.editor_path
        save_config(self.config)

    def add_control_buttons(self, layout, list_w):
        h_box = QHBoxLayout()
        btn_add = QPushButton("📂 폴더 추가"); btn_clear = QPushButton("🗑 목록 초기화")
        btn_add.setStyleSheet(self.get_button_style())
        btn_clear.setStyleSheet(self.get_button_style())
        btn_add.clicked.connect(lambda: self.add_folder(list_w))
        btn_clear.clicked.connect(list_w.clear)
        h_box.addWidget(btn_add); h_box.addWidget(btn_clear)
        layout.addLayout(h_box)

    def init_tab_content(self, parent, list_w):
        layout = QVBoxLayout(parent); layout.setSpacing(6)
        self.add_control_buttons(layout, list_w)
        self.label_file_count1 = QLabel()
        layout.addWidget(self.label_file_count1)
        layout.addWidget(list_w)

        self.update_file_count_label(self.label_file_count1, list_w)
        list_w.model().rowsInserted.connect(lambda: self.update_file_count_label(self.label_file_count1, list_w))
        list_w.model().rowsRemoved.connect(lambda: self.update_file_count_label(self.label_file_count1, list_w))
        self.old_t = QLineEdit(); self.old_t.setPlaceholderText("찾을 내용")
        self.new_t = QLineEdit(); self.new_t.setPlaceholderText("바꿀 내용")
        layout.addWidget(self.old_t); layout.addWidget(self.new_t)
        btn_h = QHBoxLayout()
        btn_find = QPushButton("🔍 찾기")
        btn_rep = QPushButton("✏ 내용 교체")
        btn_undo = QPushButton("↩ 되돌리기")
        for b in [btn_find, btn_rep, btn_undo]: b.setStyleSheet(self.get_button_style())
        btn_find.clicked.connect(lambda: self.run_find(list_w))
        btn_rep.clicked.connect(lambda: self.run_replace(list_w))
        btn_undo.clicked.connect(lambda: self.undo_action(list_w, 'content'))
        btn_h.addWidget(btn_find); btn_h.addWidget(btn_rep); btn_h.addWidget(btn_undo)
        layout.addLayout(btn_h)

    def update_file_count_label(self, label, list_w):
        label.setText(f"▣ 대상 파일 목록: {list_w.count()}개")

    def init_tab_rename(self, parent, list_w):
        layout = QVBoxLayout(parent); layout.setSpacing(6)
        self.add_control_buttons(layout, list_w)

        self.label_file_count2 = QLabel()
        layout.addWidget(self.label_file_count2)
        layout.addWidget(list_w)

        self.update_file_count_label(self.label_file_count2, list_w)
        list_w.model().rowsInserted.connect(lambda: self.update_file_count_label(self.label_file_count2, list_w))
        list_w.model().rowsRemoved.connect(lambda: self.update_file_count_label(self.label_file_count2, list_w))
        self.rename_old = QLineEdit(); self.rename_old.setPlaceholderText("기존 문자")
        self.rename_new = QLineEdit(); self.rename_new.setPlaceholderText("변경 문자")
        layout.addWidget(self.rename_old); layout.addWidget(self.rename_new)
        btn_h = QHBoxLayout()
        btn_ren = QPushButton("✏ 이름 교체"); btn_undo = QPushButton("↩ 되돌리기")
        btn_ren.setStyleSheet(self.get_button_style())
        btn_undo.setStyleSheet(self.get_button_style())
        btn_ren.clicked.connect(lambda: self.run_rename(list_w))
        btn_undo.clicked.connect(lambda: self.undo_action(list_w, 'rename'))
        btn_h.addWidget(btn_ren); btn_h.addWidget(btn_undo)
        layout.addLayout(btn_h)

    def add_folder(self, list_w):    
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            self.set_status("📂 파일 목록 불러오는 중...")
            worker = FolderScanWorker(folder)
            worker.path_found.connect(list_w.add_path)
            worker.finished.connect(lambda: self.set_status(f"✅ 불러오기 완료"))
            worker.start()
            self._workers = getattr(self, '_workers', [])
            self._workers.append(worker)

    def add_folder_all(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            self.set_status("📂 파일 목록 불러오는 중...")
            worker = FolderScanWorker(folder)
            worker.path_found.connect(lambda p: (self.list1.add_path(p), self.list2.add_path(p)))
            worker.finished.connect(lambda: self.set_status("✅ 불러오기 완료"))
            worker.start()
            self._workers = getattr(self, '_workers', [])
            self._workers.append(worker)

    def check_list_empty(self, list_w):
        if list_w.count() == 0:
            QMessageBox.warning(self, "알림", "변경할 파일이 없습니다.\n파일을 추가해 주세요.")
            return True
        return False

    def safe_rename(self, src, dst):
        if src == dst: return dst
        if not os.path.exists(dst):
            os.rename(src, dst); return dst
        mode = self.duplicate_mode
        if mode == 'overwrite':
            os.replace(src, dst); return dst
        elif mode == 'numbering':
            base, ext = os.path.splitext(dst)
            i = 1
            while os.path.exists(f"{base} ({i}){ext}"): i += 1
            new_dst = f"{base} ({i}){ext}"
            os.rename(src, new_dst); return new_dst
        else:
            return None

    def run_find(self, list_w):
        if self.check_list_empty(list_w): 
            return

        target = self.old_t.text().strip()
        if not target:
            QMessageBox.warning(self, "알림", "찾을 내용을 입력해주세요.")
            return

        # 실제 전체 경로 리스트 만들기
        file_list = []
        for i in range(list_w.count()):
            item = list_w.item(i)
            fp = item.data(Qt.ItemDataRole.UserRole)   # ← 핵심 수정!
            if fp and os.path.exists(fp):
                file_list.append(fp)

        if not file_list:
            QMessageBox.warning(self, "알림", "유효한 파일이 없습니다.")
            return

        self.set_status("🔍 파일 내용 검색 중...")
        self.start_search_with_loading(file_list, target)

    def start_search_with_loading(self, file_list, keyword):
        self.loading_dialog = LoadingDialog(self, self.theme)
        self.loading_dialog.label.setText("파일 내용 검색 중...")
        self.loading_dialog.show()

        self.worker = FileSearchWorker(file_list, keyword)
        self.worker.progress.connect(self.loading_dialog.set_progress)
        self.worker.finished.connect(self._on_search_finished)
        self.worker.start()

    def _on_search_finished(self, results):
        self.loading_dialog.close()

        if not results:
            QMessageBox.information(self, "검색 결과", "해당 내용을 찾을 수 없습니다.")
            return

        dlg = SearchResultDialog(self, self.theme, results, self.editor_path)
        dlg.exec()

    def run_replace(self, list_w):
        if self.check_list_empty(list_w): return
        self.undo_stack_content = []; count = 0
        for i in range(list_w.count()):
            item = list_w.item(i)
            # .text() 대신 .data(Qt.ItemDataRole.UserRole) 사용
            fp = item.data(Qt.ItemDataRole.UserRole) 
            if os.path.exists(fp):
                try:
                    with open(fp, 'r', encoding='utf-8') as f: content = f.read()
                    if self.old_t.text() in content:
                        self.undo_stack_content.append({'path': fp, 'content': content})
                        with open(fp, 'w', encoding='utf-8') as f:
                            f.write(content.replace(self.old_t.text(), self.new_t.text()))
                        count += 1
                except: continue
        QMessageBox.information(self, "교체 완료", f"{count}개의 파일 내용이 교체되었습니다.")
        self.set_status(f"✏ 내용 교체 완료 — {count}개 파일")

    def run_rename(self, list_w):
        if self.check_list_empty(list_w): 
            return

        self.undo_stack_rename = []
        count = 0
        old_text = self.rename_old.text()
        new_text = self.rename_new.text()

        if not old_text:
            QMessageBox.warning(self, "알림", "기존 문자를 입력해주세요.")
            return

        for i in range(list_w.count()):
            item = list_w.item(i)
            fp = item.data(Qt.ItemDataRole.UserRole)   # 실제 전체 경로

            if not os.path.exists(fp):
                continue

            dir_n, file_n = os.path.split(fp)

            if old_text in file_n:
                new_name = file_n.replace(old_text, new_text)
                new_fp = os.path.join(dir_n, new_name)

                # 실제 파일 이름 변경
                result = self.safe_rename(fp, new_fp)
                if result:
                    # Undo 스택에 저장 (되돌릴 때 필요)
                    self.undo_stack_rename.append({
                        'old': result,      # 바뀐 후 경로
                        'new': fp           # 원래 경로
                    })

                    # 리스트 위젯 업데이트
                    item.setText(os.path.basename(result))
                    item.setData(Qt.ItemDataRole.UserRole, result)
                    count += 1

        if count == 0:
            QMessageBox.information(self, "알림", "변경 대상이 없습니다.")
        else:
            QMessageBox.information(self, "교체 완료", f"{count}개의 파일 이름이 수정되었습니다.")
            self.set_status(f"✏ 이름 교체 완료 — {count}개 파일")

    def auto_version_convert(self):
        list_w = self.list2
        if self.check_list_empty(list_w): return
        self.undo_stack_rename = []
        count = 0

        for i in range(list_w.count()):
            item = list_w.item(i)
            fp = item.data(Qt.ItemDataRole.UserRole)   # ← 핵심 수정!
            
            if not os.path.exists(fp):
                continue
                
            dir_n, file_n = os.path.split(fp)
            new_name = re.sub(r'([vV]\d+)_(\d+)', r'\1.\2', file_n)
            
            if new_name != file_n:
                new_fp = os.path.join(dir_n, new_name)
                result = self.safe_rename(fp, new_fp)
                if result:
                    self.undo_stack_rename.append({'old': result, 'new': fp})
                    item.setText(os.path.basename(result))      # 표시용 이름 업데이트
                    item.setData(Qt.ItemDataRole.UserRole, result)  # 실제 경로 업데이트
                    count += 1

        if count > 0:
            QMessageBox.information(self, "변환 완료", f"{count}개의 파일 이름이 수정되었습니다.")
            self.set_status(f"🔢 버전 변환 완료 — {count}개 파일")
        else:
            QMessageBox.information(self, "알림", "변환할 버전 패턴(vX_X)이 없습니다.")

    def auto_space_convert(self):
        list_w = self.list2
        if self.check_list_empty(list_w): return
        self.undo_stack_rename = []
        count = 0

        for i in range(list_w.count()):
            item = list_w.item(i)
            fp = item.data(Qt.ItemDataRole.UserRole)   # ← 핵심 수정!
            
            if not os.path.exists(fp):
                continue
                
            dir_n, file_n = os.path.split(fp)
            name, ext = os.path.splitext(file_n)
            new_name = name.replace('_', ' ') + ext
            
            if new_name != file_n:
                new_fp = os.path.join(dir_n, new_name)
                result = self.safe_rename(fp, new_fp)
                if result:
                    self.undo_stack_rename.append({'old': result, 'new': fp})
                    item.setText(os.path.basename(result))      # 표시용 이름 업데이트
                    item.setData(Qt.ItemDataRole.UserRole, result)  # 실제 경로 업데이트
                    count += 1

        if count > 0:
            QMessageBox.information(self, "변환 완료", f"{count}개의 파일 이름이 수정되었습니다.")
            self.set_status(f"🔤 공백 변환 완료 — {count}개 파일")
        else:
            QMessageBox.information(self, "알림", "변환할 언더바(_)가 없습니다.")

    def _apply_name_transform(self, transform_fn):
        list_w = self.list2
        self.undo_stack_rename = []; count = 0
        for i in range(list_w.count()):
            fp = list_w.item(i).text()
            if os.path.exists(fp):
                dir_n, file_n = os.path.split(fp)
                name, ext = os.path.splitext(file_n)
                new_name = transform_fn(name) + ext
                if new_name != file_n:
                    new_fp = os.path.join(dir_n, new_name)
                    result = self.safe_rename(fp, new_fp)
                    if result:
                        self.undo_stack_rename.append({'old': result, 'new': fp})
                        list_w.item(i).setText(result); count += 1
        QMessageBox.information(self, "변환 완료", f"{count}개의 파일 이름이 수정되었습니다.")
        self.set_status(f"✅ 변환 완료 — {count}개 파일")

    def open_remove_bracket(self):
        if self.check_list_empty(self.list2): return
        dlg = RemoveBracketDialog(self, self.theme, self.list2)
        if dlg.exec() and dlg.result_confirmed:
            self._apply_name_transform(dlg.transform)

    def open_number_filter(self):
        if self.check_list_empty(self.list2): return
        dlg = NumberFilterDialog(self, self.theme, self.list2)
        if dlg.exec() and dlg.result_confirmed:
            self._apply_name_transform(dlg.transform)

    def open_pad_number(self):
        if self.check_list_empty(self.list2): return
        dlg = PadNumberDialog(self, self.theme, self.list2)
        if dlg.exec() and dlg.result_confirmed:
            self._apply_name_transform(dlg.transform)

    def open_add_number(self):
        if self.check_list_empty(self.list2): return
        dlg = AddNumberDialog(self, self.theme, self.list2)
        if not (dlg.exec() and dlg.result_confirmed): return
        list_w = self.list2
        self.undo_stack_rename = []; count = 0
        folder_counters = {}
        for i in range(list_w.count()):
            fp = list_w.item(i).text()
            if not os.path.exists(fp): continue
            dir_n, file_n = os.path.split(fp)
            name, ext = os.path.splitext(file_n)
            is_folder_mode = dlg.rb_folder_after.isChecked() or dlg.rb_folder_before.isChecked()
            if is_folder_mode:
                if dir_n not in folder_counters:
                    folder_counters[dir_n] = dlg.spin_s.value()
                idx = folder_counters[dir_n] - dlg.spin_s.value()
                folder_counters[dir_n] += 1
            else:
                idx = i
            new_name = dlg.transform(name, idx) + ext
            if new_name != file_n:
                new_fp = os.path.join(dir_n, new_name)
                result = self.safe_rename(fp, new_fp)
                if result:
                    self.undo_stack_rename.append({'old': result, 'new': fp})
                    list_w.item(i).setText(result); count += 1
        QMessageBox.information(self, "변환 완료", f"{count}개의 파일 이름이 수정되었습니다.")
        self.set_status(f"🔖 번호 붙이기 완료 — {count}개 파일")

    def open_duplicate_dialog(self):
        dlg = DuplicateDialog(self, self.theme, self.duplicate_mode)
        if dlg.exec() and dlg.result_confirmed:
            self.duplicate_mode = dlg.get_value()
            self.save_current_config()

    def undo_action(self, list_w, mode):
        if mode == 'content':
            if not self.undo_stack_content:
                QMessageBox.warning(self, "알림", "되돌릴 작업이 없습니다.")
                return
            for item in self.undo_stack_content:
                try:
                    with open(item['path'], 'w', encoding='utf-8') as f:
                        f.write(item['content'])
                except:
                    pass
            self.undo_stack_content = []
            QMessageBox.information(self, "복구 완료", "문서 내용이 이전 상태로 복구되었습니다.")

        else:  # === 파일 이름 되돌리기 ===
            if not self.undo_stack_rename:
                QMessageBox.warning(self, "알림", "되돌릴 작업이 없습니다.")
                return

            restored = 0
            for entry in reversed(self.undo_stack_rename):   # 역순으로 복구
                old_path = entry['old']   # 현재 파일 경로 (바뀐 이름)
                original_path = entry['new']  # 원래 파일 경로

                if os.path.exists(old_path):
                    try:
                        os.rename(old_path, original_path)

                        # 리스트에서 해당 아이템 찾아 완전 복구
                        for i in range(list_w.count()):
                            item = list_w.item(i)
                            if item.data(Qt.ItemDataRole.UserRole) == old_path:
                                item.setText(os.path.basename(original_path))
                                item.setData(Qt.ItemDataRole.UserRole, original_path)
                                restored += 1
                                break
                    except Exception as e:
                        print(f"Undo error: {e}")

            self.undo_stack_rename = []
            QMessageBox.information(self, "복구 완료", 
                                  f"{restored}개의 파일 이름이 이전 상태로 복구되었습니다.")
            self.set_status(f"↩ 되돌리기 완료 — {restored}개 파일")

        # 파일 개수 라벨 업데이트
        if mode == 'rename':
            self.update_file_count_label(self.label_file_count2, list_w)
        else:
            self.update_file_count_label(self.label_file_count1, list_w)

    def open_theme_dialog(self):   ThemeDialog(self, self.theme).exec()
    def open_about_dialog(self):   AboutDialog(self, self.theme).exec()
    def open_features_dialog(self): FeaturesDialog(self, self.theme).exec()

    def open_editor_dialog(self):
        dlg = EditorDialog(self, self.theme, self.editor_path)
        if dlg.exec() and dlg.result_confirmed:
            self.editor_path = dlg.get_value()
            self.save_current_config()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SProjectManager()
    ex.show()
    sys.exit(app.exec())