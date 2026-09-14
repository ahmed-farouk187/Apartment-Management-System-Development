# ui/widgets/complaints.py
# Student: Ahmed Saad - 24062019
# Complaints management widget — log, view, resolve tenant complaints

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from core.models.models import User
from core.services.services import ComplaintService, TenantService
from ui.style import STATUS_COLORS


class LogComplaintDialog(QDialog):
    """Dialog for front-desk staff to log a new complaint."""

    def __init__(self, parent, user: User):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Log Tenant Complaint")
        self.setMinimumWidth(460)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Log Tenant Complaint")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        tenant_svc = TenantService()
        self._tenants = tenant_svc.get_all()
        self.tenant_combo = QComboBox()
        self.tenant_combo.setFixedHeight(36)
        for t in self._tenants:
            self.tenant_combo.addItem(f"{t.name} (#{t.tenant_id})", t.tenant_id)

        self.description = QTextEdit()
        self.description.setFixedHeight(90)
        self.description.setPlaceholderText("Describe the complaint in detail...")

        form.addRow("Tenant *", self.tenant_combo)
        form.addRow("Description *", self.description)
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
        if not self.description.toPlainText().strip():
            self.error_lbl.setText("Description is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "tenant_id": self.tenant_combo.currentData(),
            "description": self.description.toPlainText().strip(),
        }


class ResolveComplaintDialog(QDialog):
    """Dialog for staff to mark a complaint as resolved with notes."""

    def __init__(self, parent, complaint_id: int):
        super().__init__(parent)
        self.complaint_id = complaint_id
        self.setWindowTitle(f"Resolve Complaint #{complaint_id}")
        self.setMinimumWidth(400)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel(f"Resolve Complaint #{self.complaint_id}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.resolution = QTextEdit()
        self.resolution.setFixedHeight(90)
        self.resolution.setPlaceholderText("Describe how the complaint was resolved...")

        form.addRow("Resolution notes *", self.resolution)
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
        if not self.resolution.toPlainText().strip():
            self.error_lbl.setText("Resolution notes are required.")
            return
        self.accept()

    def get_data(self) -> str:
        return self.resolution.toPlainText().strip()


class ComplaintWidget(QWidget):
    """Full complaints management widget — log, filter, and resolve complaints."""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = ComplaintService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Complaints")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        # Filter by status
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "open", "resolved"])
        self.filter_combo.currentTextChanged.connect(self.refresh)
        hdr.addWidget(self.filter_combo)

        # Log new complaint (front-desk and admin)
        if self.user.role in ("front_desk", "admin"):
            log_btn = QPushButton("+ Log Complaint")
            log_btn.clicked.connect(self._log_complaint)
            hdr.addWidget(log_btn)

        layout.addLayout(hdr)

        # Stats row
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)
        layout.addLayout(self.stats_row)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tenant", "Description", "Date Logged", "Status", "Resolution", "Actions"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 45)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 130)
        layout.addWidget(self.table)

    def refresh(self):
        self._refresh_stats()
        self._refresh_table()

    def _refresh_stats(self):
        while self.stats_row.count():
            item = self.stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_complaints = self._svc.get_all()
        open_count = sum(1 for c in all_complaints if c["status"] == "open")
        resolved_count = sum(1 for c in all_complaints if c["status"] == "resolved")

        for val, lbl, color in [
            (str(len(all_complaints)), "Total Complaints", "#534AB7"),
            (str(open_count),          "Open",             "#A32D2D"),
            (str(resolved_count),      "Resolved",         "#3B6D11"),
        ]:
            from PyQt6.QtWidgets import QFrame
            from PyQt6.QtGui import QFont as _F
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
        status_filter = self.filter_combo.currentText()
        complaints = self._svc.get_all(status_filter if status_filter != "All" else None)

        self.table.setRowCount(0)
        for c in complaints:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 44)

            self.table.setItem(r, 0, QTableWidgetItem(str(c["complaint_id"])))
            self.table.setItem(r, 1, QTableWidgetItem(c.get("tenant_name", str(c["tenant_id"]))))

            desc = c["description"]
            short_desc = desc[:40] + "..." if len(desc) > 40 else desc
            self.table.setItem(r, 2, QTableWidgetItem(short_desc))
            self.table.setItem(r, 3, QTableWidgetItem(str(c["date_logged"])[:10]))

            st = QTableWidgetItem(c["status"].upper())
            st.setForeground(QColor(STATUS_COLORS.get(c["status"], "#2C2C2A")))
            self.table.setItem(r, 4, st)

            resolution = c.get("resolution") or "—"
            short_res = resolution[:35] + "..." if len(resolution) > 35 else resolution
            self.table.setItem(r, 5, QTableWidgetItem(short_res))

            # Action buttons
            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 2, 2, 2)
            btn_l.setSpacing(4)

            if c["status"] == "open" and self.user.role in ("front_desk", "admin", "maintenance"):
                resolve_btn = QPushButton("Resolve")
                resolve_btn.setFixedHeight(30)
                resolve_btn.setStyleSheet("""
                    QPushButton {
                        background: #1D9E75; color: #ffffff;
                        border: none; border-radius: 5px;
                        font-size: 12px; font-weight: 600;
                        padding: 0 10px; min-width: 80px;
                    }
                    QPushButton:hover { background: #0F6E56; }
                """)
                resolve_btn.clicked.connect(
                    lambda _, cid=c["complaint_id"]: self._resolve_complaint(cid)
                )
                btn_l.addWidget(resolve_btn)
            else:
                lbl = QLabel("✓ Done" if c["status"] == "resolved" else "—")
                lbl.setStyleSheet("color: #3B6D11; font-weight: 600; padding: 0 8px;")
                btn_l.addWidget(lbl)

            self.table.setCellWidget(r, 6, btn_w)

    def _log_complaint(self):
        dlg = LogComplaintDialog(self, self.user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._svc.create(data["tenant_id"], data["description"], self.user.user_id)
            QMessageBox.information(self, "Complaint Logged", "Complaint has been recorded successfully.")
            self.refresh()

    def _resolve_complaint(self, complaint_id: int):
        dlg = ResolveComplaintDialog(self, complaint_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            resolution = dlg.get_data()
            self._svc.resolve(complaint_id, resolution)
            QMessageBox.information(self, "Resolved", f"Complaint #{complaint_id} marked as resolved.")
            self.refresh()
