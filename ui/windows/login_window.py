# ui/windows/login_window.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.services.services import AuthService
from core.models.models import User


class LoginWindow(QWidget):
    login_success = pyqtSignal(object)  # emits User

    def __init__(self):
        super().__init__()
        self._auth = AuthService()
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("PAMS — Login")
        self.setFixedSize(440, 560)
        self.setStyleSheet("""
            QWidget { background-color: #F8F7F4; font-family: 'Segoe UI', Arial, sans-serif; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Top accent bar
        accent = QFrame()
        accent.setFixedHeight(6)
        accent.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #534AB7, stop:1 #1D9E75);"
        )
        outer.addWidget(accent)

        # Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E0DED6;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 32, 40, 32)
        card_layout.setSpacing(0)

        # Title
        title = QLabel("PAMS")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E1E2E; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        sub = QLabel("Paragon Apartment Management System")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #888780; font-size: 12px; border: none; margin-bottom: 28px;")
        card_layout.addWidget(sub)

        card_layout.addSpacing(4)

        # Email label + input
        lbl_email = QLabel("Email address")
        lbl_email.setStyleSheet(
            "color: #5F5E5A; font-size: 12px; font-weight: 600; border: none; margin-bottom: 4px;"
        )
        card_layout.addWidget(lbl_email)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g. admin1@pams.com")
        self.email_input.setStyleSheet(self._input_style())
        self.email_input.setFixedHeight(44)
        card_layout.addWidget(self.email_input)

        card_layout.addSpacing(14)

        # Password label + input
        lbl_pw = QLabel("Password")
        lbl_pw.setStyleSheet(
            "color: #5F5E5A; font-size: 12px; font-weight: 600; border: none; margin-bottom: 4px;"
        )
        card_layout.addWidget(lbl_pw)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Enter your password")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setStyleSheet(self._input_style())
        self.pw_input.setFixedHeight(44)
        self.pw_input.returnPressed.connect(self._attempt_login)
        card_layout.addWidget(self.pw_input)

        card_layout.addSpacing(6)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #A32D2D; font-size: 12px; border: none;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.error_lbl)

        card_layout.addSpacing(10)

        # Login button
        self.login_btn = QPushButton("Sign in")
        self.login_btn.setFixedHeight(46)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #534AB7; color: #FFFFFF; border: none;
                border-radius: 8px; font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background: #3C3489; }
            QPushButton:pressed { background: #26215C; }
        """)
        self.login_btn.clicked.connect(self._attempt_login)
        card_layout.addWidget(self.login_btn)

        card_layout.addSpacing(20)

        # Credentials hint
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E0DED6; border: none; background: #E0DED6; max-height: 1px;")
        card_layout.addWidget(sep)

        card_layout.addSpacing(12)

        hint_title = QLabel("Demo accounts")
        hint_title.setStyleSheet("color: #5F5E5A; font-size: 11px; font-weight: 600; border: none;")
        hint_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(hint_title)

        credentials = [
            ("admin1@pams.com",       "admin123",        "Administrator"),
            ("frontdesk1@pams.com",   "desk123",         "Front-desk Staff"),
            ("finance1@pams.com",     "finance123",      "Finance Manager"),
            ("maintenance1@pams.com", "maintenance123",  "Maintenance Staff"),
            ("manager1@pams.com",     "manager123",      "Manager"),
        ]
        for email, pw, role in credentials:
            row = QLabel(f"{email}  /  {pw}  —  {role}")
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.setStyleSheet("color: #B4B2A9; font-size: 10px; border: none;")
            card_layout.addWidget(row)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(28, 28, 28, 28)
        wrapper.addWidget(card)
        outer.addLayout(wrapper)

    def _input_style(self) -> str:
        return """
            QLineEdit {
                border: 1px solid #D3D1C7; border-radius: 8px;
                padding: 10px 14px; font-size: 14px; color: #2C2C2A;
                background: #FAFAF9;
            }
            QLineEdit:focus { border: 1.5px solid #534AB7; background: #FFFFFF; }
        """

    def _attempt_login(self):
        email = self.email_input.text().strip()
        pw = self.pw_input.text()
        if not email or not pw:
            self.error_lbl.setText("Please enter your email and password.")
            return
        user = self._auth.login(email, pw)
        if user:
            self.error_lbl.setText("")
            self.login_success.emit(user)
        else:
            self.error_lbl.setText("Incorrect email or password. Please try again.")
            self.pw_input.clear()
