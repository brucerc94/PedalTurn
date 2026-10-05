from __future__ import annotations

from PySide6.QtCore import QPoint, Signal
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QMainWindow


class VideoWindow(QMainWindow):
    closed = Signal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vídeo — PDF Page Changer Piano")
        self.setMinimumSize(640, 360)

        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(
            QVideoWidget.AspectRatioMode.KeepAspectRatio
        )
        self.setCentralWidget(self.video_widget)

    def closeEvent(self, event) -> None:
        self.closed.emit(self.pos())
        event.accept()
