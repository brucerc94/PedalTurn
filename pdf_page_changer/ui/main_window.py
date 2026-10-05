from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow, QPushButton, QSplitter, QStatusBar, QVBoxLayout, QWidget

from ..core.models import ScoreItem
from .score_viewer import ScoreViewer


class MainWindow(QMainWindow):
    add_pdf_requested = Signal()
    save_project_requested = Signal()
    load_project_requested = Signal()
    remove_pdf_requested = Signal()
    previous_page_requested = Signal()
    next_page_requested = Signal()
    add_video_requested = Signal()
    toggle_video_requested = Signal()
    settings_requested = Signal()
    pdf_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Page Changer Piano")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self._build_menu()
        self._build_ui()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Archivo")
        file_menu.addAction(self._action("Agregar PDF", self.add_pdf_requested.emit))
        file_menu.addAction(self._action("Guardar lista", self.save_project_requested.emit))
        file_menu.addAction(self._action("Cargar lista", self.load_project_requested.emit))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Salir", self.close))

        view_menu = self.menuBar().addMenu("Ver")
        view_menu.addAction(self._action("Página anterior", self.previous_page_requested.emit))
        view_menu.addAction(self._action("Página siguiente", self.next_page_requested.emit))

        settings_menu = self.menuBar().addMenu("Configuración")
        settings_menu.addAction(self._action("Preferencias", self.settings_requested.emit))

    @staticmethod
    def _action(text: str, slot) -> QAction:
        action = QAction(text)
        action.triggered.connect(lambda _checked=False: slot())
        return action

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(300)
        sidebar.setMaximumWidth(380)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(9)

        title = QLabel("PDF Page Changer")
        title.setObjectName("appTitle")
        sidebar_layout.addWidget(title)
        subtitle = QLabel("Visor de partituras · control MIDI")
        subtitle.setObjectName("statusLabel")
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(10)

        sidebar_layout.addWidget(self._section_label("ARCHIVOS"))
        sidebar_layout.addWidget(self._button("Agregar PDF", self.add_pdf_requested.emit, accent=True))
        sidebar_layout.addWidget(self._button("Guardar lista", self.save_project_requested.emit))
        sidebar_layout.addWidget(self._button("Cargar lista", self.load_project_requested.emit))
        sidebar_layout.addWidget(self._button("Eliminar PDF", self.remove_pdf_requested.emit, danger=True))
        sidebar_layout.addSpacing(8)

        sidebar_layout.addWidget(self._section_label("NAVEGACIÓN"))
        nav_row = QHBoxLayout()
        nav_row.addWidget(self._button("← Anterior", self.previous_page_requested.emit))
        nav_row.addWidget(self._button("Siguiente →", self.next_page_requested.emit))
        sidebar_layout.addLayout(nav_row)
        sidebar_layout.addSpacing(8)

        sidebar_layout.addWidget(self._section_label("MULTIMEDIA"))
        sidebar_layout.addWidget(self._button("Agregar video", self.add_video_requested.emit))
        sidebar_layout.addWidget(self._button("Mostrar / ocultar video", self.toggle_video_requested.emit))
        sidebar_layout.addSpacing(8)

        sidebar_layout.addWidget(self._section_label("CONFIGURACIÓN"))
        sidebar_layout.addWidget(self._button("Preferencias", self.settings_requested.emit))
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self._section_label("COLA DE PARTITURAS"))

        self.playlist = QListWidget()
        self.playlist.currentRowChanged.connect(self.pdf_selected.emit)
        sidebar_layout.addWidget(self.playlist, 1)

        viewer = QWidget()
        viewer_layout = QVBoxLayout(viewer)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)

        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 10)
        self.score_title = QLabel("Sin PDF cargado")
        self.score_title.setObjectName("scoreTitle")
        self.page_info = QLabel("")
        self.page_info.setObjectName("pageInfo")
        header_layout.addWidget(self.score_title)
        header_layout.addWidget(self.page_info)

        self.score_viewer = ScoreViewer()
        controls = QHBoxLayout()
        controls.setContentsMargins(18, 0, 18, 12)
        controls.addStretch()
        zoom_out = QPushButton("−")
        zoom_out.setFixedWidth(42)
        zoom_out.clicked.connect(self.score_viewer.zoom_out)
        fit = QPushButton("Ajustar")
        fit.clicked.connect(self.score_viewer.reset_zoom)
        zoom_in = QPushButton("+")
        zoom_in.setFixedWidth(42)
        zoom_in.clicked.connect(self.score_viewer.zoom_in)
        controls.addWidget(zoom_out)
        controls.addWidget(fit)
        controls.addWidget(zoom_in)

        viewer_layout.addWidget(header)
        viewer_layout.addWidget(self.score_viewer, 1)
        viewer_layout.addLayout(controls)

        splitter.addWidget(sidebar)
        splitter.addWidget(viewer)
        splitter.setSizes([320, 1120])
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.addWidget(splitter)
        self.setStatusBar(QStatusBar())
        self._install_shortcuts()

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    @staticmethod
    def _button(text: str, slot, accent: bool = False, danger: bool = False) -> QPushButton:
        button = QPushButton(text)
        if accent:
            button.setObjectName("accentButton")
        elif danger:
            button.setObjectName("dangerButton")
        button.clicked.connect(lambda _checked=False: slot())
        return button

    def _install_shortcuts(self) -> None:
        next_action = QAction(self)
        next_action.setShortcut(QKeySequence(Qt.Key.Key_Right))
        next_action.triggered.connect(lambda: self.next_page_requested.emit())
        self.addAction(next_action)
        previous_action = QAction(self)
        previous_action.setShortcut(QKeySequence(Qt.Key.Key_Left))
        previous_action.triggered.connect(lambda: self.previous_page_requested.emit())
        self.addAction(previous_action)

    def set_playlist(self, items: list[ScoreItem], current_index: int) -> None:
        self.playlist.blockSignals(True)
        self.playlist.clear()
        for item in items:
            label = item.display_name if item.pdf_path.exists() else f"⚠ {item.display_name}"
            self.playlist.addItem(label)
        self.playlist.setCurrentRow(current_index if items else -1)
        self.playlist.blockSignals(False)

    def set_score_info(self, item: ScoreItem | None, current_page: int, page_count: int) -> None:
        if item is None:
            self.score_title.setText("Sin PDF cargado")
            self.page_info.setText("")
            return
        self.score_title.setText(item.display_name)
        if page_count:
            end_page = min(current_page + 2, page_count)
            self.page_info.setText(f"Páginas {current_page + 1}–{end_page} de {page_count}")
        else:
            self.page_info.setText("PDF no disponible")

    def set_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def open_pdf_dialog(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar partitura", "", "Partituras PDF (*.pdf)")
        return Path(path) if path else None

    def save_project_dialog(self) -> Path | None:
        path, _ = QFileDialog.getSaveFileName(self, "Guardar lista", "", "Proyecto VDP (*.vdp)")
        return Path(path) if path else None

    def load_project_dialog(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar lista", "", "Proyecto VDP (*.vdp)")
        return Path(path) if path else None

    def choose_video_dialog(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar video", "", "Videos (*.mp4 *.avi *.mov *.mkv *.webm)")
        return Path(path) if path else None
