# core/models/models.py
# Student: Ahmed Saad - 24062019
# Data models (dataclasses) matching the class diagram

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List


@dataclass
class User:
    user_id: int
    name: str
    email: str
    role: str
    location: str
    is_active: bool = True
    password_hash: str = ""

    def get_role(self) -> str:
        return self.role

    def is_admin_or_manager(self) -> bool:
        return self.role in ("admin", "manager")


@dataclass
class Tenant:
    tenant_id: int
    ni_number: str
    name: str
    phone: str
    email: str
    occupation: str = ""
    references_: str = ""
    created_at: str = ""

    def validate(self) -> list:
        errors = []
        if not self.ni_number or len(self.ni_number) < 9:
            errors.append("Invalid NI number (min 9 chars).")
        if not self.name.strip():
            errors.append("Name is required.")
        if "@" not in self.email:
            errors.append("Invalid email address.")
        if not self.phone.strip():
            errors.append("Phone number is required.")
        return errors


@dataclass
class Apartment:
    apartment_id: int
    unit_number: str
    location: str
    type: str
    num_rooms: int
    floor: int
    monthly_rent: float
    is_occupied: bool = False

    def get_occupancy_status(self) -> str:
        return "Occupied" if self.is_occupied else "Available"


@dataclass
class LeaseAgreement:
    lease_id: int
    tenant_id: int
    apartment_id: int
    start_date: str
    end_date: str
    monthly_rent: float
    deposit: float
    status: str = "active"
    early_exit: bool = False
    penalty_paid: float = 0.0

    def is_active(self) -> bool:
        return self.status == "active"

    def early_exit_penalty(self) -> float:
        return round(self.monthly_rent * 0.05, 2)

    def days_remaining(self) -> int:
        try:
            end = date.fromisoformat(self.end_date)
            delta = end - date.today()
            return max(delta.days, 0)
        except Exception:
            return 0


@dataclass
class Invoice:
    invoice_id: int
    tenant_id: int
    lease_id: int
    amount_due: float
    due_date: str
    issued_date: str
    status: str = "unpaid"

    def is_overdue(self) -> bool:
        try:
            return self.status != "paid" and date.fromisoformat(self.due_date) < date.today()
        except Exception:
            return False

    def mark_paid(self):
        self.status = "paid"

    def generate_receipt(self) -> str:
        return (
            f"RECEIPT — Invoice #{self.invoice_id}\n"
            f"Tenant ID : {self.tenant_id}\n"
            f"Amount    : £{self.amount_due:.2f}\n"
            f"Due date  : {self.due_date}\n"
            f"Status    : {self.status.upper()}\n"
        )


@dataclass
class Payment:
    payment_id: int
    invoice_id: int
    amount_paid: float
    payment_date: str
    method: str = "bank_transfer"

    def get_receipt(self) -> str:
        return (
            f"PAYMENT RECEIPT — Payment #{self.payment_id}\n"
            f"Invoice   : #{self.invoice_id}\n"
            f"Amount    : £{self.amount_paid:.2f}\n"
            f"Date      : {self.payment_date}\n"
            f"Method    : {self.method}\n"
        )


@dataclass
class MaintenanceRequest:
    request_id: int
    tenant_id: int
    apartment_id: int
    description: str
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[int] = None
    submitted_date: str = ""
    scheduled_date: Optional[str] = None
    resolved_date: Optional[str] = None
    resolution_notes: Optional[str] = None
    time_taken_hrs: Optional[float] = None
    cost: float = 0.0

    def is_resolved(self) -> bool:
        return self.status == "resolved"


@dataclass
class Complaint:
    complaint_id: int
    tenant_id: int
    description: str
    date_logged: str
    status: str = "open"
    resolution: Optional[str] = None


@dataclass
class Notification:
    notif_id: int
    recipient_id: int
    message: str
    type: str = "info"
    is_read: bool = False
    sent_at: str = ""
    tenant_id: Optional[int] = None


@dataclass
class Report:
    report_id: int
    report_type: str
    generated_by: int
    generated_at: str
    location_filter: str
    data: dict = field(default_factory=dict)
