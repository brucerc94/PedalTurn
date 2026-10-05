from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .controllers.app_controller import AppController
from .services.config_service import ConfigService
from .utils.paths import AppPaths
from .ui.styles import APPLICATION_STYLE


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Page Changer Piano")
    app.setApplicationDisplayName("PDF Page Changer Piano")
    app.setStyleSheet(APPLICATION_STYLE)

    config_service = ConfigService(AppPaths.config_file())
    controller = AppController(config_service)
    app.aboutToQuit.connect(controller.shutdown)
    controller.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
