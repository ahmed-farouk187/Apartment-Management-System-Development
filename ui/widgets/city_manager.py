# ui/widgets/city_manager.py
# Student: Ahmed Saad - 24062019
# Manager-only widget to expand business to new cities / locations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.models.models import User
from core.services.services import CityService, ApartmentService, UserService


class AddCityDialog(QDialog):
    """Dialog for manager to register a new city / office location."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Expand Business — Add New City")
        self.setMinimumWidth(420)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Add New Office Location")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        sub = QLabel(
            "Register a new city where Paragon will operate.\n"
            "This creates the location so apartments and staff can be assigned."
        )
        sub.setStyleSheet("color: #5F5E5A; font-size: 12px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(10)

        self.city_name = QLineEdit()
        self.city_name.setPlaceholderText("e.g. Edinburgh, Leeds, Birmingham...")
        self.city_name.setFixedHeight(36)

        self.office_address = QLineEdit()
        self.office_address.setPlaceholderText("e.g. 12 High Street, Edinburgh, EH1 1AA")
        self.office_address.setFixedHeight(36)

        self.manager_name = QLineEdit()
        self.manager_name.setPlaceholderText("Name of the city office manager")
        self.manager_name.setFixedHeight(36)

        form.addRow("City name *", self.city_name)
        form.addRow("Office address", self.office_address)
        form.addRow("Local manager", self.manager_name)
        layout.addLayout(form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("msg_error")
        layout.addWidget(self.error_lbl)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate(self):
        if not self.city_name.text().strip():
            self.error_lbl.setText("City name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "city": self.city_name.text().strip(),
            "address": self.office_address.text().strip(),
            "manager": self.manager_name.text().strip(),
        }


class CityManagerWidget(QWidget):
    """Manager-only page: view all locations and expand to new cities."""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._city_svc = CityService()
        self._apt_svc = ApartmentService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Business Expansion")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        expand_btn = QPushButton("+ Add New City")
        expand_btn.clicked.connect(self._add_city)
        hdr.addWidget(expand_btn)
        layout.addLayout(hdr)

        sub = QLabel("Manage Paragon office locations across the UK. Add new cities to expand operations.")
        sub.setStyleSheet("color: #888780; font-size: 12px;")
        layout.addWidget(sub)

        # Stats row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        layout.addLayout(self.stats_row)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["City", "Office Address", "Local Manager", "Apartments", "Occupancy"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def refresh(self):
        self._refresh_stats()
        self._refresh_table()

    def _refresh_stats(self):
        while self.stats_row.count():
            item = self.stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cities = self._city_svc.get_all()
        apts = self._apt_svc.get_all()
        total_apts = len(apts)
        occupied = sum(1 for a in apts if a.is_occupied)

        for val, lbl, color in [
            (str(len(cities)),  "Active Cities",    "#534AB7"),
            (str(total_apts),   "Total Apartments",  "#185FA5"),
            (str(occupied),     "Occupied Units",    "#3B6D11"),
        ]:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: #FFFFFF;
                    border: 1px solid #E0DED6;
                    border-top: 3px solid {color};
                    border-radius: 10px;
                }}
            """)
            from PyQt6.QtWidgets import QVBoxLayout as _VL
            from PyQt6.QtGui import QFont as _F
            cl = _VL(card)
            cl.setContentsMargins(16, 12, 16, 12)
            v = QLabel(val)
            v.setFont(_F("Segoe UI", 22, _F.Weight.Bold))
            v.setStyleSheet(f"color: {color};")
            cl.addWidget(v)
            lb = QLabel(lbl.upper())
            lb.setStyleSheet("color: #888780; font-size: 11px;")
            cl.addWidget(lb)
            self.stats_row.addWidget(card)

    def _refresh_table(self):
        cities = self._city_svc.get_all()
        apts_all = self._apt_svc.get_all()

        self.table.setRowCount(0)
        for city in cities:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 44)

            city_apts = [a for a in apts_all if a.location == city["city"]]
            occupied = sum(1 for a in city_apts if a.is_occupied)
            rate = f"{round(occupied / len(city_apts) * 100)}%" if city_apts else "0%"

            self.table.setItem(r, 0, QTableWidgetItem(city["city"]))
            self.table.setItem(r, 1, QTableWidgetItem(city.get("address") or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(city.get("manager") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(str(len(city_apts))))
            self.table.setItem(r, 4, QTableWidgetItem(f"{occupied}/{len(city_apts)}  ({rate})"))

    def _add_city(self):
        dlg = AddCityDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            success, msg = self._city_svc.add_city(data["city"], data["address"], data["manager"])
            if success:
                QMessageBox.information(
                    self, "City Added",
                    f"'{data['city']}' has been registered as a new Paragon location.\n"
                    f"Administrators and apartments can now be assigned to this city."
                )
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", msg)
