# ui/widgets/dashboard.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from core.models.models import User
from core.services.services import (
    TenantService, ApartmentService, FinanceService,
    MaintenanceService, LeaseService, NotificationService
)
from ui.style import STATUS_COLORS, PRIORITY_COLORS


class StatCard(QFrame):
    def __init__(self, value: str, label: str, accent: str = "#534AB7"):
        super().__init__()
        self.setObjectName("stat_card")
        self.setStyleSheet(f"""
            QFrame#stat_card {{
                background: #FFFFFF;
                border: 1px solid #E0DED6;
                border-top: 3px solid {accent};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat_value")
        val_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {accent};")
        layout.addWidget(val_lbl)

        lbl = QLabel(label.upper())
        lbl.setObjectName("stat_label")
        lbl.setStyleSheet("color: #888780; font-size: 11px; letter-spacing: 0.5px;")
        layout.addWidget(lbl)


class DashboardWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._tenant_svc = TenantService()
        self._apt_svc = ApartmentService()
        self._fin_svc = FinanceService()
        self._maint_svc = MaintenanceService()
        self._lease_svc = LeaseService()
        self._notif_svc = NotificationService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(28, 24, 28, 24)
        self._layout.setSpacing(20)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()
        sub = QLabel(f"Welcome back, {self.user.name}")
        sub.setObjectName("page_sub")
        hdr.addWidget(sub)

        # Notification bell
        self._notif_btn = QPushButton("🔔")
        self._notif_btn.setFixedSize(38, 38)
        self._notif_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; border: 1px solid #D3D1C7;
                border-radius: 19px; font-size: 16px;
            }
            QPushButton:hover { background: #EEEDFE; border-color: #534AB7; }
        """)
        self._notif_btn.setToolTip("View notifications")
        self._notif_btn.clicked.connect(self._show_notifications)
        hdr.addWidget(self._notif_btn)

        self._layout.addLayout(hdr)

        # Stats grid
        self._stats_grid = QGridLayout()
        self._stats_grid.setSpacing(14)
        self._layout.addLayout(self._stats_grid)

        # Lower section: notifications + expiring leases + open maintenance
        lower = QHBoxLayout()
        lower.setSpacing(16)

        # Expiring leases
        self._leases_frame = self._make_table_card("Leases expiring soon (30 days)",
            ["Tenant", "Apartment", "End date", "Days left"])
        lower.addWidget(self._leases_frame, 1)

        # Open maintenance
        self._maint_frame = self._make_table_card("Open maintenance requests",
            ["ID", "Description", "Priority", "Status"])
        lower.addWidget(self._maint_frame, 1)

        self._layout.addLayout(lower)
        self._layout.addStretch()

    def _make_table_card(self, title: str, columns: list) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet("""
            QFrame#card {
                background: #FFFFFF;
                border: 1px solid #E0DED6;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #1E1E2E;")
        layout.addWidget(lbl)

        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMaximumHeight(200)
        layout.addWidget(table)

        frame._table = table
        return frame

    def refresh(self):
        # Clear stats
        while self._stats_grid.count():
            item = self._stats_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tenants = self._tenant_svc.get_all()
        apts = self._apt_svc.get_all()
        occupied = sum(1 for a in apts if a.is_occupied)
        fin = self._fin_svc.financial_summary()
        overdue = self._fin_svc.get_overdue()
        maint_open = [m for m in self._maint_svc.get_all() if m.status in ("open", "assigned")]

        cards = [
            (str(len(tenants)),   "Total tenants",        "#534AB7"),
            (str(occupied),       "Occupied units",       "#0F6E56"),
            (f"£{fin['collected']:,.0f}", "Rent collected", "#185FA5"),
            (str(len(overdue)),   "Overdue invoices",     "#A32D2D"),
            (str(len(maint_open)),"Open maintenance",     "#854F0B"),
            (str(len(apts) - occupied), "Vacant units",   "#888780"),
        ]
        for i, (val, lbl, color) in enumerate(cards):
            card = StatCard(val, lbl, color)
            self._stats_grid.addWidget(card, i // 3, i % 3)

        # Expiring leases
        expiring = self._lease_svc.get_expiring_soon(30)
        t = self._leases_frame._table
        t.setRowCount(0)
        for row in expiring:
            r = t.rowCount()
            t.insertRow(r)
            t.setRowHeight(r, 36)
            t.setItem(r, 0, QTableWidgetItem(row.get("tenant_name", "")))
            t.setItem(r, 1, QTableWidgetItem(row.get("unit_number", "")))
            t.setItem(r, 2, QTableWidgetItem(str(row.get("end_date", ""))))
            days_left = row.get("days_left", 0) or 0
            days_item = QTableWidgetItem(f"{days_left} days")
            # Colour code: red if <= 7 days, amber if <= 14, green otherwise
            if days_left <= 7:
                days_item.setForeground(QColor("#A32D2D"))
            elif days_left <= 14:
                days_item.setForeground(QColor("#854F0B"))
            else:
                days_item.setForeground(QColor("#3B6D11"))
            t.setItem(r, 3, days_item)

        # Open maintenance
        t2 = self._maint_frame._table
        t2.setRowCount(0)
        for req in maint_open[:8]:
            r = t2.rowCount()
            t2.insertRow(r)
            t2.setItem(r, 0, QTableWidgetItem(f"#{req.request_id}"))
            desc = req.description[:40] + "..." if len(req.description) > 40 else req.description
            t2.setItem(r, 1, QTableWidgetItem(desc))
            pri_item = QTableWidgetItem(req.priority.upper())
            pri_item.setForeground(QColor(PRIORITY_COLORS.get(req.priority, "#2C2C2A")))
            t2.setItem(r, 2, pri_item)
            t2.setItem(r, 3, QTableWidgetItem(req.status))

        # Update notification badge
        unread = self._notif_svc.get_unread(self.user.user_id)
        count = len(unread)
        self._notif_btn.setText(f"🔔 {count}" if count else "🔔")
        if count:
            self._notif_btn.setStyleSheet("""
                QPushButton {
                    background: #534AB7; color: #ffffff;
                    border: none; border-radius: 19px; font-size: 13px; font-weight: 700;
                }
                QPushButton:hover { background: #3C3489; }
            """)
        else:
            self._notif_btn.setStyleSheet("""
                QPushButton {
                    background: #FFFFFF; border: 1px solid #D3D1C7;
                    border-radius: 19px; font-size: 16px;
                }
                QPushButton:hover { background: #EEEDFE; border-color: #534AB7; }
            """)

    def _show_notifications(self):
        unread = self._notif_svc.get_unread(self.user.user_id)
        if not unread:
            QMessageBox.information(self, "Notifications", "No unread notifications.")
            return
        msg_lines = []
        for n in unread[:10]:
            icon = "⚠️" if n.type == "warning" else "ℹ️"
            msg_lines.append(f"{icon}  {n.message}\n   {str(n.sent_at)[:16]}")
            self._notif_svc.mark_read(n.notif_id)
        QMessageBox.information(
            self, f"Notifications ({len(unread)} unread)",
            "\n\n".join(msg_lines)
        )
        self.refresh()
