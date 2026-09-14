# ui/widgets/users.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QComboBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from core.models.models import User
from core.services.services import UserService
from ui.style import ROLE_LABELS, ROLE_COLORS

ROLES = ["front_desk", "finance", "maintenance", "admin", "manager"]
LOCATIONS = ["Bristol", "London", "Cardiff", "Manchester"]


class CreateUserDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Create User Account")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Create User Account")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name = QLineEdit()
        self.name.setFixedHeight(36)
        self.email = QLineEdit()
        self.email.setFixedHeight(36)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setFixedHeight(36)
        self.role = QComboBox()
        self.role.addItems(ROLES)
        self.role.setFixedHeight(36)
        self.location = QComboBox()
        self.location.addItems(LOCATIONS)
        self.location.setFixedHeight(36)

        form.addRow("Full name *", self.name)
        form.addRow("Email *", self.email)
        form.addRow("Password *", self.password)
        form.addRow("Role *", self.role)
        form.addRow("Location *", self.location)
        layout.addLayout(form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("msg_error")
        layout.addWidget(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate(self):
        errors = []
        if not self.name.text().strip():
            errors.append("Name required.")
        if "@" not in self.email.text():
            errors.append("Valid email required.")
        if len(self.password.text()) < 6:
            errors.append("Password min 6 chars.")
        if errors:
            self.error_lbl.setText(" ".join(errors))
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "email": self.email.text().strip(),
            "password": self.password.text(),
            "role": self.role.currentText(),
            "location": self.location.currentText(),
        }


class UserManagementWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = UserService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("User Management")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        add_btn = QPushButton("+ Create User")
        add_btn.clicked.connect(self._create_user)
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Role", "Location", "Actions"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 160)
        layout.addWidget(self.table)

    def refresh(self):
        location = None if self.user.role == "manager" else self.user.location
        users = self._svc.get_all(location)
        self.table.setRowCount(0)
        for u in users:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 44)
            self.table.setItem(r, 0, QTableWidgetItem(str(u.user_id)))
            self.table.setItem(r, 1, QTableWidgetItem(u.name))
            self.table.setItem(r, 2, QTableWidgetItem(u.email))

            role_item = QTableWidgetItem(ROLE_LABELS.get(u.role, u.role))
            role_item.setForeground(QColor(ROLE_COLORS.get(u.role, "#2C2C2A")))
            self.table.setItem(r, 3, role_item)
            self.table.setItem(r, 4, QTableWidgetItem(u.location))

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 2, 2, 2)
            btn_l.setSpacing(4)

            if u.user_id != self.user.user_id:
                deact_btn = QPushButton("Deactivate")
                deact_btn.setObjectName("btn_danger")
                deact_btn.setFixedHeight(28)
                deact_btn.clicked.connect(lambda _, uid=u.user_id: self._deactivate(uid))
                btn_l.addWidget(deact_btn)

            self.table.setCellWidget(r, 5, btn_w)

    def _create_user(self):
        dlg = CreateUserDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self._svc.create(
                    data["name"], data["email"], data["password"],
                    data["role"], data["location"]
                )
                QMessageBox.information(self, "Created", f"User '{data['name']}' created.")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create user: {e}")

    def _deactivate(self, user_id: int):
        reply = QMessageBox.question(
            self, "Deactivate User",
            "Deactivate this user account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._svc.deactivate(user_id)
            self.refresh()
