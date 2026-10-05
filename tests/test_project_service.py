import json
import tempfile
import unittest
from pathlib import Path

from pdf_page_changer.core.models import ScoreItem
from pdf_page_changer.services.project_service import ProjectFileService


class ProjectFileServiceTests(unittest.TestCase):
    def test_round_trip_v2(self):
        service = ProjectFileService()
        items = [
            ScoreItem(Path("C:/Scores/song.pdf"), Path("C:/Videos/song.mp4")),
            ScoreItem(Path("C:/Scores/empty.pdf")),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "scores.vdp"
            service.save(project, items)
            loaded = service.load(project)
        self.assertEqual(loaded, items)

    def test_loads_legacy_project(self):
        service = ProjectFileService()
        legacy = {"pdf_queue": ["song.pdf"], "video_map": {"song.pdf": "song.mp4"}}
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "legacy.vdp"
            project.write_text(json.dumps(legacy), encoding="utf-8")
            loaded = service.load(project)
        self.assertEqual(loaded[0], ScoreItem(Path("song.pdf"), Path("song.mp4")))


if __name__ == "__main__":
    unittest.main()
