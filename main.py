import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from database.db import init_db
from ui.windows.login_window import LoginWindow
from ui.windows.main_window import MainWindow
from ui.style import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PAMS")
    app.setOrganizationName("Paragon")
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 13))

    init_db()

    login = LoginWindow()

    def on_login(user):
        login.close()
        main_win = MainWindow(user)
        main_win.show()
        app._main_win = main_win

    login.login_success.connect(on_login)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()