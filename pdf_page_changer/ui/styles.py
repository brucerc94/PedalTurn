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

QComboBox#floatingQueue, QComboBox {
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
"""
