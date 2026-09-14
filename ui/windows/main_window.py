# ui/windows/main_window.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from core.models.models import User
from ui.style import STYLESHEET, ROLE_LABELS, ROLE_COLORS
from ui.widgets.dashboard import DashboardWidget
from ui.widgets.tenants import TenantWidget
from ui.widgets.apartments import ApartmentWidget
from ui.widgets.finance import FinanceWidget
from ui.widgets.maintenance import MaintenanceWidget
from ui.widgets.reports import ReportWidget
from ui.widgets.users import UserManagementWidget
from ui.widgets.complaints import ComplaintWidget
from ui.widgets.city_manager import CityManagerWidget


# Maps role → which nav items are visible
ROLE_NAV = {
    "front_desk":  ["Dashboard", "Tenants", "Complaints", "Maintenance"],
    "finance":     ["Dashboard", "Finance", "Reports"],
    "maintenance": ["Dashboard", "Maintenance", "Complaints"],
    "admin":       ["Dashboard", "Tenants", "Apartments", "Finance", "Complaints", "Maintenance", "Reports", "Users"],
    "manager":     ["Dashboard", "Apartments", "Reports", "City Manager"],
}

NAV_ICONS = {
    "Dashboard":    "⊞",
    "Tenants":      "◎",
    "Apartments":   "⬡",
    "Finance":      "◈",
    "Complaints":   "⚑",
    "Maintenance":  "⚙",
    "Reports":      "▤",
    "Users":        "◉",
    "City Manager": "🌐",
}


class MainWindow(QMainWindow):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.setWindowTitle("PAMS — Paragon Apartment Management")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(STYLESHEET)
        self._nav_buttons = {}
        self._build_ui()
        self._navigate("Dashboard")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        # Content
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")
        self._pages = {}

        allowed = ROLE_NAV.get(self.user.role, ["Dashboard"])

        page_map = {
            "Dashboard":    lambda: DashboardWidget(self.user),
            "Tenants":      lambda: TenantWidget(self.user),
            "Apartments":   lambda: ApartmentWidget(self.user),
            "Finance":      lambda: FinanceWidget(self.user),
            "Complaints":   lambda: ComplaintWidget(self.user),
            "Maintenance":  lambda: MaintenanceWidget(self.user),
            "Reports":      lambda: ReportWidget(self.user),
            "Users":        lambda: UserManagementWidget(self.user),
            "City Manager": lambda: CityManagerWidget(self.user),
        }
        for name in allowed:
            if name in page_map:
                widget = page_map[name]()
                self._pages[name] = widget
                self.stack.addWidget(widget)

        root.addWidget(self.stack)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App branding
        brand = QWidget()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 20, 16, 16)
        brand_layout.setSpacing(2)

        title_lbl = QLabel("PAMS")
        title_lbl.setObjectName("app_title")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        brand_layout.addWidget(title_lbl)

        role_lbl = QLabel(ROLE_LABELS.get(self.user.role, self.user.role))
        role_lbl.setObjectName("user_role")
        brand_layout.addWidget(role_lbl)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #2A2A3E; margin: 0 0px;")
        brand_layout.addWidget(sep1)

        layout.addWidget(brand)

        # Nav items
        allowed = ROLE_NAV.get(self.user.role, ["Dashboard"])
        for name in allowed:
            btn = QPushButton(f"  {NAV_ICONS.get(name, '•')}  {name}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda checked, n=name: self._navigate(n))
            self._nav_buttons[name] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # User info + logout at bottom
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #2A2A3E;")
        layout.addWidget(sep2)

        user_info = QWidget()
        ui_layout = QVBoxLayout(user_info)
        ui_layout.setContentsMargins(16, 10, 16, 6)
        ui_layout.setSpacing(2)

        name_lbl = QLabel(self.user.name)
        name_lbl.setStyleSheet("color: #EEEDFE; font-size: 12px; font-weight: 600;")
        ui_layout.addWidget(name_lbl)

        loc_lbl = QLabel(f"📍 {self.user.location}")
        loc_lbl.setStyleSheet("color: #7F77DD; font-size: 11px;")
        ui_layout.addWidget(loc_lbl)

        logout_btn = QPushButton("Sign out")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888780;
                border: 1px solid #2A2A3E;
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
                margin-top: 8px;
            }
            QPushButton:hover { color: #E24B4A; border-color: #E24B4A; }
        """)
        logout_btn.clicked.connect(self._logout)
        ui_layout.addWidget(logout_btn)

        layout.addWidget(user_info)
        return sidebar

    def _navigate(self, name: str):
        # Update button states
        for n, btn in self._nav_buttons.items():
            btn.setChecked(n == name)

        if name in self._pages:
            self.stack.setCurrentWidget(self._pages[name])
            # Refresh if page supports it
            page = self._pages[name]
            if hasattr(page, "refresh"):
                page.refresh()

    def _logout(self):
        from ui.windows.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.login_success.connect(self._reopen)
        self.login_window.show()
        self.close()

    def _reopen(self, user: User):
        self.login_window.close()
        self.new_main = MainWindow(user)
        self.new_main.show()
