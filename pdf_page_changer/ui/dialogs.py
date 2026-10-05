from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from ..services.midi_service import MidiDevice


class MidiDeviceDialog(QDialog):
    def __init__(self, devices: list[MidiDevice], parent=None):
        super().__init__(parent)
        self.setWindowTitle("MIDI Device")
        self.setModal(True)
        self.resize(460, 320)

        self.list_widget = QListWidget()
        for device in devices:
            item = QListWidgetItem(device.name)
            item.setData(Qt.ItemDataRole.UserRole, device.device_id)
            self.list_widget.addItem(item)

        select = QPushButton("Select")
        cancel = QPushButton("Cancel")
        select.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a MIDI input device:"))
        layout.addWidget(self.list_widget)
        layout.addWidget(select)
        layout.addWidget(cancel)

        if devices:
            self.list_widget.setCurrentRow(0)

    @property
    def selected_device_id(self) -> int | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None


class MidiCaptureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detect MIDI Pedal")
        self.setModal(True)
        self.resize(420, 180)

        self.label = QLabel(
            "Press the pedal you want to use to advance one page."
        )
        self.label.setWordWrap(True)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(cancel)

    def show_detected(self, controller: int) -> None:
        self.label.setText(f"Detected: CC #{controller}")
        QTimer.singleShot(250, self.accept)


@dataclass(frozen=True)
class ResolutionOption:
    label: str
    width: int
    height: int


class SettingsDialog(QDialog):
    resolution_changed = Signal(int, int)
    change_device_requested = Signal()
    detect_pedal_requested = Signal()

    RESOLUTIONS = (
        ResolutionOption("HD · 1280 × 720", 1280, 720),
        ResolutionOption("Full HD · 1920 × 1080", 1920, 1080),
        ResolutionOption("2K · 2560 × 1440", 2560, 1440),
        ResolutionOption("4K · 3840 × 2160", 3840, 2160),
    )

    def __init__(
        self,
        width: int,
        height: int,
        pedal_cc: int | None,
        device_name: str | None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(520, 300)

        self.resolution = QComboBox()
        for option in self.RESOLUTIONS:
            self.resolution.addItem(option.label, (option.width, option.height))

        index = next(
            (
                i
                for i, option in enumerate(self.RESOLUTIONS)
                if option.width == width and option.height == height
            ),
            0,
        )
        self.resolution.setCurrentIndex(index)
        self.resolution.currentIndexChanged.connect(
            self._on_resolution_changed
        )

        self.device_label = QLabel(device_name or "Not configured")
        self.pedal_label = QLabel(
            f"CC #{pedal_cc}" if pedal_cc is not None else "Not configured"
        )

        change_device = QPushButton("Change MIDI Device")
        detect_pedal = QPushButton("Detect MIDI Pedal")
        close = QPushButton("Close")

        change_device.clicked.connect(
            lambda: self.change_device_requested.emit()
        )
        detect_pedal.clicked.connect(
            lambda: self.detect_pedal_requested.emit()
        )
        close.clicked.connect(self.accept)

        form = QFormLayout()
        form.addRow("Initial video size:", self.resolution)
        form.addRow("MIDI device:", self.device_label)
        form.addRow("Pedal:", self.pedal_label)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(change_device)
        layout.addWidget(detect_pedal)
        layout.addStretch()
        layout.addWidget(close)

    def _on_resolution_changed(self, index: int) -> None:
        width, height = self.resolution.itemData(index)
        self.resolution_changed.emit(width, height)

    def update_device(self, name: str | None) -> None:
        self.device_label.setText(name or "Not configured")

    def update_pedal(self, controller: int | None) -> None:
        self.pedal_label.setText(
            f"CC #{controller}" if controller is not None else "Not configured"
        )
