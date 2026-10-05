from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
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
        self.setWindowTitle("Dispositivo MIDI")
        self.setModal(True)
        self.resize(460, 320)

        self._devices = devices
        self.list_widget = QListWidget()
        for device in devices:
            item = QListWidgetItem(device.name)
            item.setData(256, device.device_id)
            self.list_widget.addItem(item)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecciona el dispositivo MIDI de entrada:"))
        layout.addWidget(self.list_widget)
        layout.addWidget(buttons)

    @property
    def selected_device_id(self) -> int | None:
        item = self.list_widget.currentItem()
        return item.data(256) if item else None


class MidiCaptureDialog(QDialog):
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detectar pedal MIDI")
        self.setModal(True)
        self.resize(420, 180)

        self.label = QLabel(
            "Presiona el pedal que quieres usar para avanzar una página."
        )
        self.label.setWordWrap(True)

        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(cancel)

    def show_detected(self, controller: int) -> None:
        self.label.setText(f"Detectado: CC #{controller}")
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
        self.setWindowTitle("Configuración")
        self.resize(520, 300)

        self.resolution = QComboBox()
        for option in self.RESOLUTIONS:
            self.resolution.addItem(option.label, (option.width, option.height))

        current = next(
            (
                i
                for i, option in enumerate(self.RESOLUTIONS)
                if option.width == width and option.height == height
            ),
            0,
        )
        self.resolution.setCurrentIndex(current)
        self.resolution.currentIndexChanged.connect(self._on_resolution_changed)

        self.device_label = QLabel(device_name or "No configurado")
        self.pedal_label = QLabel(
            f"CC #{pedal_cc}" if pedal_cc is not None else "No configurado"
        )

        change_device = QPushButton("Cambiar dispositivo MIDI")
        change_device.clicked.connect(self.change_device_requested)

        detect_pedal = QPushButton("Detectar pedal MIDI")
        detect_pedal.clicked.connect(self.detect_pedal_requested)

        form = QFormLayout()
        form.addRow("Tamaño inicial de video:", self.resolution)
        form.addRow("Dispositivo MIDI:", self.device_label)
        form.addRow("Pedal:", self.pedal_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(change_device)
        layout.addWidget(detect_pedal)
        layout.addStretch()
        layout.addWidget(buttons)

    def _on_resolution_changed(self, index: int) -> None:
        width, height = self.resolution.itemData(index)
        self.resolution_changed.emit(width, height)

    def update_device(self, name: str | None) -> None:
        self.device_label.setText(name or "No configurado")

    def update_pedal(self, controller: int | None) -> None:
        self.pedal_label.setText(
            f"CC #{controller}" if controller is not None else "No configurado"
        )
