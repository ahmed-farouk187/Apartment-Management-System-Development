# ui/widgets/maintenance.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from core.models.models import User
from core.services.services import MaintenanceService, TenantService, ApartmentService, UserService, NotificationService
from ui.style import PRIORITY_COLORS, STATUS_COLORS

PRIORITIES = ["low", "medium", "high", "urgent"]


class LogRequestDialog(QDialog):
    def __init__(self, parent, user: User):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Log Maintenance Request")
        self.setMinimumWidth(440)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Log Maintenance Request")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        tenant_svc = TenantService()
        apt_svc = ApartmentService()

        self.tenant_combo = QComboBox()
        self.tenant_combo.setFixedHeight(36)
        self._tenants = tenant_svc.get_all()
        for t in self._tenants:
            self.tenant_combo.addItem(f"{t.name} (#{t.tenant_id})", t.tenant_id)

        self.apt_combo = QComboBox()
        self.apt_combo.setFixedHeight(36)
        self._apts = apt_svc.get_all()
        for a in self._apts:
            self.apt_combo.addItem(f"{a.unit_number} — {a.location}", a.apartment_id)

        self.desc = QTextEdit()
        self.desc.setFixedHeight(80)
        self.desc.setPlaceholderText("Describe the issue...")

        self.priority = QComboBox()
        self.priority.addItems(PRIORITIES)
        self.priority.setCurrentText("medium")
        self.priority.setFixedHeight(36)

        form.addRow("Tenant *", self.tenant_combo)
        form.addRow("Apartment *", self.apt_combo)
        form.addRow("Description *", self.desc)
        form.addRow("Priority", self.priority)
        layout.addLayout(form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("msg_error")
        layout.addWidget(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate(self):
        if not self.desc.toPlainText().strip():
            self.error_lbl.setText("Description is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "tenant_id": self.tenant_combo.currentData(),
            "apartment_id": self.apt_combo.currentData(),
            "description": self.desc.toPlainText().strip(),
            "priority": self.priority.currentText(),
        }


class ResolveDialog(QDialog):
    def __init__(self, parent, request_id):
        super().__init__(parent)
        self.request_id = request_id
        self.setWindowTitle(f"Resolve Request #{request_id}")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel(f"Resolve Maintenance Request #{request_id}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(80)
        self.notes.setPlaceholderText("Resolution notes...")

        self.time_hrs = QDoubleSpinBox()
        self.time_hrs.setRange(0, 999)
        self.time_hrs.setSuffix(" hrs")
        self.time_hrs.setFixedHeight(36)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 99999)
        self.cost.setPrefix("£")
        self.cost.setFixedHeight(36)

        form.addRow("Resolution notes *", self.notes)
        form.addRow("Time taken", self.time_hrs)
        form.addRow("Cost", self.cost)
        layout.addLayout(form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("msg_error")
        layout.addWidget(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate(self):
        if not self.notes.toPlainText().strip():
            self.error_lbl.setText("Notes are required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "notes": self.notes.toPlainText().strip(),
            "time_hrs": self.time_hrs.value(),
            "cost": self.cost.value(),
        }


class MaintenanceWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = MaintenanceService()
        self._notif_svc = NotificationService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Maintenance")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        self.filter_status = QComboBox()
        self.filter_status.addItems(["All", "open", "assigned", "in_progress", "resolved"])
        self.filter_status.currentTextChanged.connect(self.refresh)
        hdr.addWidget(self.filter_status)

        if self.user.role in ("front_desk", "admin"):
            log_btn = QPushButton("+ Log Request")
            log_btn.clicked.connect(self._log_request)
            hdr.addWidget(log_btn)

        layout.addLayout(hdr)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tenant", "Apartment", "Description", "Priority", "Status", "Submitted", "Actions"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 160)
        layout.addWidget(self.table)

    def refresh(self):
        reqs = self._svc.get_all()
        status_filter = self.filter_status.currentText()
        if status_filter != "All":
            reqs = [r for r in reqs if r.status == status_filter]

        self.table.setRowCount(0)
        for req in reqs:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 44)
            self.table.setItem(r, 0, QTableWidgetItem(str(req.request_id)))
            self.table.setItem(r, 1, QTableWidgetItem(str(req.tenant_id)))
            self.table.setItem(r, 2, QTableWidgetItem(str(req.apartment_id)))
            desc = req.description[:35] + "..." if len(req.description) > 35 else req.description
            self.table.setItem(r, 3, QTableWidgetItem(desc))

            pri = QTableWidgetItem(req.priority.upper())
            pri.setForeground(QColor(PRIORITY_COLORS.get(req.priority, "#2C2C2A")))
            self.table.setItem(r, 4, pri)

            st = QTableWidgetItem(req.status.upper())
            st.setForeground(QColor(STATUS_COLORS.get(req.status, "#2C2C2A")))
            self.table.setItem(r, 5, st)
            self.table.setItem(r, 6, QTableWidgetItem(str(req.submitted_date)[:10]))

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 2, 2, 2)
            btn_l.setSpacing(4)

            if self.user.role in ("maintenance", "admin") and req.status in ("open", "assigned", "in_progress"):
                resolve_btn = QPushButton("Resolve Issue")
                resolve_btn.setFixedHeight(30)
                resolve_btn.setStyleSheet("""
                    QPushButton {
                        background: #1D9E75; color: #ffffff;
                        border: none; border-radius: 5px;
                        font-size: 12px; font-weight: 600;
                        padding: 0 10px; min-width: 110px;
                    }
                    QPushButton:hover { background: #0F6E56; }
                """)
                resolve_btn.clicked.connect(lambda _, rid=req.request_id, tid=req.tenant_id: self._resolve(rid, tid))
                btn_l.addWidget(resolve_btn)

            self.table.setCellWidget(r, 7, btn_w)

    def _log_request(self):
        dlg = LogRequestDialog(self, self.user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._svc.create(
                data["tenant_id"], data["apartment_id"],
                data["description"], data["priority"], self.user.user_id
            )
            QMessageBox.information(self, "Logged", "Maintenance request logged successfully.")
            self.refresh()

    def _resolve(self, request_id: int, tenant_id: int):
        dlg = ResolveDialog(self, request_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._svc.resolve(request_id, data["notes"], data["time_hrs"], data["cost"])
            self._notif_svc.send(
                self.user.user_id,
                f"Maintenance request #{request_id} has been resolved: {data['notes']}",
                type_="info", tenant_id=tenant_id
            )
            QMessageBox.information(self, "Resolved", "Request marked as resolved.")
            self.refresh()
