# ui/widgets/reports.py
# Student: Ahmed Saad - 24062019

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QPushButton, QTabWidget
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from core.models.models import User
from core.services.services import ReportService, FinanceService

LOCATIONS = ["All", "Bristol", "London", "Cardiff", "Manchester"]


class ReportWidget(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._svc = ReportService()
        self._fin_svc = FinanceService()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Reports")
        title.setObjectName("page_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()
        self.loc_filter = QComboBox()
        self.loc_filter.addItems(LOCATIONS)
        self.loc_filter.currentTextChanged.connect(self.refresh)
        hdr.addWidget(QLabel("Location:"))
        hdr.addWidget(self.loc_filter)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        tabs = QTabWidget()

        # Occupancy
        self.occ_widget = QWidget()
        occ_layout = QVBoxLayout(self.occ_widget)
        occ_layout.setContentsMargins(8, 8, 8, 8)
        self.occ_table = self._make_table(["Location", "Total", "Occupied", "Available", "Occupancy rate"])
        occ_layout.addWidget(self.occ_table)
        tabs.addTab(self.occ_widget, "Occupancy")

        # Financial
        self.fin_widget = QWidget()
        fin_layout = QVBoxLayout(self.fin_widget)
        fin_layout.setContentsMargins(8, 8, 8, 8)
        self.fin_cards = QHBoxLayout()
        fin_layout.addLayout(self.fin_cards)
        tabs.addTab(self.fin_widget, "Financial summary")

        # Maintenance costs
        self.maint_widget = QWidget()
        maint_layout = QVBoxLayout(self.maint_widget)
        maint_layout.setContentsMargins(8, 8, 8, 8)
        self.maint_table = self._make_table(["Priority", "Status", "Cost", "Time (hrs)", "Location"])
        maint_layout.addWidget(self.maint_table)
        tabs.addTab(self.maint_widget, "Maintenance costs")

        layout.addWidget(tabs)

    def _make_table(self, cols):
        t = QTableWidget(0, len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return t

    def refresh(self):
        loc_text = self.loc_filter.currentText()
        location = None if loc_text == "All" else loc_text

        # Occupancy
        occ = self._svc.occupancy_report(location)
        self.occ_table.setRowCount(0)
        for loc, data in occ.items():
            r = self.occ_table.rowCount()
            self.occ_table.insertRow(r)
            self.occ_table.setRowHeight(r, 40)
            self.occ_table.setItem(r, 0, QTableWidgetItem(loc))
            self.occ_table.setItem(r, 1, QTableWidgetItem(str(data["total"])))
            self.occ_table.setItem(r, 2, QTableWidgetItem(str(data["occupied"])))
            self.occ_table.setItem(r, 3, QTableWidgetItem(str(data["available"])))
            rate_item = QTableWidgetItem(f"{data['rate']}%")
            color = "#3B6D11" if data["rate"] >= 70 else "#854F0B" if data["rate"] >= 40 else "#A32D2D"
            rate_item.setForeground(QColor(color))
            self.occ_table.setItem(r, 4, rate_item)

        # Financial summary cards
        while self.fin_cards.count():
            item = self.fin_cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        summary = self._fin_svc.financial_summary(location)
        for val, lbl, color in [
            (f"£{summary['collected']:,.2f}", "Total collected", "#3B6D11"),
            (f"£{summary['pending']:,.2f}",   "Total pending",   "#854F0B"),
            (str(summary["total_invoices"]),   "Total invoices",  "#534AB7"),
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
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 16, 20, 16)
            v = QLabel(val)
            v.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            v.setStyleSheet(f"color: {color};")
            cl.addWidget(v)
            l = QLabel(lbl.upper())
            l.setStyleSheet("color: #888780; font-size: 11px;")
            cl.addWidget(l)
            self.fin_cards.addWidget(card)

        # Maintenance costs
        maint = self._svc.maintenance_cost_report(location)
        self.maint_table.setRowCount(0)
        for m in maint:
            r = self.maint_table.rowCount()
            self.maint_table.insertRow(r)
            self.maint_table.setRowHeight(r, 40)
            self.maint_table.setItem(r, 0, QTableWidgetItem(str(m.get("priority", ""))))
            self.maint_table.setItem(r, 1, QTableWidgetItem(str(m.get("status", ""))))
            cost = m.get("cost") or 0
            self.maint_table.setItem(r, 2, QTableWidgetItem(f"£{cost:,.2f}"))
            time_ = m.get("time_taken_hrs") or 0
            self.maint_table.setItem(r, 3, QTableWidgetItem(f"{time_:.1f}"))
            self.maint_table.setItem(r, 4, QTableWidgetItem(str(m.get("location", ""))))
