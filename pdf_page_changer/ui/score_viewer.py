from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ..services.pdf_service import PageImage


class ScoreViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setAutoFillBackground(False)
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

    def _to_pixmap(self, page: PageImage) -> QPixmap:
        image = QImage(
            page.pixels,
            page.width,
            page.height,
            page.width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        return QPixmap.fromImage(image)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        if not self._pages:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Agrega una partitura PDF para comenzar",
            )
            return

        available = self.rect().adjusted(18, 18, -18, -18)
        gap = self._page_gap if len(self._pages) == 2 else 0
        total_source_width = sum(page.width() for page in self._pages)
        source_height = max(page.height() for page in self._pages)

        if total_source_width <= 0 or source_height <= 0:
            return

        fit_scale = min(
            available.width() / (total_source_width + gap),
            available.height() / source_height,
        )
        scale = max(0.05, fit_scale * self._zoom)

        target_widths = [max(1, int(page.width() * scale)) for page in self._pages]
        target_heights = [max(1, int(page.height() * scale)) for page in self._pages]
        total_width = sum(target_widths) + gap
        max_height = max(target_heights)

        x = (self.width() - total_width) // 2
        y = (self.height() - max_height) // 2

        for index, page in enumerate(self._pages):
            target_size = page.size().scaled(
                target_widths[index],
                target_heights[index],
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            target_rect = page.rect()
            target_rect.setSize(target_size)
            target_rect.moveTop(y)
            target_rect.moveLeft(x)

            painter.fillRect(
                target_rect.adjusted(-2, -2, 2, 2),
                Qt.GlobalColor.white,
            )
            painter.drawPixmap(target_rect, page)
            x += target_widths[index] + gap

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        event.ignore()
