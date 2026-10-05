from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton


class FloatingControls(QFrame):
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

    HIDE_DELAY_MS = 3500

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(self.HIDE_DELAY_MS)
        self._hide_timer.timeout.connect(self._hide_panel)

        self._panel = QFrame(self)
        self._panel.setObjectName("floatingPanel")
        self._handle = QToolButton(self)
        self._handle.setObjectName("floatingHandle")
        self._handle.setText("☰")
        self._handle.clicked.connect(self.show_controls)

        self._page_info = QLabel()
        self._page_info.setObjectName("floatingPageInfo")

        self._status = QLabel()
        self._status.setObjectName("floatingStatus")
        self._status.setMaximumWidth(230)

        self._queue = QComboBox()
        self._queue.setObjectName("floatingQueue")
        self._queue.setMinimumWidth(230)
        self._queue.currentIndexChanged.connect(self.pdf_selected.emit)

        layout = QHBoxLayout(self._panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(self._queue, 1)
        self._add_button(layout, "+ PDF", self.add_pdf_requested.emit, "accentButton")
        self._add_button(layout, "Guardar", self.save_project_requested.emit)
        self._add_button(layout, "Cargar", self.load_project_requested.emit)
        self._add_button(layout, "Eliminar", self.remove_pdf_requested.emit, "dangerButton")
        self._add_button(layout, "←", self.previous_page_requested.emit)
        self._add_button(layout, "→", self.next_page_requested.emit, "accentButton")
        self._add_button(layout, "Video", self.toggle_video_requested.emit)
        self._add_button(layout, "Config", self.settings_requested.emit)
        self._add_button(layout, "−", self._zoom_out)
        self._add_button(layout, "Ajustar", self._fit_requested)
        self._add_button(layout, "+", self._zoom_in)
        layout.addWidget(self._page_info)
        layout.addWidget(self._status)

        self._panel.installEventFilter(self)
        self.installEventFilter(self)
        self._panel.adjustSize()
        self.setFixedHeight(self._panel.sizeHint().height())
        self.setMinimumWidth(min(1100, self._panel.sizeHint().width()))
        self.show_controls()

    def bind_viewer(self, viewer) -> None:
        self._viewer = viewer

    def _add_button(self, layout: QHBoxLayout, text: str, slot, object_name: str | None = None) -> QPushButton:
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.clicked.connect(lambda _checked=False: slot())
        layout.addWidget(button)
        return button

    def _zoom_out(self) -> None:
        if hasattr(self, "_viewer"):
            self._viewer.zoom_out()
        self._restart_hide_timer()

    def _fit_requested(self) -> None:
        if hasattr(self, "_viewer"):
            self._viewer.reset_zoom()
        self._restart_hide_timer()

    def _zoom_in(self) -> None:
        if hasattr(self, "_viewer"):
            self._viewer.zoom_in()
        self._restart_hide_timer()

    def set_playlist(self, items, current_index: int) -> None:
        self._queue.blockSignals(True)
        self._queue.clear()
        for item in items:
            label = item.display_name if item.pdf_path.exists() else f"⚠ {item.display_name}"
            self._queue.addItem(label)
        self._queue.setCurrentIndex(current_index if items else -1)
        self._queue.blockSignals(False)

    def set_page_info(self, text: str) -> None:
        self._page_info.setText(text)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def show_controls(self) -> None:
        self._panel.show()
        self._handle.hide()
        self._panel.adjustSize()
        self.setFixedSize(self._panel.sizeHint())
        self.raise_()
        self._restart_hide_timer()

    def _hide_panel(self) -> None:
        if self.underMouse():
            self._restart_hide_timer()
            return
        self._panel.hide()
        self.setFixedSize(self._handle.sizeHint())
        self._handle.show()
        self.raise_()

    def _restart_hide_timer(self) -> None:
        if self._panel.isVisible():
            self._hide_timer.start()

    def enterEvent(self, event: QEvent) -> None:
        del event
        self._hide_timer.stop()

    def leaveEvent(self, event: QEvent) -> None:
        del event
        self._restart_hide_timer()

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self._panel and event.type() == QEvent.Type.MouseMove:
            self._hide_timer.stop()
        return super().eventFilter(obj, event)
