-- PAMS Database Schema
-- SQLite

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────
-- Users / Roles
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('front_desk','finance','maintenance','admin','manager')),
    location      TEXT NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────
-- Tenants
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    ni_number   TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    occupation  TEXT,
    references_ TEXT,
    created_by  INTEGER REFERENCES users(user_id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────
-- Apartments
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS apartments (
    apartment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_number   TEXT NOT NULL,
    location      TEXT NOT NULL,
    type          TEXT NOT NULL,
    num_rooms     INTEGER NOT NULL,
    floor         INTEGER NOT NULL DEFAULT 1,
    monthly_rent  REAL NOT NULL,
    is_occupied   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────
-- Lease Agreements
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leases (
    lease_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     INTEGER NOT NULL REFERENCES tenants(tenant_id),
    apartment_id  INTEGER NOT NULL REFERENCES apartments(apartment_id),
    start_date    TEXT NOT NULL,
    end_date      TEXT NOT NULL,
    monthly_rent  REAL NOT NULL,
    deposit       REAL NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','terminated','expired')),
    early_exit    INTEGER NOT NULL DEFAULT 0,
    penalty_paid  REAL NOT NULL DEFAULT 0.0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────
-- Invoices
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id    INTEGER NOT NULL REFERENCES tenants(tenant_id),
    lease_id     INTEGER NOT NULL REFERENCES leases(lease_id),
    amount_due   REAL NOT NULL,
    due_date     TEXT NOT NULL,
    issued_date  TEXT NOT NULL DEFAULT (date('now')),
    status       TEXT NOT NULL DEFAULT 'unpaid' CHECK(status IN ('unpaid','paid','overdue')),
    created_by   INTEGER REFERENCES users(user_id)
);

-- ─────────────────────────────────────────
-- Payments
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    payment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id    INTEGER NOT NULL REFERENCES invoices(invoice_id),
    amount_paid   REAL NOT NULL,
    payment_date  TEXT NOT NULL DEFAULT (date('now')),
    method        TEXT NOT NULL DEFAULT 'bank_transfer',
    recorded_by   INTEGER REFERENCES users(user_id)
);

-- ─────────────────────────────────────────
-- Maintenance Requests
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS maintenance_requests (
    request_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id        INTEGER NOT NULL REFERENCES tenants(tenant_id),
    apartment_id     INTEGER NOT NULL REFERENCES apartments(apartment_id),
    description      TEXT NOT NULL,
    priority         TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high','urgent')),
    status           TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','assigned','in_progress','resolved','closed')),
    assigned_to      INTEGER REFERENCES users(user_id),
    submitted_date   TEXT NOT NULL DEFAULT (datetime('now')),
    scheduled_date   TEXT,
    resolved_date    TEXT,
    resolution_notes TEXT,
    time_taken_hrs   REAL,
    cost             REAL DEFAULT 0.0,
    logged_by        INTEGER REFERENCES users(user_id)
);

-- ─────────────────────────────────────────
-- Complaints
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     INTEGER NOT NULL REFERENCES tenants(tenant_id),
    description   TEXT NOT NULL,
    date_logged   TEXT NOT NULL DEFAULT (date('now')),
    status        TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','resolved')),
    resolution    TEXT,
    logged_by     INTEGER REFERENCES users(user_id)
);

-- ─────────────────────────────────────────
-- Notifications
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    notif_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id  INTEGER NOT NULL REFERENCES users(user_id),
    tenant_id     INTEGER REFERENCES tenants(tenant_id),
    message       TEXT NOT NULL,
    type          TEXT NOT NULL DEFAULT 'info',
    is_read       INTEGER NOT NULL DEFAULT 0,
    sent_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
