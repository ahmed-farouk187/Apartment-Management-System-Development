# core/services/services.py
# Student: Ahmed Saad - 24062019
# Business-logic services — one per domain area

import hashlib
from datetime import date, datetime
from typing import Optional, List

from database.db import get_connection
from core.models.models import (
    User, Tenant, Apartment, LeaseAgreement,
    Invoice, Payment, MaintenanceRequest, Complaint, Notification
)


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
class AuthService:
    def login(self, email: str, password: str) -> Optional[User]:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND is_active=1", (email,)
        ).fetchone()
        conn.close()
        if row and row["password_hash"] == _hash(password):
            return User(
                user_id=row["user_id"], name=row["name"], email=row["email"],
                role=row["role"], location=row["location"],
                is_active=bool(row["is_active"]), password_hash=row["password_hash"]
            )
        return None


# ──────────────────────────────────────────────
# User Management
# ──────────────────────────────────────────────
class UserService:
    def get_all(self, location: Optional[str] = None) -> List[User]:
        conn = get_connection()
        q = "SELECT * FROM users"
        params = ()
        if location:
            q += " WHERE location=?"
            params = (location,)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [User(r["user_id"], r["name"], r["email"], r["role"],
                     r["location"], bool(r["is_active"])) for r in rows]

    def create(self, name, email, password, role, location) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, location) VALUES (?,?,?,?,?)",
            (name, email, _hash(password), role, location)
        )
        conn.commit()
        uid = cur.lastrowid
        conn.close()
        return uid

    def deactivate(self, user_id: int):
        conn = get_connection()
        conn.execute("UPDATE users SET is_active=0 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

    def update_role(self, user_id: int, role: str):
        conn = get_connection()
        conn.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
        conn.commit()
        conn.close()


# ──────────────────────────────────────────────
# Tenant Management
# ──────────────────────────────────────────────
class TenantService:
    def get_all(self) -> List[Tenant]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM tenants ORDER BY name").fetchall()
        conn.close()
        return [Tenant(r["tenant_id"], r["ni_number"], r["name"], r["phone"],
                       r["email"], r["occupation"] or "", r["references_"] or "",
                       r["created_at"]) for r in rows]

    def get_by_id(self, tenant_id: int) -> Optional[Tenant]:
        conn = get_connection()
        r = conn.execute("SELECT * FROM tenants WHERE tenant_id=?", (tenant_id,)).fetchone()
        conn.close()
        if r:
            return Tenant(r["tenant_id"], r["ni_number"], r["name"], r["phone"],
                          r["email"], r["occupation"] or "", r["references_"] or "")
        return None

    def create(self, ni, name, phone, email, occupation, references, created_by) -> tuple:
        conn = get_connection()
        # Check NI uniqueness
        exists = conn.execute("SELECT 1 FROM tenants WHERE ni_number=?", (ni,)).fetchone()
        if exists:
            conn.close()
            return None, "NI number already registered."
        cur = conn.execute(
            "INSERT INTO tenants (ni_number, name, phone, email, occupation, references_, created_by) VALUES (?,?,?,?,?,?,?)",
            (ni, name, phone, email, occupation, references, created_by)
        )
        conn.commit()
        tid = cur.lastrowid
        conn.close()
        return tid, None

    def update(self, tenant_id, name, phone, email, occupation, references):
        conn = get_connection()
        conn.execute(
            "UPDATE tenants SET name=?, phone=?, email=?, occupation=?, references_=? WHERE tenant_id=?",
            (name, phone, email, occupation, references, tenant_id)
        )
        conn.commit()
        conn.close()

    def delete(self, tenant_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM tenants WHERE tenant_id=?", (tenant_id,))
        conn.commit()
        conn.close()

    def search(self, query: str) -> List[Tenant]:
        conn = get_connection()
        q = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM tenants WHERE name LIKE ? OR email LIKE ? OR ni_number LIKE ?", (q, q, q)
        ).fetchall()
        conn.close()
        return [Tenant(r["tenant_id"], r["ni_number"], r["name"], r["phone"],
                       r["email"], r["occupation"] or "", r["references_"] or "") for r in rows]


# ──────────────────────────────────────────────
# Apartment Management
# ──────────────────────────────────────────────
class ApartmentService:
    def get_all(self, location: Optional[str] = None) -> List[Apartment]:
        conn = get_connection()
        q = "SELECT * FROM apartments"
        params = ()
        if location:
            q += " WHERE location=?"
            params = (location,)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [Apartment(r["apartment_id"], r["unit_number"], r["location"],
                          r["type"], r["num_rooms"], r["floor"],
                          r["monthly_rent"], bool(r["is_occupied"])) for r in rows]

    def get_available(self, location: Optional[str] = None) -> List[Apartment]:
        conn = get_connection()
        q = "SELECT * FROM apartments WHERE is_occupied=0"
        params = ()
        if location:
            q += " AND location=?"
            params = (location,)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [Apartment(r["apartment_id"], r["unit_number"], r["location"],
                          r["type"], r["num_rooms"], r["floor"],
                          r["monthly_rent"], False) for r in rows]

    def create(self, unit_number, location, type_, num_rooms, floor, monthly_rent) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO apartments (unit_number, location, type, num_rooms, floor, monthly_rent) VALUES (?,?,?,?,?,?)",
            (unit_number, location, type_, num_rooms, floor, monthly_rent)
        )
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return aid

    def assign_tenant(self, apartment_id: int, tenant_id: int):
        conn = get_connection()
        conn.execute("UPDATE apartments SET is_occupied=1 WHERE apartment_id=?", (apartment_id,))
        conn.commit()
        conn.close()

    def vacate(self, apartment_id: int):
        conn = get_connection()
        conn.execute("UPDATE apartments SET is_occupied=0 WHERE apartment_id=?", (apartment_id,))
        conn.commit()
        conn.close()


# ──────────────────────────────────────────────
# Lease Service
# ──────────────────────────────────────────────
class LeaseService:
    def get_all(self) -> List[LeaseAgreement]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM leases ORDER BY end_date").fetchall()
        conn.close()
        return [LeaseAgreement(r["lease_id"], r["tenant_id"], r["apartment_id"],
                               r["start_date"], r["end_date"], r["monthly_rent"],
                               r["deposit"], r["status"]) for r in rows]

    def get_by_tenant(self, tenant_id: int) -> Optional[LeaseAgreement]:
        conn = get_connection()
        r = conn.execute(
            "SELECT * FROM leases WHERE tenant_id=? AND status='active'", (tenant_id,)
        ).fetchone()
        conn.close()
        if r:
            return LeaseAgreement(r["lease_id"], r["tenant_id"], r["apartment_id"],
                                  r["start_date"], r["end_date"], r["monthly_rent"],
                                  r["deposit"], r["status"])
        return None

    def create(self, tenant_id, apartment_id, start_date, end_date, monthly_rent, deposit) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO leases (tenant_id, apartment_id, start_date, end_date, monthly_rent, deposit) VALUES (?,?,?,?,?,?)",
            (tenant_id, apartment_id, start_date, end_date, monthly_rent, deposit)
        )
        conn.commit()
        lid = cur.lastrowid
        conn.close()
        return lid

    def early_exit(self, lease_id: int, penalty: float):
        conn = get_connection()
        conn.execute(
            "UPDATE leases SET status='terminated', early_exit=1, penalty_paid=? WHERE lease_id=?",
            (penalty, lease_id)
        )
        conn.commit()
        conn.close()

    def get_expiring_soon(self, days: int = 30) -> List[dict]:
        conn = get_connection()
        rows = conn.execute("""
            SELECT l.*, t.name as tenant_name, a.unit_number,
                   CAST(julianday(l.end_date) - julianday('now') AS INTEGER) as days_left
            FROM leases l
            JOIN tenants t ON l.tenant_id = t.tenant_id
            JOIN apartments a ON l.apartment_id = a.apartment_id
            WHERE l.status='active'
              AND date(l.end_date) <= date('now', ? || ' days')
            ORDER BY l.end_date
        """, (str(days),)).fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# Finance / Payment Service
# ──────────────────────────────────────────────
class FinanceService:
    def generate_invoice(self, tenant_id, lease_id, amount, due_date, created_by) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO invoices (tenant_id, lease_id, amount_due, due_date, status, created_by) VALUES (?,?,?,?,'unpaid',?)",
            (tenant_id, lease_id, amount, due_date, created_by)
        )
        conn.commit()
        iid = cur.lastrowid
        conn.close()
        return iid

    def record_payment(self, invoice_id, amount, method, recorded_by) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO payments (invoice_id, amount_paid, method, recorded_by) VALUES (?,?,?,?)",
            (invoice_id, amount, method, recorded_by)
        )
        conn.execute("UPDATE invoices SET status='paid' WHERE invoice_id=?", (invoice_id,))
        conn.commit()
        pid = cur.lastrowid
        conn.close()
        return pid

    def get_invoices(self, tenant_id: Optional[int] = None) -> List[Invoice]:
        conn = get_connection()
        if tenant_id:
            rows = conn.execute("SELECT * FROM invoices WHERE tenant_id=?", (tenant_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM invoices ORDER BY due_date DESC").fetchall()
        conn.close()
        return [Invoice(r["invoice_id"], r["tenant_id"], r["lease_id"],
                        r["amount_due"], r["due_date"], r["issued_date"], r["status"]) for r in rows]

    def get_overdue(self) -> List[dict]:
        conn = get_connection()
        rows = conn.execute("""
            SELECT i.*, t.name as tenant_name, t.email as tenant_email
            FROM invoices i
            JOIN tenants t ON i.tenant_id = t.tenant_id
            WHERE i.status != 'paid' AND i.due_date < date('now')
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def mark_overdue(self):
        conn = get_connection()
        conn.execute(
            "UPDATE invoices SET status='overdue' WHERE status='unpaid' AND due_date < date('now')"
        )
        conn.commit()
        conn.close()

    def financial_summary(self, location: Optional[str] = None) -> dict:
        conn = get_connection()
        base = """
            SELECT
              SUM(CASE WHEN i.status='paid' THEN i.amount_due ELSE 0 END) as collected,
              SUM(CASE WHEN i.status!='paid' THEN i.amount_due ELSE 0 END) as pending,
              COUNT(*) as total_invoices
            FROM invoices i
            JOIN leases l ON i.lease_id = l.lease_id
            JOIN apartments a ON l.apartment_id = a.apartment_id
        """
        params = ()
        if location:
            base += " WHERE a.location=?"
            params = (location,)
        row = conn.execute(base, params).fetchone()
        conn.close()
        return {
            "collected": row["collected"] or 0,
            "pending": row["pending"] or 0,
            "total_invoices": row["total_invoices"] or 0,
        }


# ──────────────────────────────────────────────
# Maintenance Service
# ──────────────────────────────────────────────
class MaintenanceService:
    def get_all(self, location: Optional[str] = None) -> List[MaintenanceRequest]:
        conn = get_connection()
        if location:
            rows = conn.execute("""
                SELECT mr.* FROM maintenance_requests mr
                JOIN apartments a ON mr.apartment_id = a.apartment_id
                WHERE a.location=? ORDER BY mr.submitted_date DESC
            """, (location,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM maintenance_requests ORDER BY submitted_date DESC"
            ).fetchall()
        conn.close()
        return [self._row_to_obj(r) for r in rows]

    def create(self, tenant_id, apartment_id, description, priority, logged_by) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO maintenance_requests (tenant_id, apartment_id, description, priority, logged_by) VALUES (?,?,?,?,?)",
            (tenant_id, apartment_id, description, priority, logged_by)
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def assign(self, request_id, staff_id, scheduled_date):
        conn = get_connection()
        conn.execute(
            "UPDATE maintenance_requests SET assigned_to=?, scheduled_date=?, status='assigned' WHERE request_id=?",
            (staff_id, scheduled_date, request_id)
        )
        conn.commit()
        conn.close()

    def resolve(self, request_id, notes, time_hrs, cost):
        conn = get_connection()
        conn.execute(
            """UPDATE maintenance_requests SET status='resolved', resolution_notes=?,
               resolved_date=date('now'), time_taken_hrs=?, cost=? WHERE request_id=?""",
            (notes, time_hrs, cost, request_id)
        )
        conn.commit()
        conn.close()

    def get_cost_summary(self) -> dict:
        conn = get_connection()
        row = conn.execute(
            "SELECT SUM(cost) as total, AVG(time_taken_hrs) as avg_time, COUNT(*) as total_requests FROM maintenance_requests"
        ).fetchone()
        conn.close()
        return {
            "total_cost": row["total"] or 0,
            "avg_time_hrs": row["avg_time"] or 0,
            "total_requests": row["total_requests"] or 0,
        }

    def _row_to_obj(self, r) -> MaintenanceRequest:
        return MaintenanceRequest(
            r["request_id"], r["tenant_id"], r["apartment_id"], r["description"],
            r["priority"], r["status"], r["assigned_to"],
            r["submitted_date"], r["scheduled_date"], r["resolved_date"],
            r["resolution_notes"], r["time_taken_hrs"], r["cost"] or 0.0
        )


# ──────────────────────────────────────────────
# Notification Service
# ──────────────────────────────────────────────
class NotificationService:
    def send(self, recipient_id, message, type_="info", tenant_id=None):
        conn = get_connection()
        conn.execute(
            "INSERT INTO notifications (recipient_id, message, type, tenant_id) VALUES (?,?,?,?)",
            (recipient_id, message, type_, tenant_id)
        )
        conn.commit()
        conn.close()

    def get_unread(self, recipient_id: int) -> List[Notification]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM notifications WHERE recipient_id=? AND is_read=0 ORDER BY sent_at DESC",
            (recipient_id,)
        ).fetchall()
        conn.close()
        return [Notification(r["notif_id"], r["recipient_id"], r["message"],
                             r["type"], bool(r["is_read"]), r["sent_at"], r["tenant_id"]) for r in rows]

    def mark_read(self, notif_id: int):
        conn = get_connection()
        conn.execute("UPDATE notifications SET is_read=1 WHERE notif_id=?", (notif_id,))
        conn.commit()
        conn.close()


# ──────────────────────────────────────────────
# Complaint Service
# ──────────────────────────────────────────────
class ComplaintService:
    def get_all(self, status: Optional[str] = None) -> List[dict]:
        conn = get_connection()
        if status:
            rows = conn.execute("""
                SELECT c.*, t.name as tenant_name FROM complaints c
                JOIN tenants t ON c.tenant_id = t.tenant_id
                WHERE c.status=? ORDER BY c.date_logged DESC
            """, (status,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.*, t.name as tenant_name FROM complaints c
                JOIN tenants t ON c.tenant_id = t.tenant_id
                ORDER BY c.date_logged DESC
            """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create(self, tenant_id: int, description: str, logged_by: int) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO complaints (tenant_id, description, logged_by) VALUES (?,?,?)",
            (tenant_id, description, logged_by)
        )
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return cid

    def resolve(self, complaint_id: int, resolution: str):
        conn = get_connection()
        conn.execute(
            "UPDATE complaints SET status='resolved', resolution=? WHERE complaint_id=?",
            (resolution, complaint_id)
        )
        conn.commit()
        conn.close()


# ──────────────────────────────────────────────
# City Service  (manager — expand to new cities)
# ──────────────────────────────────────────────
class CityService:
    """Manages city/office locations Paragon operates in."""

    def get_all(self) -> List[dict]:
        conn = get_connection()
        # Derive cities from the offices table; fall back to distinct apartment locations
        try:
            rows = conn.execute("SELECT * FROM offices ORDER BY city").fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            # offices table might not exist yet — fall back to distinct apt locations
            rows = conn.execute(
                "SELECT DISTINCT location as city FROM apartments ORDER BY location"
            ).fetchall()
            conn.close()
            return [{"city": r["city"], "address": "", "manager": ""} for r in rows]

    def add_city(self, city: str, address: str, manager: str) -> tuple:
        conn = get_connection()
        # Ensure offices table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offices (
                office_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                city       TEXT NOT NULL UNIQUE,
                address    TEXT,
                manager    TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        # Check duplicate
        exists = conn.execute("SELECT 1 FROM offices WHERE city=?", (city,)).fetchone()
        if exists:
            conn.close()
            return False, f"City '{city}' is already registered."
        conn.execute(
            "INSERT INTO offices (city, address, manager) VALUES (?,?,?)",
            (city, address, manager)
        )
        conn.commit()
        conn.close()
        return True, None


# ──────────────────────────────────────────────
# Reporting Service
# ──────────────────────────────────────────────
class ReportService:
    def occupancy_report(self, location: Optional[str] = None) -> dict:
        conn = get_connection()
        q = "SELECT location, COUNT(*) as total, SUM(is_occupied) as occupied FROM apartments"
        params = ()
        if location:
            q += " WHERE location=?"
            params = (location,)
        q += " GROUP BY location"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        result = {}
        for r in rows:
            total = r["total"]
            occ = r["occupied"]
            result[r["location"]] = {
                "total": total,
                "occupied": occ,
                "available": total - occ,
                "rate": round((occ / total * 100) if total else 0, 1)
            }
        return result

    def maintenance_cost_report(self, location: Optional[str] = None) -> List[dict]:
        conn = get_connection()
        q = """
            SELECT mr.priority, mr.status, mr.cost, mr.time_taken_hrs, a.location
            FROM maintenance_requests mr
            JOIN apartments a ON mr.apartment_id = a.apartment_id
        """
        params = ()
        if location:
            q += " WHERE a.location=?"
            params = (location,)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def complaint_log(self) -> List[dict]:
        conn = get_connection()
        rows = conn.execute("""
            SELECT c.*, t.name as tenant_name FROM complaints c
            JOIN tenants t ON c.tenant_id = t.tenant_id
            ORDER BY c.date_logged DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
