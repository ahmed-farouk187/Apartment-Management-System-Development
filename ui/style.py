# ui/style.py
# Student: Ahmed Saad - 24062019
# Global stylesheet and UI constants for PAMS

ROLE_COLORS = {
    "admin":       "#534AB7",
    "manager":     "#0F6E56",
    "front_desk":  "#185FA5",
    "finance":     "#854F0B",
    "maintenance": "#993C1D",
}

ROLE_LABELS = {
    "admin":       "Administrator",
    "manager":     "Manager",
    "front_desk":  "Front-desk Staff",
    "finance":     "Finance Manager",
    "maintenance": "Maintenance Staff",
}

PRIORITY_COLORS = {
    "low":    "#3B6D11",
    "medium": "#854F0B",
    "high":   "#993C1D",
    "urgent": "#A32D2D",
}

STATUS_COLORS = {
    "active":      "#0F6E56",
    "terminated":  "#993C1D",
    "expired":     "#5F5E5A",
    "paid":        "#3B6D11",
    "unpaid":      "#854F0B",
    "overdue":     "#A32D2D",
    "open":        "#185FA5",
    "assigned":    "#854F0B",
    "in_progress": "#534AB7",
    "resolved":    "#3B6D11",
    "closed":      "#5F5E5A",
}

STYLESHEET = """
QMainWindow, QDialog {
    background-color: #F8F7F4;
}

QWidget {
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 13px;
    color: #2C2C2A;
}

/* Sidebar */
#sidebar {
    background-color: #1E1E2E;
    min-width: 220px;
    max-width: 220px;
}
#sidebar QLabel#app_title {
    color: #EEEDFE;
    font-size: 15px;
    font-weight: 600;
    padding: 20px 16px 4px 16px;
}
#sidebar QLabel#user_role {
    color: #7F77DD;
    font-size: 11px;
    padding: 0 16px 16px 16px;
}
#sidebar QLabel#user_name {
    color: #AFA9EC;
    font-size: 12px;
    padding: 0 16px 4px 16px;
}

QPushButton#nav_btn {
    background: transparent;
    color: #AFA9EC;
    border: none;
    text-align: left;
    padding: 10px 16px;
    font-size: 13px;
    border-radius: 0;
}
QPushButton#nav_btn:hover {
    background-color: #2A2A3E;
    color: #EEEDFE;
}
QPushButton#nav_btn:checked {
    background-color: #534AB7;
    color: #EEEDFE;
    font-weight: 600;
}

/* Content area */
#content_area {
    background-color: #F8F7F4;
}

/* Cards */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E0DED6;
    border-radius: 8px;
    padding: 16px;
}

/* Page header */
QLabel#page_title {
    font-size: 20px;
    font-weight: 600;
    color: #1E1E2E;
}
QLabel#page_sub {
    font-size: 12px;
    color: #888780;
}

/* Buttons */
QPushButton {
    background-color: #534AB7;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3C3489;
}
QPushButton:pressed {
    background-color: #26215C;
}
QPushButton#btn_secondary {
    background-color: #F1EFE8;
    color: #2C2C2A;
    border: 1px solid #D3D1C7;
}
QPushButton#btn_secondary:hover {
    background-color: #D3D1C7;
}
QPushButton#btn_danger {
    background-color: #E24B4A;
    color: #FFFFFF;
}
QPushButton#btn_danger:hover {
    background-color: #A32D2D;
}
QPushButton#btn_success {
    background-color: #1D9E75;
    color: #FFFFFF;
}
QPushButton#btn_success:hover {
    background-color: #0F6E56;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #D3D1C7;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    color: #2C2C2A;
    selection-background-color: #CECBF6;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #534AB7;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #D3D1C7;
    selection-background-color: #EEEDFE;
    selection-color: #26215C;
}

/* Tables */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E0DED6;
    border-radius: 6px;
    gridline-color: #F1EFE8;
    selection-background-color: #EEEDFE;
    selection-color: #26215C;
    alternate-background-color: #F8F7F4;
}
QTableWidget::item {
    padding: 6px 10px;
    border: none;
}
QHeaderView::section {
    background-color: #F1EFE8;
    color: #5F5E5A;
    font-size: 11px;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #D3D1C7;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #F1EFE8;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #B4B2A9;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* Search bar */
QLineEdit#search_bar {
    background: #FFFFFF;
    border: 1px solid #D3D1C7;
    border-radius: 20px;
    padding: 7px 14px;
    font-size: 13px;
    min-width: 200px;
}

/* Stat cards */
QFrame#stat_card {
    background: #FFFFFF;
    border: 1px solid #E0DED6;
    border-radius: 10px;
    padding: 16px;
}
QLabel#stat_value {
    font-size: 28px;
    font-weight: 700;
    color: #1E1E2E;
}
QLabel#stat_label {
    font-size: 11px;
    color: #888780;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Badge labels */
QLabel#badge {
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* Tab widget */
QTabWidget::pane {
    border: 1px solid #E0DED6;
    border-radius: 6px;
    background: #FFFFFF;
}
QTabBar::tab {
    background: transparent;
    color: #888780;
    padding: 8px 16px;
    font-size: 13px;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    color: #534AB7;
    border-bottom: 2px solid #534AB7;
    font-weight: 600;
}
QTabBar::tab:hover {
    color: #2C2C2A;
}

/* Messages */
QLabel#msg_error {
    color: #A32D2D;
    font-size: 12px;
    padding: 4px 0;
}
QLabel#msg_success {
    color: #3B6D11;
    font-size: 12px;
    padding: 4px 0;
}

/* Separator */
QFrame[frameShape="4"] {
    color: #E0DED6;
}
"""
