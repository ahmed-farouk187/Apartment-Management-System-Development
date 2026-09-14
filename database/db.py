# database/db.py
# Student: Ahmed Saad - 24062019
# Database connection manager for PAMS

import sqlite3
import hashlib
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "pams.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables from schema.sql and seed mock data."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    _seed(conn)
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _seed(conn: sqlite3.Connection):
    # Skip seeding if data already exists
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return

    # ── Users ────────────────────────────────────────────────────────────
    users = [
        ("Admin User",         "admin1@pams.com",        hash_password("admin123"),        "admin",       "Bristol"),
        ("Front Desk User",    "frontdesk1@pams.com",    hash_password("desk123"),         "front_desk",  "Bristol"),
        ("Finance User",       "finance1@pams.com",      hash_password("finance123"),      "finance",     "Bristol"),
        ("Maintenance User",   "maintenance1@pams.com",  hash_password("maintenance123"),  "maintenance", "Bristol"),
        ("Manager User",       "manager1@pams.com",      hash_password("manager123"),      "manager",     "Bristol"),
        ("Admin London",       "admin2@pams.com",        hash_password("admin123"),        "admin",       "London"),
        ("Front Desk Cardiff", "frontdesk2@pams.com",    hash_password("desk123"),         "front_desk",  "Cardiff"),
    ]
    conn.executemany(
        "INSERT INTO users (name, email, password_hash, role, location) VALUES (?,?,?,?,?)",
        users
    )

    # ── Apartments ───────────────────────────────────────────────────────
    apartments = [
        ("A101", "Bristol",    "1-bed",  1, 1, 950.0,  0),
        ("A102", "Bristol",    "2-bed",  2, 1, 1200.0, 0),
        ("A201", "Bristol",    "2-bed",  2, 2, 1250.0, 0),
        ("A202", "Bristol",    "3-bed",  3, 2, 1600.0, 0),
        ("A203", "Bristol",    "1-bed",  1, 2, 975.0,  0),
        ("A204", "Bristol",    "2-bed",  2, 3, 1300.0, 0),
        ("B101", "London",     "1-bed",  1, 1, 1800.0, 0),
        ("B201", "London",     "2-bed",  2, 2, 2200.0, 0),
        ("C101", "Cardiff",    "1-bed",  1, 1, 850.0,  0),
        ("C102", "Cardiff",    "2-bed",  2, 1, 1100.0, 0),
        ("D101", "Manchester", "studio", 0, 1, 750.0,  0),
    ]
    conn.executemany(
        "INSERT INTO apartments (unit_number, location, type, num_rooms, floor, monthly_rent, is_occupied) VALUES (?,?,?,?,?,?,?)",
        apartments
    )

    # ── Tenants ──────────────────────────────────────────────────────────
    tenants = [
        ("AB111111A", "Ahmed Hassan",  "07700900101", "ahmed@email.com",  "Software Engineer", "Dr Smith, Prof Jones"),
        ("AB222222B", "Imene Benali",  "07700900102", "imene@email.com",  "Doctor",            "Mr Clark, Mrs Davis"),
        ("AB333333C", "Omar Farooq",   "07700900103", "omar@email.com",   "Accountant",        "Ms Taylor, Mr Brown"),
        ("AB444444D", "Jack Thompson", "07700900104", "jack@email.com",   "Teacher",           "Mrs White, Dr Green"),
        ("AB555555E", "Kevin Murphy",  "07700900105", "kevin@email.com",  "Architect",         "Mr Black, Ms Hall"),
        ("AB666666F", "Sara Williams", "07700900106", "sara@email.com",   "Nurse",             "Dr Lee, Mr Wilson"),
    ]
    conn.executemany(
        "INSERT INTO tenants (ni_number, name, phone, email, occupation, references_, created_by) VALUES (?,?,?,?,?,?,1)",
        tenants
    )

    # ── Leases ───────────────────────────────────────────────────────────
    leases = [
        (1, 1, "2025-06-01", "2026-05-01", 950.0,  1900.0,  "active"),
        (2, 2, "2025-07-01", "2026-05-10", 1200.0, 2400.0,  "active"),
        (3, 3, "2025-08-01", "2026-05-20", 1250.0, 2500.0,  "active"),
        (4, 4, "2025-09-01", "2026-06-01", 1600.0, 3200.0,  "active"),
        (5, 5, "2025-10-01", "2026-07-01", 975.0,  1950.0,  "active"),
        (6, 6, "2025-11-01", "2026-08-01", 1300.0, 2600.0,  "active"),
    ]
    conn.executemany(
        "INSERT INTO leases (tenant_id, apartment_id, start_date, end_date, monthly_rent, deposit, status) VALUES (?,?,?,?,?,?,?)",
        leases
    )
    # Mark those apartments as occupied
    conn.executemany(
        "UPDATE apartments SET is_occupied=1 WHERE apartment_id=?",
        [(1,), (2,), (3,), (4,), (5,), (6,)]
    )

    # ── Invoices ─────────────────────────────────────────────────────────
    invoices = [
        (1, 1, 950.0,  "2025-03-01", "2025-02-01", "overdue"),
        (2, 2, 1200.0, "2025-04-01", "2025-03-01", "paid"),
        (3, 3, 1250.0, "2025-04-30", "2025-04-01", "unpaid"),
        (4, 4, 1600.0, "2025-04-01", "2025-03-01", "paid"),
        (5, 5, 975.0,  "2025-04-30", "2025-04-01", "unpaid"),
        (6, 6, 1300.0, "2025-03-15", "2025-02-15", "overdue"),
    ]
    conn.executemany(
        "INSERT INTO invoices (tenant_id, lease_id, amount_due, due_date, issued_date, status, created_by) VALUES (?,?,?,?,?,?,1)",
        invoices
    )

    # ── Payments ─────────────────────────────────────────────────────────
    payments = [
        (2, 1200.0, "2025-03-28", "bank_transfer"),
        (4, 1600.0, "2025-03-25", "bank_transfer"),
    ]
    conn.executemany(
        "INSERT INTO payments (invoice_id, amount_paid, payment_date, method, recorded_by) VALUES (?,?,?,?,1)",
        payments
    )

    # ── Maintenance Requests ─────────────────────────────────────────────
    maint = [
        (1, 1, "Leaking tap in kitchen",       "medium", "open",     None, "2025-04-01"),
        (2, 2, "Broken window latch",           "high",   "assigned", 4,    "2025-04-05"),
        (3, 3, "Boiler not heating",            "urgent", "resolved", 4,    "2025-03-20"),
        (4, 4, "Bathroom extractor fan faulty", "low",    "open",     None, "2025-04-10"),
        (5, 5, "Front door lock stiff",         "medium", "open",     None, "2025-04-12"),
        (6, 6, "Ceiling damp patch in bedroom", "high",   "assigned", 4,    "2025-04-15"),
    ]
    conn.executemany(
        """INSERT INTO maintenance_requests
           (tenant_id, apartment_id, description, priority, status, assigned_to, submitted_date)
           VALUES (?,?,?,?,?,?,?)""",
        maint
    )
    conn.execute(
        """UPDATE maintenance_requests
           SET resolved_date=?, resolution_notes=?, time_taken_hrs=?, cost=?
           WHERE request_id=3""",
        ("2025-03-22", "Replaced boiler igniter unit. Tested and confirmed working.", 3.5, 180.0)
    )

    # ── Complaints ───────────────────────────────────────────────────────
    complaints = [
        (1, "Noisy neighbours after midnight",  "2025-03-15", "open",     None),
        (2, "Hallway lighting flickering",      "2025-03-20", "resolved", "Bulbs replaced by maintenance team."),
        (3, "Car park barrier not working",     "2025-04-02", "open",     None),
        (4, "Post box lock broken",             "2025-04-08", "open",     None),
    ]
    conn.executemany(
        "INSERT INTO complaints (tenant_id, description, date_logged, status, resolution) VALUES (?,?,?,?,?)",
        complaints
    )

    conn.commit()
    print("[DB] Database seeded successfully.")
