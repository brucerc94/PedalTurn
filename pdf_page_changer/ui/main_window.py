from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog, QMainWindow, QVBoxLayout, QWidget

from ..core.models import ScoreItem
from .floating_controls import FloatingControls
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
        self.setWindowTitle("PedalTurn")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)

        self._build_ui()
        self._install_shortcuts()
        self._build_connections()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.score_viewer = ScoreViewer()
        layout.addWidget(self.score_viewer, 1)

        self.controls = FloatingControls(root)
        self.controls.bind_viewer(self.score_viewer)
        self.controls.show_controls()

        self.statusBar().setVisible(False)
        self.menuBar().setVisible(False)
        self._position_controls()

    def _build_connections(self) -> None:
        connections = (
            (self.controls.add_pdf_requested, self.add_pdf_requested),
            (self.controls.save_project_requested, self.save_project_requested),
            (self.controls.load_project_requested, self.load_project_requested),
            (self.controls.remove_pdf_requested, self.remove_pdf_requested),
            (self.controls.previous_page_requested, self.previous_page_requested),
            (self.controls.next_page_requested, self.next_page_requested),
            (self.controls.add_video_requested, self.add_video_requested),
            (self.controls.toggle_video_requested, self.toggle_video_requested),
            (self.controls.settings_requested, self.settings_requested),
            (self.controls.pdf_selected, self.pdf_selected),
        )
        for source, target in connections:
            source.connect(target)

    def _install_shortcuts(self) -> None:
        shortcuts = (
            (Qt.Key.Key_Right, self.next_page_requested.emit),
            (Qt.Key.Key_Left, self.previous_page_requested.emit),
            (Qt.Key.Key_Escape, self.controls.show_controls),
        )
        for key, slot in shortcuts:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(
                lambda _checked=False, callback=slot: callback()
            )
            self.addAction(action)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_controls()

    def _position_controls(self) -> None:
        margin = 18
        size = self.controls.sizeHint()
        width = min(
            size.width(),
            max(260, self.centralWidget().width() - margin * 2),
        )
        self.controls.setGeometry(
            margin,
            margin,
            width,
            size.height(),
        )

    def set_playlist(self, items: list[ScoreItem], current_index: int) -> None:
        self.controls.set_playlist(items, current_index)

    def set_score_info(
        self,
        item: ScoreItem | None,
        current_page: int,
        page_count: int,
    ) -> None:
        if item is None:
            self.controls.set_page_info("")
            return

        if page_count:
            end_page = min(current_page + 2, page_count)
            self.controls.set_page_info(
                f"{item.display_name}  ·  "
                f"{current_page + 1}–{end_page}/{page_count}"
            )
        else:
            self.controls.set_page_info(
                f"{item.display_name}  ·  PDF unavailable"
            )

    def set_status(self, text: str) -> None:
        self.controls.set_status(text)
        self.controls.show_controls()

    def open_pdf_dialog(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF Score",
            "",
            "PDF Scores (*.pdf)",
        )
        return Path(path) if path else None

    def save_project_dialog(self) -> Path | None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save VDP Project",
            "",
            "VDP Projects (*.vdp)",
        )
        return Path(path) if path else None

    def load_project_dialog(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load VDP Project",
            "",
            "VDP Projects (*.vdp)",
        )
        return Path(path) if path else None

    def choose_video_dialog(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Videos (*.mp4 *.avi *.mov *.mkv *.webm)",
        )
        return Path(path) if path else None
