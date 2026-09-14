# ui/widgets/tenants.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QFrame, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from core.models.models import User
from core.services.services import TenantService, LeaseService, ApartmentService, NotificationService, ComplaintService
from ui.style import STATUS_COLORS


class EarlyExitDialog(QDialog):
    """Dialog to process a tenant early lease exit — 1 month notice + 5% penalty."""

    def __init__(self, parent, tenant_name: str, lease):
        super().__init__(parent)
        self.lease = lease
        self.setWindowTitle("Early Lease Exit")
        self.setMinimumWidth(420)
        self._build(tenant_name)

    def _build(self, tenant_name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Early Lease Exit Request")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        penalty = self.lease.early_exit_penalty()
        info = QLabel(
            f"<b>Tenant:</b> {tenant_name}<br>"
            f"<b>Lease ends:</b> {self.lease.end_date}<br>"
            f"<b>Monthly rent:</b> £{self.lease.monthly_rent:.2f}<br><br>"
            f"Per policy, the tenant must give <b>1 month notice</b> and pay a "
            f"<b>5% penalty</b> of their monthly rent.<br><br>"
            f"<span style='color:#A32D2D; font-size:15px; font-weight:700;'>"
            f"Penalty due: £{penalty:.2f}</span>"
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setStyleSheet(
            "line-height:1.5; padding:8px; background:#FFF9F0;"
            "border:1px solid #F5D6A0; border-radius:6px;"
        )
        layout.addWidget(info)

        note = QLabel("Confirming will terminate the lease and log the penalty.")
        note.setStyleSheet("color: #5F5E5A; font-size: 12px;")
        layout.addWidget(note)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_penalty(self) -> float:
        return self.lease.early_exit_penalty()


class TenantFormDialog(QDialog):
    def __init__(self, parent, user: User, tenant=None):
        super().__init__(parent)
        self.user = user
        self.tenant = tenant
        self.setWindowTitle("Edit Tenant" if tenant else "Register New Tenant")
        self.setMinimumWidth(480)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Edit Tenant" if self.tenant else "Register New Tenant")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.ni = QLineEdit(self.tenant.ni_number if self.tenant else "")
        self.ni.setPlaceholderText("e.g. AB123456C")
        if self.tenant:
            self.ni.setReadOnly(True)

        self.name = QLineEdit(self.tenant.name if self.tenant else "")
        self.phone = QLineEdit(self.tenant.phone if self.tenant else "")
        self.email = QLineEdit(self.tenant.email if self.tenant else "")
        self.occupation = QLineEdit(self.tenant.occupation if self.tenant else "")
        self.refs = QLineEdit(self.tenant.references_ if self.tenant else "")

        for w in [self.ni, self.name, self.phone, self.email, self.occupation, self.refs]:
            w.setFixedHeight(36)

        form.addRow("NI Number *", self.ni)
        form.addRow("Full Name *", self.name)
        form.addRow("Phone *", self.phone)
        form.addRow("Email *", self.email)
        form.addRow("Occupation", self.occupation)
        form.addRow("References", self.refs)
        layout.addLayout(form)

        # Lease section (only for new tenants)
        if not self.tenant:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #E0DED6;")
            layout.addWidget(sep)

            lease_title = QLabel("Lease Details")
            lease_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            layout.addWidget(lease_title)

            lease_form = QFormLayout()
            lease_form.setSpacing(10)

            apt_svc = ApartmentService()
            apts = apt_svc.get_available()
            self.apt_combo = QComboBox()
            self.apt_combo.setFixedHeight(36)
            for a in apts:
                self.apt_combo.addItem(
                    f"{a.unit_number} — {a.location} ({a.type}, £{a.monthly_rent:.0f}/mo)",
                    a.apartment_id
                )
            self._apts = apts

            self.start_date = QDateEdit(QDate.currentDate())
            self.start_date.setCalendarPopup(True)
            self.start_date.setFixedHeight(36)

            self.end_date = QDateEdit(QDate.currentDate().addMonths(12))
            self.end_date.setCalendarPopup(True)
            self.end_date.setFixedHeight(36)

            self.deposit = QDoubleSpinBox()
            self.deposit.setRange(0, 99999)
            self.deposit.setPrefix("£")
            self.deposit.setFixedHeight(36)
            if apts:
                self.deposit.setValue(apts[0].monthly_rent * 2)
            self.apt_combo.currentIndexChanged.connect(self._update_deposit)

            lease_form.addRow("Apartment *", self.apt_combo)
            lease_form.addRow("Start date *", self.start_date)
            lease_form.addRow("End date *", self.end_date)
            lease_form.addRow("Deposit", self.deposit)
            layout.addLayout(lease_form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("msg_error")
        layout.addWidget(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _update_deposit(self, idx):
        if self._apts and idx < len(self._apts):
            self.deposit.setValue(self._apts[idx].monthly_rent * 2)

    def _validate_and_accept(self):
        errors = []
        if not self.ni.text().strip():
            errors.append("NI number is required.")
        elif len(self.ni.text().strip()) < 9:
            errors.append("NI number must be at least 9 characters.")
        if not self.name.text().strip():
            errors.append("Name is required.")
        if not self.phone.text().strip():
            errors.append("Phone is required.")
        if "@" not in self.email.text():
            errors.append("Valid email is required.")
        if errors:
            self.error_lbl.setText(" | ".join(errors))
            return
        self.error_lbl.setText("")
        self.accept()

    def get_data(self) -> dict:
        d = {
            "ni": self.ni.text().strip(),
            "name": self.name.text().strip(),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "occupation": self.occupation.text().strip(),
            "references": self.refs.text().strip(),
        }
        if not self.tenant and hasattr(self, "apt_combo"):
            d["apartment_id"] = self.apt_combo.currentData()
            d["start_date"] = self.start_date.date().toString("yyyy-MM-dd")
            d["end_date"] = self.end_date.date().toString("yyyy-MM-dd")
            d["deposit"] = self.deposit.value()
            idx = self.apt_combo.currentIndex()
            d["monthly_rent"] = self._apts[idx].monthly_rent if self._apts else 0
        return d


class TenantWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = TenantService()
        self._lease_svc = LeaseService()
        self._apt_svc = ApartmentService()
        self._notif_svc = NotificationService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Tenant Management")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        self.search = QLineEdit()
        self.search.setObjectName("search_bar")
        self.search.setPlaceholderText("Search by name, email or NI...")
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self._search)
        hdr.addWidget(self.search)

        if self.user.role in ("front_desk", "admin"):
            self.add_btn = QPushButton("+ Register Tenant")
            self.add_btn.clicked.connect(self._add_tenant)
            hdr.addWidget(self.add_btn)

        layout.addLayout(hdr)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "NI Number", "Email", "Phone", "Occupation", "Actions"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 220)
        self.table.setRowHeight(0, 40)
        layout.addWidget(self.table)

    def refresh(self):
        tenants = self._svc.get_all()
        self._populate(tenants)

    def _search(self, query: str):
        if query.strip():
            results = self._svc.search(query)
        else:
            results = self._svc.get_all()
        self._populate(results)

    def _populate(self, tenants):
        self.table.setRowCount(0)
        for t in tenants:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 44)
            self.table.setItem(r, 0, QTableWidgetItem(str(t.tenant_id)))
            self.table.setItem(r, 1, QTableWidgetItem(t.name))
            self.table.setItem(r, 2, QTableWidgetItem(t.ni_number))
            self.table.setItem(r, 3, QTableWidgetItem(t.email))
            self.table.setItem(r, 4, QTableWidgetItem(t.phone))
            self.table.setItem(r, 5, QTableWidgetItem(t.occupation))

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            btn_style_sec = "QPushButton { min-width: 46px; padding: 0 8px; font-size: 12px; }"
            btn_style_dan = "QPushButton { min-width: 58px; padding: 0 8px; font-size: 12px; background: #E24B4A; color: #fff; border-radius: 5px; } QPushButton:hover { background: #A32D2D; }"
            btn_style_pri = "QPushButton { min-width: 42px; padding: 0 8px; font-size: 12px; }"

            if self.user.role in ("front_desk", "admin"):
                edit_btn = QPushButton("Edit")
                edit_btn.setObjectName("btn_secondary")
                edit_btn.setFixedHeight(28)
                edit_btn.setStyleSheet(btn_style_sec)
                edit_btn.clicked.connect(lambda _, tid=t.tenant_id: self._edit_tenant(tid))
                btn_layout.addWidget(edit_btn)

            if self.user.role == "admin":
                del_btn = QPushButton("Remove")
                del_btn.setFixedHeight(28)
                del_btn.setStyleSheet(btn_style_dan)
                del_btn.clicked.connect(lambda _, tid=t.tenant_id: self._remove_tenant(tid))
                btn_layout.addWidget(del_btn)

            view_btn = QPushButton("View")
            view_btn.setFixedHeight(28)
            view_btn.setStyleSheet(btn_style_pri)
            view_btn.clicked.connect(lambda _, tid=t.tenant_id: self._view_tenant(tid))
            btn_layout.addWidget(view_btn)

            # Early exit button (front_desk and admin)
            if self.user.role in ("front_desk", "admin"):
                exit_btn = QPushButton("Early Exit")
                exit_btn.setFixedHeight(28)
                exit_btn.setStyleSheet(
                    "QPushButton { min-width: 70px; padding: 0 8px; font-size: 12px;"
                    "background: #854F0B; color: #fff; border-radius: 5px; }"
                    "QPushButton:hover { background: #5C3608; }"
                )
                exit_btn.clicked.connect(lambda _, tid=t.tenant_id, tn=t.name: self._early_exit(tid, tn))
                btn_layout.addWidget(exit_btn)

            self.table.setCellWidget(r, 6, btn_widget)

    def _add_tenant(self):
        dlg = TenantFormDialog(self, self.user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            tid, err = self._svc.create(
                data["ni"], data["name"], data["phone"], data["email"],
                data["occupation"], data["references"], self.user.user_id
            )
            if err:
                QMessageBox.warning(self, "Error", err)
                return
            if "apartment_id" in data and data["apartment_id"]:
                self._lease_svc.create(
                    tid, data["apartment_id"], data["start_date"],
                    data["end_date"], data["monthly_rent"], data["deposit"]
                )
                self._apt_svc.assign_tenant(data["apartment_id"], tid)
            QMessageBox.information(self, "Success", f"Tenant '{data['name']}' registered successfully.")
            self.refresh()

    def _edit_tenant(self, tenant_id: int):
        tenant = self._svc.get_by_id(tenant_id)
        if not tenant:
            return
        dlg = TenantFormDialog(self, self.user, tenant)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._svc.update(tenant_id, data["name"], data["phone"],
                             data["email"], data["occupation"], data["references"])
            self.refresh()

    def _remove_tenant(self, tenant_id: int):
        reply = QMessageBox.question(
            self, "Confirm removal",
            "Remove this tenant and all associated records? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._svc.delete(tenant_id)
            self.refresh()

    def _view_tenant(self, tenant_id: int):
        tenant = self._svc.get_by_id(tenant_id)
        lease = self._lease_svc.get_by_tenant(tenant_id)
        if not tenant:
            return
        msg = (
            f"Name: {tenant.name}\n"
            f"NI: {tenant.ni_number}\n"
            f"Email: {tenant.email}\n"
            f"Phone: {tenant.phone}\n"
            f"Occupation: {tenant.occupation}\n\n"
        )
        if lease:
            msg += (
                f"Lease: #{lease.lease_id}\n"
                f"Apartment: #{lease.apartment_id}\n"
                f"Period: {lease.start_date} → {lease.end_date}\n"
                f"Rent: £{lease.monthly_rent:.2f}/mo\n"
                f"Days remaining: {lease.days_remaining()}\n"
                f"Status: {lease.status.upper()}"
            )
        else:
            msg += "No active lease."
        QMessageBox.information(self, f"Tenant: {tenant.name}", msg)

    def _early_exit(self, tenant_id: int, tenant_name: str):
        lease = self._lease_svc.get_by_tenant(tenant_id)
        if not lease:
            QMessageBox.warning(self, "No Active Lease", f"{tenant_name} has no active lease to terminate.")
            return
        dlg = EarlyExitDialog(self, tenant_name, lease)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            penalty = dlg.get_penalty()
            self._lease_svc.early_exit(lease.lease_id, penalty)
            self._apt_svc.vacate(lease.apartment_id)
            self._notif_svc.send(
                self.user.user_id,
                f"Early exit processed for {tenant_name}. Penalty: £{penalty:.2f}. "
                f"Apartment #{lease.apartment_id} is now available.",
                type_="warning", tenant_id=tenant_id
            )
            QMessageBox.information(
                self, "Early Exit Processed",
                f"Lease terminated for {tenant_name}.\n"
                f"Penalty applied: £{penalty:.2f}\n"
                f"Apartment #{lease.apartment_id} marked as available."
            )
            self.refresh()
