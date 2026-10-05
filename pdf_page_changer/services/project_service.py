from __future__ import annotations

import json
from pathlib import Path

from ..core.models import ScoreItem


class ProjectFileError(RuntimeError):
    """Raised when a .vdp project cannot be parsed or written."""


class ProjectFileService:
    CURRENT_VERSION = 2

    def save(self, file_path: Path, items: list[ScoreItem]) -> None:
        payload = {
            "version": self.CURRENT_VERSION,
            "items": [
                {
                    "pdf": str(item.pdf_path),
                    "video": str(item.video_path) if item.video_path else None,
                }
                for item in items
            ],
        }

        try:
            file_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise ProjectFileError(f"No se pudo guardar el proyecto: {exc}") from exc

    def load(self, file_path: Path) -> list[ScoreItem]:
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ProjectFileError(f"No se pudo leer el proyecto: {exc}") from exc

        try:
            if isinstance(raw.get("items"), list):
                return self._load_v2(raw["items"])
            return self._load_legacy(raw)
        except (TypeError, ValueError) as exc:
            raise ProjectFileError(f"Formato de proyecto inválido: {exc}") from exc

    @staticmethod
    def _load_v2(items: list[object]) -> list[ScoreItem]:
        result: list[ScoreItem] = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue
            pdf = ProjectFileService._required_path(raw_item.get("pdf"))
            video = ProjectFileService._optional_path(raw_item.get("video"))
            result.append(ScoreItem(pdf, video))
        return result

    @staticmethod
    def _load_legacy(raw: dict) -> list[ScoreItem]:
        pdf_queue = raw.get("pdf_queue", [])
        video_map = raw.get("video_map", {})
        if not isinstance(pdf_queue, list):
            raise ValueError("pdf_queue debe ser una lista")
        if not isinstance(video_map, dict):
            video_map = {}

        result: list[ScoreItem] = []
        for pdf in pdf_queue:
            pdf_path = ProjectFileService._required_path(pdf)
            video = ProjectFileService._optional_path(video_map.get(str(pdf_path)))
            if video is None:
                video = ProjectFileService._optional_path(video_map.get(str(pdf)))
            result.append(ScoreItem(pdf_path, video))
        return result

    @staticmethod
    def _required_path(value: object) -> Path:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("cada PDF debe tener una ruta válida")
        return Path(value)

    @staticmethod
    def _optional_path(value: object) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            return None
        return Path(value)
