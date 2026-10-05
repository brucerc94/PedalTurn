APPLICATION_STYLE = """
QMainWindow, QDialog {
    background: #12161c;
    color: #e8edf2;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 10pt;
    color: #e8edf2;
}

QPushButton {
    background: #252d37;
    border: 1px solid #343e4a;
    border-radius: 7px;
    padding: 8px 10px;
}

QPushButton:hover {
    background: #303a47;
}

QPushButton:pressed {
    background: #1f2630;
}

QPushButton#accentButton {
    background: #2c71d9;
    border-color: #2c71d9;
    color: white;
}

QPushButton#accentButton:hover {
    background: #3881ee;
}

QPushButton#dangerButton {
    color: #ffb4b4;
}

QFrame#floatingPanel {
    background: rgba(15, 20, 26, 235);
    border: 1px solid #3b4654;
    border-radius: 10px;
}

QToolButton#floatingHandle {
    background: rgba(15, 20, 26, 225);
    border: 1px solid #3b4654;
    border-radius: 8px;
    padding: 7px 10px;
    color: #e8edf2;
    font-size: 12pt;
}

QToolButton#floatingHandle:hover {
    background: #252d37;
}

QPushButton#playlistButton {
    background: #202833;
    border: 1px solid #3b4654;
    text-align: left;
    min-width: 220px;
}

QPushButton#playlistButton:hover {
    background: #2b3541;
}

QFrame#playlistPopup {
    background: #121820;
    border: 1px solid #3b4654;
    border-radius: 10px;
}

QLabel#playlistPopupTitle {
    color: #f4f7fa;
    font-size: 9pt;
    font-weight: 700;
}

QLabel#playlistPopupCount {
    color: #7f8c9d;
}

QListWidget#playlistList {
    background: #0f141a;
    border: 1px solid #2a313b;
    border-radius: 7px;
    padding: 5px;
    outline: none;
}

QListWidget#playlistList::item {
    padding: 9px 8px;
    border-radius: 6px;
}

QListWidget#playlistList::item:hover {
    background: #252d37;
}

QListWidget#playlistList::item:selected {
    background: #2c71d9;
    color: white;
}

QComboBox {
    background: #0f141a;
    border: 1px solid #343e4a;
    border-radius: 6px;
    padding: 7px;
}

QLabel#floatingPageInfo {
    color: #c8d2dc;
    padding: 0 5px;
}

QLabel#floatingStatus {
    color: #7f8c9d;
    padding: 0 4px;
}

QListWidget {
    background: #0f141a;
    border: 1px solid #2a313b;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}

QListWidget::item {
    padding: 9px 8px;
    border-radius: 6px;
}

QListWidget::item:selected {
    background: #2c71d9;
    color: white;
}

QLabel#sourceLink {
    background: rgba(0, 0, 0, 150);
    color: #aeb9c6;
    border: 1px solid rgba(59, 70, 84, 170);
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 8pt;
}

QLabel#sourceLink a {
    color: #b9c8d8;
    text-decoration: none;
}

QLabel#sourceLink a:hover {
    color: #ffffff;
    text-decoration: underline;
}
"""
