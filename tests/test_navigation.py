import unittest
from pathlib import Path

from pdf_page_changer.core.models import PlaylistState, ScoreItem
from pdf_page_changer.core.navigation import PageNavigator


class PageNavigatorTests(unittest.TestCase):
    def setUp(self):
        self.navigator = PageNavigator()
        self.state = PlaylistState([ScoreItem(Path("one.pdf")), ScoreItem(Path("two.pdf"))])

    def test_next_moves_two_pages(self):
        self.assertEqual(self.navigator.next_within_document(0, 6), 2)

    def test_next_returns_none_at_last_spread(self):
        self.assertIsNone(self.navigator.next_within_document(4, 5))

    def test_previous_moves_two_pages(self):
        self.assertEqual(self.navigator.previous_within_document(4), 2)

    def test_previous_returns_none_before_first_page(self):
        self.assertIsNone(self.navigator.previous_within_document(0))

    def test_last_spread_start_handles_odd_page_count(self):
        self.assertEqual(self.navigator.last_spread_start(5), 4)
        self.assertEqual(self.navigator.last_spread_start(6), 4)


if __name__ == "__main__":
    unittest.main()
