# ui/widgets/finance.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QDateEdit, QDoubleSpinBox, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from core.models.models import User
from core.services.services import FinanceService, TenantService, LeaseService, NotificationService
from ui.style import STATUS_COLORS


class GenerateInvoiceDialog(QDialog):
    def __init__(self, parent, tenants, leases):
        super().__init__(parent)
        self.setWindowTitle("Generate Invoice")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Generate Invoice")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.tenant_combo = QComboBox()
        self.tenant_combo.setFixedHeight(36)
        self._tenant_lease_map = {}
        for t in tenants:
            lease = next((l for l in leases if l.tenant_id == t.tenant_id), None)
            if lease:
                self.tenant_combo.addItem(f"{t.name} (Apt #{lease.apartment_id})", (t.tenant_id, lease.lease_id, lease.monthly_rent))
                self._tenant_lease_map[t.tenant_id] = lease
        self.tenant_combo.currentIndexChanged.connect(self._update_amount)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 99999)
        self.amount.setPrefix("£")
        self.amount.setFixedHeight(36)

        self.due_date = QDateEdit(QDate.currentDate().addMonths(1))
        self.due_date.setCalendarPopup(True)
        self.due_date.setFixedHeight(36)

        form.addRow("Tenant *", self.tenant_combo)
        form.addRow("Amount due *", self.amount)
        form.addRow("Due date *", self.due_date)
        layout.addLayout(form)
        self._update_amount(0)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _update_amount(self, idx):
        data = self.tenant_combo.currentData()
        if data:
            self.amount.setValue(data[2])

    def get_data(self) -> dict:
        data = self.tenant_combo.currentData()
        return {
            "tenant_id": data[0],
            "lease_id": data[1],
            "amount": self.amount.value(),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
        }


class FinanceWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = FinanceService()
        self._tenant_svc = TenantService()
        self._lease_svc = LeaseService()
        self._notif_svc = NotificationService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Finance & Billing")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        gen_btn = QPushButton("+ Generate Invoice")
        gen_btn.clicked.connect(self._generate_invoice)
        hdr.addWidget(gen_btn)

        alert_btn = QPushButton("Send Late Alerts")
        alert_btn.setObjectName("btn_danger")
        alert_btn.clicked.connect(self._send_late_alerts)
        hdr.addWidget(alert_btn)

        layout.addLayout(hdr)

        # Summary cards
        self.summary_row = QHBoxLayout()
        self.summary_row.setSpacing(12)
        layout.addLayout(self.summary_row)

        # Tabs
        tabs = QTabWidget()

        # All invoices
        self.inv_table = self._make_table(["ID", "Tenant ID", "Amount", "Due date", "Issued", "Status", "Actions"])
        tabs.addTab(self._wrap(self.inv_table), "All invoices")

        # Overdue
        self.overdue_table = self._make_table(["Invoice ID", "Tenant", "Email", "Amount", "Due date"])
        tabs.addTab(self._wrap(self.overdue_table), "Overdue")

        layout.addWidget(tabs)

    def _make_table(self, cols) -> QTableWidget:
        t = QTableWidget(0, len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Fix Actions column to a wide enough fixed size
        if "Actions" in cols:
            actions_col = cols.index("Actions")
            t.horizontalHeader().setSectionResizeMode(actions_col, QHeaderView.ResizeMode.Fixed)
            t.setColumnWidth(actions_col, 160)
        return t

    def _wrap(self, widget) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 8, 0, 0)
        l.addWidget(widget)
        return w

    def refresh(self):
        self._svc.mark_overdue()
        self._refresh_invoices()
        self._refresh_overdue()
        self._refresh_summary()

    def _refresh_summary(self):
        while self.summary_row.count():
            item = self.summary_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        summary = self._svc.financial_summary()
        for val, lbl, color in [
            (f"£{summary['collected']:,.0f}", "Collected", "#3B6D11"),
            (f"£{summary['pending']:,.0f}",   "Pending",   "#854F0B"),
            (str(summary["total_invoices"]),   "Invoices",  "#534AB7"),
        ]:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: #FFFFFF;
                    border: 1px solid #E0DED6;
                    border-top: 3px solid {color};
                    border-radius: 10px;
                    padding: 12px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            v = QLabel(val)
            v.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            v.setStyleSheet(f"color: {color};")
            cl.addWidget(v)
            l = QLabel(lbl.upper())
            l.setStyleSheet("color: #888780; font-size: 11px;")
            cl.addWidget(l)
            self.summary_row.addWidget(card)

    def _refresh_invoices(self):
        invoices = self._svc.get_invoices()
        self.inv_table.setRowCount(0)
        for inv in invoices:
            r = self.inv_table.rowCount()
            self.inv_table.insertRow(r)
            self.inv_table.setRowHeight(r, 44)
            self.inv_table.setItem(r, 0, QTableWidgetItem(str(inv.invoice_id)))
            self.inv_table.setItem(r, 1, QTableWidgetItem(str(inv.tenant_id)))
            self.inv_table.setItem(r, 2, QTableWidgetItem(f"£{inv.amount_due:,.2f}"))
            self.inv_table.setItem(r, 3, QTableWidgetItem(inv.due_date))
            self.inv_table.setItem(r, 4, QTableWidgetItem(inv.issued_date))
            st = QTableWidgetItem(inv.status.upper())
            st.setForeground(QColor(STATUS_COLORS.get(inv.status, "#2C2C2A")))
            self.inv_table.setItem(r, 5, st)

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(4, 2, 4, 2)
            if inv.status != "paid":
                pay_btn = QPushButton("Record Payment")
                pay_btn.setFixedHeight(30)
                pay_btn.setStyleSheet("""
                    QPushButton {
                        background: #1D9E75; color: #ffffff;
                        border: none; border-radius: 5px;
                        font-size: 12px; font-weight: 600;
                        padding: 0 10px; min-width: 130px;
                    }
                    QPushButton:hover { background: #0F6E56; }
                """)
                pay_btn.clicked.connect(lambda _, iid=inv.invoice_id, tid=inv.tenant_id: self._record_payment(iid, tid))
                btn_l.addWidget(pay_btn)
            else:
                done = QLabel("  Paid")
                done.setStyleSheet("color: #3B6D11; font-weight: 700; font-size: 13px; padding: 0 8px;")
                btn_l.addWidget(done)
            self.inv_table.setCellWidget(r, 6, btn_w)

    def _refresh_overdue(self):
        overdue = self._svc.get_overdue()
        self.overdue_table.setRowCount(0)
        for o in overdue:
            r = self.overdue_table.rowCount()
            self.overdue_table.insertRow(r)
            self.overdue_table.setItem(r, 0, QTableWidgetItem(str(o["invoice_id"])))
            self.overdue_table.setItem(r, 1, QTableWidgetItem(o.get("tenant_name", "")))
            self.overdue_table.setItem(r, 2, QTableWidgetItem(o.get("tenant_email", "")))
            self.overdue_table.setItem(r, 3, QTableWidgetItem(f"£{o['amount_due']:,.2f}"))
            self.overdue_table.setItem(r, 4, QTableWidgetItem(o["due_date"]))

    def _generate_invoice(self):
        tenants = self._tenant_svc.get_all()
        leases = self._lease_svc.get_all()
        dlg = GenerateInvoiceDialog(self, tenants, leases)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._svc.generate_invoice(
                data["tenant_id"], data["lease_id"],
                data["amount"], data["due_date"], self.user.user_id
            )
            QMessageBox.information(self, "Invoice Generated", "Invoice created successfully.")
            self.refresh()

    def _record_payment(self, invoice_id: int, tenant_id: int):
        reply = QMessageBox.question(
            self, "Record Payment",
            f"Mark invoice #{invoice_id} as paid?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            inv = next((i for i in self._svc.get_invoices(tenant_id) if i.invoice_id == invoice_id), None)
            amount = inv.amount_due if inv else 0
            self._svc.record_payment(invoice_id, amount, "bank_transfer", self.user.user_id)
            self.refresh()

    def _send_late_alerts(self):
        overdue = self._svc.get_overdue()
        if not overdue:
            QMessageBox.information(self, "No Overdue", "No overdue invoices found.")
            return
        for o in overdue:
            self._notif_svc.send(
                self.user.user_id,
                f"Late payment alert: Invoice #{o['invoice_id']} for £{o['amount_due']:.2f} is overdue.",
                type_="warning",
                tenant_id=o["tenant_id"]
            )
        QMessageBox.information(self, "Alerts Sent", f"Late payment alerts sent for {len(overdue)} invoice(s).")
