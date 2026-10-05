from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ScoreItem:
    pdf_path: Path
    video_path: Path | None = None

    @property
    def display_name(self) -> str:
        return self.pdf_path.name


@dataclass
class PlaylistState:
    items: list[ScoreItem] = field(default_factory=list)
    current_index: int = 0
    current_page: int = 0

    @property
    def current_item(self) -> ScoreItem | None:
        if not self.items:
            return None
        if not 0 <= self.current_index < len(self.items):
            return None
        return self.items[self.current_index]

    def set_items(self, items: list[ScoreItem]) -> None:
        self.items = items
        self.current_index = 0
        self.current_page = 0

    def replace_current_item(self, item: ScoreItem) -> None:
        if self.current_item is None:
            return
        self.items[self.current_index] = item

    def remove_current_item(self) -> None:
        if not self.items:
            return
        self.items.pop(self.current_index)
        if self.current_index >= len(self.items):
            self.current_index = max(0, len(self.items) - 1)
        self.current_page = 0
