from __future__ import annotations

from dataclasses import dataclass

import pygame.midi


@dataclass(frozen=True)
class MidiDevice:
    device_id: int
    name: str


@dataclass(frozen=True)
class MidiEvent:
    status: int
    data1: int
    data2: int
    timestamp: int

    @property
    def is_control_change(self) -> bool:
        return (self.status & 0xF0) == 0xB0

    @property
    def controller(self) -> int:
        return self.data1

    @property
    def value(self) -> int:
        return self.data2


class MidiService:
    def __init__(self):
        pygame.midi.init()
        self._input: pygame.midi.Input | None = None
        self._device_id: int | None = None

    @property
    def device_id(self) -> int | None:
        return self._device_id

    def list_input_devices(self) -> list[MidiDevice]:
        devices: list[MidiDevice] = []
        for device_id in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(device_id)
            if not info:
                continue

            _, name, is_input, _, _ = info
            if is_input:
                devices.append(
                    MidiDevice(
                        device_id=device_id,
                        name=name.decode(errors="replace"),
                    )
                )
        return devices

    def find_device_by_name(self, name: str | None) -> MidiDevice | None:
        if not name:
            return None

        target = name.strip().casefold()
        return next(
            (
                device
                for device in self.list_input_devices()
                if device.name.casefold() == target
            ),
            None,
        )

    def open(self, device_id: int) -> MidiDevice:
        current_device = self._device_id

        # If this device is already open, reuse the existing handle.
        # Some Windows MIDI drivers do not allow two simultaneous handles.
        if self._input is not None and current_device == device_id:
            return self._device_info(device_id)

        # Open the new device first. If it fails, keep the current device
        # active so the application is not left without MIDI input.
        try:
            new_input = pygame.midi.Input(device_id)
        except Exception as exc:
            detail = str(exc).strip()
            suffix = f" ({detail})" if detail else ""
            raise RuntimeError(
                f"Could not open MIDI device #{device_id}{suffix}"
            ) from exc

        old_input = self._input
        self._input = new_input
        self._device_id = device_id

        if old_input is not None:
            try:
                old_input.close()
            except Exception:
                pass

        return self._device_info(device_id)

    def _device_info(self, device_id: int) -> MidiDevice:
        return next(
            (
                device
                for device in self.list_input_devices()
                if device.device_id == device_id
            ),
            MidiDevice(device_id, f"MIDI #{device_id}"),
        )

    def open_first_input(self) -> MidiDevice | None:
        devices = self.list_input_devices()
        return self.open(devices[0].device_id) if devices else None

    def clear_pending(self) -> None:
        if self._input is None:
            return
        while self._input.poll():
            self._input.read(64)

    def poll(self, max_events: int = 32) -> list[MidiEvent]:
        if self._input is None or not self._input.poll():
            return []

        events: list[MidiEvent] = []
        for raw_event in self._input.read(max_events):
            data, timestamp = raw_event
            if len(data) < 3:
                continue
            events.append(
                MidiEvent(
                    status=int(data[0]),
                    data1=int(data[1]),
                    data2=int(data[2]),
                    timestamp=int(timestamp),
                )
            )
        return events

    def close_input(self) -> None:
        if self._input is not None:
            try:
                self._input.close()
            finally:
                self._input = None
                self._device_id = None

    def close(self) -> None:
        self.close_input()
        pygame.midi.quit()
