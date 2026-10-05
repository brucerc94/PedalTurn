from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .controllers.app_controller import AppController
from .services.config_service import ConfigService
from .ui.styles import APPLICATION_STYLE
from .utils.paths import AppPaths


APP_NAME = "PedalTurn"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)

    icon_path = AppPaths.icon_file()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    app.setStyleSheet(APPLICATION_STYLE)

    controller = AppController(ConfigService(AppPaths.config_file()))
    app.aboutToQuit.connect(controller.shutdown)
    controller.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
