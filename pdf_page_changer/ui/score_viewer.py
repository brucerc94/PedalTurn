from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ..services.pdf_service import PageImage


class ScoreViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self._pages: list[QPixmap] = []
        self._page_gap = 14
        self._zoom = 1.0

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_pages(self, pages: list[PageImage]) -> None:
        self._pages = [self._to_pixmap(page) for page in pages]
        self.update()

    def clear(self) -> None:
        self._pages.clear()
        self.update()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self.update()

    def zoom_in(self) -> None:
        self._zoom = min(2.5, self._zoom + 0.1)
        self.update()

    def zoom_out(self) -> None:
        self._zoom = max(0.5, self._zoom - 0.1)
        self.update()

    @staticmethod
    def _to_pixmap(page: PageImage) -> QPixmap:
        image = QImage(
            page.pixels,
            page.width,
            page.height,
            page.width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        return QPixmap.fromImage(image)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        if not self._pages:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Add a PDF score to get started",
            )
            return

        available = self.rect().adjusted(18, 18, -18, -18)
        gap = self._page_gap if len(self._pages) == 2 else 0
        source_width = sum(page.width() for page in self._pages)
        source_height = max(page.height() for page in self._pages)

        fit_scale = min(
            available.width() / max(1, source_width + gap),
            available.height() / max(1, source_height),
        )
        scale = max(0.05, fit_scale * self._zoom)

        target_sizes = [
            page.size().scaled(
                max(1, int(page.width() * scale)),
                max(1, int(page.height() * scale)),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            for page in self._pages
        ]

        total_width = sum(size.width() for size in target_sizes) + gap
        max_height = max(size.height() for size in target_sizes)
        x = (self.width() - total_width) // 2
        y = (self.height() - max_height) // 2

        for page, size in zip(self._pages, target_sizes):
            target = page.rect()
            target.setSize(size)
            target.moveTo(x, y)
            painter.fillRect(
                target.adjusted(-2, -2, 2, 2),
                Qt.GlobalColor.white,
            )
            painter.drawPixmap(target, page)
            x += size.width() + gap

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
            event.accept()
            return
        event.ignore()
