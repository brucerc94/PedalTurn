from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    video_width: int = 1280
    video_height: int = 720
    midi_pedal_cc: int | None = None
    midi_device_name: str | None = None
    video_x: int | None = None
    video_y: int | None = None


class ConfigService:
    def __init__(self, config_path: Path):
        self._config_path = config_path

    def load(self) -> AppConfig:
        if not self._config_path.exists():
            return AppConfig()

        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return AppConfig()

        if not isinstance(raw, dict):
            return AppConfig()

        return AppConfig(
            video_width=self._positive_int(raw.get("video_width"), 1280),
            video_height=self._positive_int(raw.get("video_height"), 720),
            midi_pedal_cc=self._optional_int(raw.get("midi_pedal_cc")),
            midi_device_name=self._optional_text(raw.get("midi_device_name")),
            video_x=self._optional_int(raw.get("video_x")),
            video_y=self._optional_int(raw.get("video_y")),
        )

    def save(self, config: AppConfig) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(asdict(config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _positive_int(value: object, default: int) -> int:
        try:
            number = int(value)
            return number if number > 0 else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _optional_text(value: object) -> str | None:
        text = str(value).strip() if value is not None else ""
        return text or None
