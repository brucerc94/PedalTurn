from __future__ import annotations

import sys
from pathlib import Path


class AppPaths:
    @staticmethod
    def base_directory() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[2]

    @classmethod
    def config_file(cls) -> Path:
        return cls.base_directory() / "config.json"
