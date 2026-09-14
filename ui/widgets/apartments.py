# ui/widgets/apartments.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from core.models.models import User
from core.services.services import ApartmentService
from ui.style import STATUS_COLORS

LOCATIONS = ["Bristol", "London", "Cardiff", "Manchester"]
APT_TYPES = ["studio", "1-bed", "2-bed", "3-bed", "4-bed"]


class ApartmentFormDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Register Apartment")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Register New Apartment")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.unit = QLineEdit()
        self.unit.setPlaceholderText("e.g. A101")
        self.unit.setFixedHeight(36)

        self.location = QComboBox()
        self.location.addItems(LOCATIONS)
        self.location.setFixedHeight(36)

        self.type_ = QComboBox()
        self.type_.addItems(APT_TYPES)
        self.type_.setFixedHeight(36)

        self.rooms = QSpinBox()
        self.rooms.setRange(0, 10)
        self.rooms.setValue(2)
        self.rooms.setFixedHeight(36)

        self.floor = QSpinBox()
        self.floor.setRange(1, 50)
        self.floor.setFixedHeight(36)

        self.rent = QDoubleSpinBox()
        self.rent.setRange(0, 99999)
        self.rent.setPrefix("£")
        self.rent.setValue(1000)
        self.rent.setFixedHeight(36)

        form.addRow("Unit number *", self.unit)
        form.addRow("Location *", self.location)
        form.addRow("Type *", self.type_)
        form.addRow("Rooms", self.rooms)
        form.addRow("Floor", self.floor)
        form.addRow("Monthly rent *", self.rent)
        layout.addLayout(form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("msg_error")
        layout.addWidget(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate(self):
        if not self.unit.text().strip():
            self.error_lbl.setText("Unit number is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "unit_number": self.unit.text().strip(),
            "location": self.location.currentText(),
            "type_": self.type_.currentText(),
            "num_rooms": self.rooms.value(),
            "floor": self.floor.value(),
            "monthly_rent": self.rent.value(),
        }


class ApartmentWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = ApartmentService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Apartment Management")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All locations"] + LOCATIONS)
        self.filter_combo.currentTextChanged.connect(self.refresh)
        hdr.addWidget(self.filter_combo)

        if self.user.role in ("admin", "manager"):
            add_btn = QPushButton("+ Add Apartment")
            add_btn.clicked.connect(self._add_apt)
            hdr.addWidget(add_btn)

        layout.addLayout(hdr)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Unit", "Location", "Type", "Rooms", "Rent/mo", "Status"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def refresh(self):
        loc = self.filter_combo.currentText()
        location = None if loc == "All locations" else loc
        apts = self._svc.get_all(location)
        self.table.setRowCount(0)
        for a in apts:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 40)
            self.table.setItem(r, 0, QTableWidgetItem(str(a.apartment_id)))
            self.table.setItem(r, 1, QTableWidgetItem(a.unit_number))
            self.table.setItem(r, 2, QTableWidgetItem(a.location))
            self.table.setItem(r, 3, QTableWidgetItem(a.type))
            self.table.setItem(r, 4, QTableWidgetItem(str(a.num_rooms)))
            self.table.setItem(r, 5, QTableWidgetItem(f"£{a.monthly_rent:,.2f}"))
            status = "Occupied" if a.is_occupied else "Available"
            st_item = QTableWidgetItem(status)
            color = "#993C1D" if a.is_occupied else "#3B6D11"
            st_item.setForeground(QColor(color))
            self.table.setItem(r, 6, st_item)

    def _add_apt(self):
        dlg = ApartmentFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._svc.create(**data)
            self.refresh()
