from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QMainWindow


class VideoWindow(QMainWindow):
    closed = Signal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video — PedalTurn")
        self.setMinimumSize(640, 360)
        widget = QVideoWidget()
        widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.setCentralWidget(widget)
        self.video_widget = widget

    def closeEvent(self, event) -> None:
        self.closed.emit(self.pos())
        event.accept()
