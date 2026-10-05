from __future__ import annotations


class PageNavigator:
    """Rules for advancing through a score two pages at a time."""

    PAGES_PER_VIEW = 2

    def next_within_document(self, current_page: int, page_count: int) -> int | None:
        candidate = current_page + self.PAGES_PER_VIEW
        return candidate if candidate < page_count else None

    def previous_within_document(self, current_page: int) -> int | None:
        candidate = current_page - self.PAGES_PER_VIEW
        return candidate if candidate >= 0 else None

    @staticmethod
    def last_spread_start(page_count: int) -> int:
        if page_count <= 0:
            return 0
        return ((page_count - 1) // 2) * 2
