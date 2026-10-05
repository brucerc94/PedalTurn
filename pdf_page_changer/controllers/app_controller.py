from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QTimer
from PySide6.QtWidgets import QDialog, QMessageBox

from ..core.models import PlaylistState, ScoreItem
from ..core.navigation import PageNavigator
from ..services.config_service import AppConfig, ConfigService
from ..services.media_service import MediaService
from ..services.midi_service import MidiEvent, MidiService
from ..services.pdf_service import PdfService, PdfServiceError
from ..services.project_service import ProjectFileError, ProjectFileService
from ..ui.dialogs import MidiCaptureDialog, MidiDeviceDialog, SettingsDialog
from ..ui.main_window import MainWindow
from ..ui.video_window import VideoWindow


class AppController:
    MIDI_THRESHOLD = 64

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service
        self._config: AppConfig = config_service.load()
        self._state = PlaylistState()
        self._navigator = PageNavigator()
        self._pdf_service = PdfService()
        self._project_service = ProjectFileService()
        self._midi_service = MidiService()
        self._media_service = MediaService()
        self._window = MainWindow()
        self._video_window = VideoWindow()
        self._settings_dialog: SettingsDialog | None = None
        self._capture_dialog: MidiCaptureDialog | None = None
        self._last_midi_values: dict[int, int] = {}
        self._midi_timer = QTimer(self._window)
        self._midi_timer.setInterval(30)
        self._midi_timer.timeout.connect(self._poll_midi)
        self._shutting_down = False

        self._video_window.closed.connect(self._on_video_closed)
        self._media_service.attach_video_output(self._video_window.video_widget)
        self._media_service.error.connect(self._on_media_error)
        self._connect_signals()
        self._initialize_midi()
        self._sync_ui()

    def show(self) -> None:
        self._window.show()

    def _connect_signals(self) -> None:
        self._window.add_pdf_requested.connect(self.add_pdf)
        self._window.save_project_requested.connect(self.save_project)
        self._window.load_project_requested.connect(self.load_project)
        self._window.remove_pdf_requested.connect(self.remove_pdf)
        self._window.previous_page_requested.connect(self.previous_page)
        self._window.next_page_requested.connect(self.next_page)
        self._window.add_video_requested.connect(self.add_video)
        self._window.toggle_video_requested.connect(self.toggle_video)
        self._window.settings_requested.connect(self.show_settings)
        self._window.pdf_selected.connect(self.select_pdf)

    def _initialize_midi(self) -> None:
        device = self._midi_service.find_device_by_name(self._config.midi_device_name)
        if device is None:
            devices = self._midi_service.list_input_devices()
            device = devices[0] if len(devices) == 1 else None

        try:
            if device is not None:
                opened = self._midi_service.open(device.device_id)
                self._config.midi_device_name = opened.name
                self._config_service.save(self._config)
                self._window.set_status(f"MIDI ready: {opened.name}")
            else:
                self._window.set_status(
                    "Connect a MIDI device and select it in Settings."
                )
        except RuntimeError as exc:
            self._window.set_status(str(exc))

        self._midi_timer.start()

    def add_pdf(self) -> None:
        path = self._window.open_pdf_dialog()
        if path is None:
            return

        resolved = path.resolve()
        if any(item.pdf_path.resolve() == resolved for item in self._state.items):
            self._window.set_status("That PDF is already in the playlist.")
            return

        self._state.items.append(ScoreItem(resolved))
        if len(self._state.items) == 1:
            self._open_current_pdf()
        else:
            self._sync_ui()

    def save_project(self) -> None:
        if not self._state.items:
            QMessageBox.information(
                self._window,
                "No Scores",
                "There are no PDFs in the playlist to save.",
            )
            return

        path = self._window.save_project_dialog()
        if path is None:
            return
        if path.suffix.lower() != ".vdp":
            path = path.with_suffix(".vdp")

        try:
            self._project_service.save(path, self._state.items)
        except ProjectFileError as exc:
            QMessageBox.critical(self._window, "Error", str(exc))
            return

        self._window.set_status(f"Playlist saved: {path.name}")

    def load_project(self) -> None:
        path = self._window.load_project_dialog()
        if path is None:
            return

        try:
            items = self._project_service.load(path)
        except ProjectFileError as exc:
            QMessageBox.critical(self._window, "Error", str(exc))
            return

        self._stop_video()
        self._state.set_items(items)
        self._open_current_pdf()
        self._window.set_status(f"Playlist loaded: {len(items)} scores.")

    def remove_pdf(self) -> None:
        item = self._state.current_item
        if item is None:
            return

        self._stop_video()
        removed = item.display_name
        self._state.remove_current_item()
        self._open_current_pdf() if self._state.current_item else self._clear_current_pdf()
        self._window.set_status(f"PDF removed: {removed}")

    def select_pdf(self, index: int) -> None:
        if not 0 <= index < len(self._state.items) or index == self._state.current_index:
            return
        self._switch_pdf(index, 0)

    def add_video(self) -> None:
        item = self._state.current_item
        if item is None:
            QMessageBox.information(
                self._window,
                "No Score",
                "Add a PDF score first.",
            )
            return

        path = self._window.choose_video_dialog()
        if path is None:
            return

        self._state.replace_current_item(
            ScoreItem(item.pdf_path, path.resolve())
        )
        self._window.set_status(f"Video assigned: {path.name}")

    def toggle_video(self) -> None:
        if self._video_window.isVisible():
            self._stop_video()
            return

        item = self._state.current_item
        if item is None or item.video_path is None:
            QMessageBox.information(
                self._window,
                "No Video",
                "No video is assigned to this score.",
            )
            return

        try:
            if not item.video_path.exists():
                raise FileNotFoundError(f"Video not found: {item.video_path}")

            self._video_window.resize(
                self._config.video_width,
                self._config.video_height,
            )
            self._restore_video_position()
            self._video_window.show()
            self._media_service.play(item.video_path)
        except (FileNotFoundError, RuntimeError) as exc:
            self._video_window.hide()
            QMessageBox.critical(self._window, "Video", str(exc))
            return

        self._window.set_status("Video started.")

    def show_settings(self) -> None:
        if self._settings_dialog is not None:
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return

        dialog = SettingsDialog(
            self._config.video_width,
            self._config.video_height,
            self._config.midi_pedal_cc,
            self._config.midi_device_name,
            self._window,
        )
        self._settings_dialog = dialog
        dialog.resolution_changed.connect(self.set_video_size)
        dialog.change_device_requested.connect(self.change_midi_device)
        dialog.detect_pedal_requested.connect(self.capture_pedal)
        dialog.finished.connect(lambda _code: self._clear_settings_dialog())
        dialog.show()

    def set_video_size(self, width: int, height: int) -> None:
        self._config.video_width = width
        self._config.video_height = height
        self._config_service.save(self._config)
        self._window.set_status(f"Video window size: {width} × {height}")

    def change_midi_device(self) -> None:
        devices = self._midi_service.list_input_devices()
        if not devices:
            QMessageBox.information(
                self._settings_dialog or self._window,
                "MIDI",
                "No MIDI input devices were found.",
            )
            return

        dialog = MidiDeviceDialog(devices, self._settings_dialog or self._window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        device_id = dialog.selected_device_id
        if device_id is None:
            return

        try:
            device = self._midi_service.open(device_id)
        except RuntimeError as exc:
            QMessageBox.critical(
                self._settings_dialog or self._window,
                "MIDI",
                str(exc),
            )
            return

        self._last_midi_values.clear()
        self._config.midi_device_name = device.name
        self._config_service.save(self._config)

        if self._settings_dialog:
            self._settings_dialog.update_device(device.name)

        self._window.set_status(f"MIDI device selected: {device.name}")

    def capture_pedal(self) -> None:
        if self._capture_dialog is not None:
            return

        if self._midi_service.device_id is None:
            QMessageBox.information(
                self._settings_dialog or self._window,
                "MIDI",
                "Select a MIDI device first.",
            )
            return

        self._midi_service.clear_pending()
        self._last_midi_values.clear()
        dialog = MidiCaptureDialog(self._settings_dialog or self._window)
        self._capture_dialog = dialog
        dialog.finished.connect(lambda _code: self._clear_capture_dialog())
        dialog.open()

    def next_page(self) -> None:
        page_count = self._pdf_service.page_count
        new_page = self._navigator.next_within_document(
            self._state.current_page,
            page_count,
        )
        if new_page is not None:
            self._state.current_page = new_page
            self._render_current_spread()
            return

        if self._state.current_index + 1 < len(self._state.items):
            self._switch_pdf(self._state.current_index + 1, 0)
            return

        self._window.set_status("Already at the end of the playlist.")

    def previous_page(self) -> None:
        new_page = self._navigator.previous_within_document(
            self._state.current_page
        )
        if new_page is not None:
            self._state.current_page = new_page
            self._render_current_spread()
            return

        if self._state.current_index == 0:
            self._window.set_status("Already at the beginning of the playlist.")
            return

        self._switch_pdf(self._state.current_index - 1, None)

    def _switch_pdf(self, index: int, page: int | None) -> None:
        was_visible = self._video_window.isVisible()
        self._stop_video()
        self._state.current_index = index
        self._state.current_page = 0

        if not self._open_current_pdf(render=False):
            return

        if page is None:
            self._state.current_page = self._navigator.last_spread_start(
                self._pdf_service.page_count
            )
        else:
            self._state.current_page = min(
                page,
                max(0, self._pdf_service.page_count - 1),
            )

        self._render_current_spread()

        if (
            was_visible
            and self._state.current_item
            and self._state.current_item.video_path
        ):
            self.toggle_video()

    def _open_current_pdf(self, render: bool = True) -> bool:
        item = self._state.current_item
        if item is None:
            self._clear_current_pdf()
            return False

        if not item.pdf_path.exists():
            self._pdf_service.close()
            self._window.score_viewer.clear()
            self._window.set_status(f"PDF not found: {item.pdf_path}")
            self._sync_ui()
            return False

        try:
            self._pdf_service.open(item.pdf_path)
        except PdfServiceError as exc:
            self._pdf_service.close()
            self._window.score_viewer.clear()
            QMessageBox.critical(self._window, "PDF", str(exc))
            self._sync_ui()
            return False

        if render:
            self._render_current_spread()
        return True

    def _render_current_spread(self) -> None:
        if self._pdf_service.page_count <= 0:
            return

        pages = self._pdf_service.render_spread(self._state.current_page)
        self._window.score_viewer.set_pages(pages)
        self._sync_ui()

    def _clear_current_pdf(self) -> None:
        self._pdf_service.close()
        self._window.score_viewer.clear()
        self._sync_ui()

    def _sync_ui(self) -> None:
        self._window.set_playlist(
            self._state.items,
            self._state.current_index,
        )
        self._window.set_score_info(
            self._state.current_item,
            self._state.current_page,
            self._pdf_service.page_count,
        )

    def _poll_midi(self) -> None:
        for event in self._midi_service.poll():
            if not event.is_control_change:
                continue

            if self._capture_dialog is not None:
                self._capture_midi_event(event)
            else:
                self._handle_pedal_event(event)

    def _capture_midi_event(self, event: MidiEvent) -> None:
        previous = self._last_midi_values.get(event.controller, 0)
        self._last_midi_values[event.controller] = event.value

        if event.value >= self.MIDI_THRESHOLD and previous < self.MIDI_THRESHOLD:
            self._config.midi_pedal_cc = event.controller
            self._config_service.save(self._config)
            self._capture_dialog.show_detected(event.controller)

            if self._settings_dialog:
                self._settings_dialog.update_pedal(event.controller)

    def _handle_pedal_event(self, event: MidiEvent) -> None:
        previous = self._last_midi_values.get(event.controller, 0)
        self._last_midi_values[event.controller] = event.value

        if self._config.midi_pedal_cc is None:
            return

        if (
            event.controller == self._config.midi_pedal_cc
            and event.value >= self.MIDI_THRESHOLD
            and previous < self.MIDI_THRESHOLD
        ):
            self.next_page()

    def _stop_video(self) -> None:
        if self._video_window.isVisible():
            position = self._video_window.pos()
            self._config.video_x = position.x()
            self._config.video_y = position.y()
            self._config_service.save(self._config)

        self._media_service.stop()
        self._video_window.hide()

    def _on_video_closed(self, position: QPoint) -> None:
        self._config.video_x = position.x()
        self._config.video_y = position.y()
        self._config_service.save(self._config)
        self._media_service.stop()
        self._window.set_status("Video stopped.")

    def _restore_video_position(self) -> None:
        if self._config.video_x is not None and self._config.video_y is not None:
            self._video_window.move(
                self._config.video_x,
                self._config.video_y,
            )

    def _on_media_error(self, message: str) -> None:
        self._video_window.hide()
        QMessageBox.critical(self._window, "Video", message)

    def _clear_settings_dialog(self) -> None:
        self._settings_dialog = None

    def _clear_capture_dialog(self) -> None:
        self._capture_dialog = None
        self._last_midi_values.clear()

    def shutdown(self) -> None:
        if self._shutting_down:
            return

        self._shutting_down = True
        self._midi_timer.stop()
        self._stop_video()
        self._pdf_service.close()
        self._midi_service.close()
