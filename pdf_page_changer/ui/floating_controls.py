from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QToolButton,
)


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
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(self.HIDE_DELAY_MS)
        self._hide_timer.timeout.connect(self._hide_panel)

        self._playlist_popup = QFrame(
            self,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self._playlist_popup.setObjectName("playlistPopup")
        self._playlist_popup.setFixedWidth(330)

        popup_layout = QGridLayout(self._playlist_popup)
        popup_layout.setContentsMargins(12, 12, 12, 12)
        popup_layout.setVerticalSpacing(8)

        popup_title = QLabel("SCORES")
        popup_title.setObjectName("playlistPopupTitle")
        self._playlist_count = QLabel()
        self._playlist_count.setObjectName("playlistPopupCount")

        popup_header = QFrame()
        header_layout = QGridLayout(popup_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(popup_title, 0, 0)
        header_layout.addWidget(
            self._playlist_count,
            0,
            1,
            Qt.AlignmentFlag.AlignRight,
        )

        self._playlist = QListWidget()
        self._playlist.setObjectName("playlistList")
        self._playlist.setSpacing(2)
        self._playlist.currentRowChanged.connect(self._select_playlist_item)
        self._playlist.itemDoubleClicked.connect(
            lambda _item: self._close_playlist()
        )

        popup_layout.addWidget(popup_header, 0, 0)
        popup_layout.addWidget(self._playlist, 1, 0)

        self._handle = QToolButton(self)
        self._handle.setObjectName("floatingHandle")
        self._handle.setText("☰")
        self._handle.setToolTip("Show controls")
        self._handle.clicked.connect(self.show_controls)

        self._playlist_button = QPushButton("Scores (0)")
        self._playlist_button.setObjectName("playlistButton")
        self._playlist_button.setToolTip("Show score playlist")
        self._playlist_button.clicked.connect(self.toggle_playlist)

        self._page_info = QLabel()
        self._page_info.setObjectName("floatingPageInfo")

        self._status = QLabel()
        self._status.setObjectName("floatingStatus")
        self._status.setMaximumWidth(210)

        self._panel = QFrame(self)
        self._panel.setObjectName("floatingPanel")

        layout = QGridLayout(self._panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(5)

        layout.addWidget(self._playlist_button, 0, 0, 1, 4)
        self._add_button(
            layout,
            "←",
            self.previous_page_requested.emit,
            0,
            4,
            "Previous page",
        )
        self._add_button(
            layout,
            "→",
            self.next_page_requested.emit,
            0,
            5,
            "Next page",
            "accentButton",
        )
        layout.addWidget(self._page_info, 0, 6, 1, 5)

        self._add_button(
            layout, "+ PDF", self.add_pdf_requested.emit, 1, 0, "Add PDF", "accentButton"
        )
        self._add_button(
            layout, "Save", self.save_project_requested.emit, 1, 1, "Save playlist"
        )
        self._add_button(
            layout, "Load", self.load_project_requested.emit, 1, 2, "Load playlist"
        )
        self._add_button(
            layout, "Remove", self.remove_pdf_requested.emit, 1, 3, "Remove PDF", "dangerButton"
        )
        self._add_button(
            layout, "+ Video", self.add_video_requested.emit, 1, 4, "Add video"
        )
        self._add_button(
            layout, "Video", self.toggle_video_requested.emit, 1, 5, "Show or hide video"
        )
        self._add_button(
            layout, "Settings", self.settings_requested.emit, 1, 6, "Settings"
        )
        self._add_button(
            layout, "−", self._zoom_out, 1, 7, "Zoom out"
        )
        self._add_button(
            layout, "Fit", self._fit_requested, 1, 8, "Fit to screen"
        )
        self._add_button(
            layout, "+", self._zoom_in, 1, 9, "Zoom in"
        )
        layout.addWidget(self._status, 1, 10)

        self._panel.installEventFilter(self)
        self._playlist_popup.installEventFilter(self)
        self.installEventFilter(self)

        self._panel.adjustSize()
        self._handle.adjustSize()
        self.show_controls()

    def bind_viewer(self, viewer) -> None:
        self._viewer = viewer

    @staticmethod
    def _add_button(
        layout: QGridLayout,
        text: str,
        slot,
        row: int,
        column: int,
        tooltip: str,
        object_name: str | None = None,
    ) -> QPushButton:
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.setToolTip(tooltip)
        button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        button.clicked.connect(lambda _checked=False: slot())
        layout.addWidget(button, row, column)
        return button

    def _zoom_out(self) -> None:
        self._viewer.zoom_out()
        self._restart_hide_timer()

    def _fit_requested(self) -> None:
        self._viewer.reset_zoom()
        self._restart_hide_timer()

    def _zoom_in(self) -> None:
        self._viewer.zoom_in()
        self._restart_hide_timer()

    def set_playlist(self, items, current_index: int) -> None:
        self._playlist_button.setText(f"Scores ({len(items)})")
        self._playlist_count.setText(str(len(items)))

        self._playlist.blockSignals(True)
        self._playlist.clear()

        for index, item in enumerate(items):
            markers = []
            if index == current_index:
                markers.append("▶")
            if item.video_path is not None:
                markers.append("🎬")
            if not item.pdf_path.exists():
                markers.append("⚠")

            prefix = f"{' '.join(markers)}  " if markers else ""
            label = f"{prefix}{item.display_name}"

            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, index)

            if index == current_index:
                list_item.setToolTip("Current score")
            elif item.video_path is not None:
                list_item.setToolTip("Has an associated video")

            if not item.pdf_path.exists():
                list_item.setToolTip("PDF not found")

            self._playlist.addItem(list_item)

        self._playlist.setCurrentRow(current_index if items else -1)
        self._playlist.blockSignals(False)

    def _select_playlist_item(self, row: int) -> None:
        if row < 0:
            return
        index = self._playlist.item(row).data(Qt.ItemDataRole.UserRole)
        self._close_playlist()
        self.pdf_selected.emit(index)
        self._restart_hide_timer()

    def toggle_playlist(self) -> None:
        if self._playlist_popup.isVisible():
            self._close_playlist()
            self._restart_hide_timer()
            return

        self._hide_timer.stop()
        self._playlist_popup.adjustSize()
        self._playlist_popup.setFixedHeight(
            min(430, max(120, self._playlist_popup.sizeHint().height()))
        )

        popup_position = self.mapToGlobal(
            QPoint(0, self._panel.height() + 8)
        )
        self._playlist_popup.move(popup_position)
        self._playlist_popup.show()
        self._playlist_popup.raise_()

    def _close_playlist(self) -> None:
        self._playlist_popup.hide()

    def set_page_info(self, text: str) -> None:
        self._page_info.setText(text)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def show_controls(self) -> None:
        self._handle.hide()
        self._panel.show()
        self._panel.adjustSize()
        self.setFixedSize(self._panel.sizeHint())
        self.raise_()
        self._restart_hide_timer()

    def _hide_panel(self) -> None:
        if self._playlist_popup.isVisible():
            self._hide_timer.stop()
            return
        if self.underMouse():
            self._restart_hide_timer()
            return
        self._panel.hide()
        self.setFixedSize(self._handle.sizeHint())
        self._handle.show()
        self.raise_()

    def _restart_hide_timer(self) -> None:
        if self._panel.isVisible() and not self._playlist_popup.isVisible():
            self._hide_timer.start()

    def enterEvent(self, event: QEvent) -> None:
        del event
        self._hide_timer.stop()

    def leaveEvent(self, event: QEvent) -> None:
        del event
        self._restart_hide_timer()

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self._playlist_popup:
            if event.type() in (QEvent.Type.Enter, QEvent.Type.MouseMove):
                self._hide_timer.stop()
            elif event.type() == QEvent.Type.Leave:
                self._restart_hide_timer()
        elif obj is self._panel and event.type() == QEvent.Type.MouseMove:
            self._hide_timer.stop()
        return super().eventFilter(obj, event)
