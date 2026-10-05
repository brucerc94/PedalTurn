from __future__ import annotations

from .models import PlaylistState


class PageNavigator:
    """Business rules for two-page piano score navigation."""

    PAGES_PER_VIEW = 2

    def next(self, state: PlaylistState, page_count: int) -> bool:
        if page_count <= 0 or state.current_item is None:
            return False

        next_page = state.current_page + self.PAGES_PER_VIEW
        if next_page < page_count:
            state.current_page = next_page
            return True

        if state.current_index + 1 < len(state.items):
            state.current_index += 1
            state.current_page = 0
            return True

        return False

    def previous(self, state: PlaylistState, page_count: int) -> bool:
        if page_count <= 0 or state.current_item is None:
            return False

        previous_page = state.current_page - self.PAGES_PER_VIEW
        if previous_page >= 0:
            state.current_page = previous_page
            return True

        if state.current_index > 0:
            state.current_index -= 1
            state.current_page = self._last_spread_start(
                self._page_count_lookup(state.current_index, page_count)
            )
            return True

        return False

    @staticmethod
    def _last_spread_start(page_count: int) -> int:
        if page_count <= 0:
            return 0
        return max(0, ((page_count - 1) // 2) * 2)

    @staticmethod
    def _page_count_lookup(index: int, current_page_count: int) -> int:
        # The controller supplies the actual page count for the target PDF.
        # This fallback keeps the rule object pure; the controller may override
        # the returned page before rendering.
        return current_page_count
