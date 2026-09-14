# tests/test_pams.py
# Student: Ahmed Saad - 24062019
# Automated unit tests for PAMS — Element 3

import sys, os, unittest, tempfile, shutil
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database.db as db_module
_TEMP_DIR = tempfile.mkdtemp()
db_module.DB_PATH = os.path.join(_TEMP_DIR, "test_pams.db")

from database.db import init_db, get_connection, hash_password
from core.models.models import (
    User, Tenant, Apartment, LeaseAgreement,
    Invoice, Payment, MaintenanceRequest
)
from core.services.services import (
    AuthService, UserService, TenantService,
    ApartmentService, LeaseService, FinanceService,
    MaintenanceService, NotificationService, ReportService
)

def setUpModule():
    init_db()

def tearDownModule():
    shutil.rmtree(_TEMP_DIR, ignore_errors=True)

# ─── Model tests ───────────────────────────────────────────────────────
class TestTenantModel(unittest.TestCase):
    def test_valid_tenant_no_errors(self):
        t = Tenant(1, "AB123456C", "John Smith", "07700900001", "john@email.com")
        self.assertEqual(t.validate(), [])
    def test_invalid_ni_too_short(self):
        t = Tenant(0, "AB1", "Jane", "07700900002", "jane@email.com")
        self.assertTrue(any("NI" in e for e in t.validate()))
    def test_missing_name(self):
        t = Tenant(0, "AB123456C", "", "07700900003", "x@x.com")
        self.assertTrue(any("Name" in e for e in t.validate()))
    def test_invalid_email(self):
        t = Tenant(0, "AB123456C", "Bob", "07700900004", "notanemail")
        self.assertTrue(any("email" in e.lower() for e in t.validate()))
    def test_missing_phone(self):
        t = Tenant(0, "AB123456C", "Bob", "", "bob@email.com")
        self.assertTrue(any("Phone" in e for e in t.validate()))

class TestLeaseModel(unittest.TestCase):
    def _lease(self, days=30, status="active"):
        end = (date.today() + timedelta(days=days)).isoformat()
        return LeaseAgreement(1,1,1,"2024-01-01",end,1000.0,2000.0,status)
    def test_is_active(self):
        self.assertTrue(self._lease().is_active())
    def test_terminated_not_active(self):
        self.assertFalse(self._lease(status="terminated").is_active())
    def test_days_remaining(self):
        self.assertAlmostEqual(self._lease(days=15).days_remaining(), 15, delta=1)
    def test_penalty_is_5_percent(self):
        self.assertAlmostEqual(self._lease().early_exit_penalty(), 50.0)

class TestInvoiceModel(unittest.TestCase):
    def test_paid_not_overdue(self):
        inv = Invoice(1,1,1,1000.0,"2020-01-01","2019-12-01","paid")
        self.assertFalse(inv.is_overdue())
    def test_unpaid_past_due_is_overdue(self):
        inv = Invoice(1,1,1,1000.0,"2020-01-01","2019-12-01","unpaid")
        self.assertTrue(inv.is_overdue())
    def test_future_due_not_overdue(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        inv = Invoice(1,1,1,1000.0,future,date.today().isoformat(),"unpaid")
        self.assertFalse(inv.is_overdue())
    def test_receipt_contains_amount(self):
        inv = Invoice(5,2,1,850.0,"2025-04-30","2025-04-01","paid")
        self.assertIn("850", inv.generate_receipt())
    def test_mark_paid(self):
        inv = Invoice(1,1,1,500.0,"2025-01-01","2024-12-01","unpaid")
        inv.mark_paid()
        self.assertEqual(inv.status, "paid")

class TestApartmentModel(unittest.TestCase):
    def test_available(self):
        apt = Apartment(1,"A101","Bristol","2-bed",2,1,1200.0,False)
        self.assertEqual(apt.get_occupancy_status(), "Available")
    def test_occupied(self):
        apt = Apartment(1,"A101","Bristol","2-bed",2,1,1200.0,True)
        self.assertEqual(apt.get_occupancy_status(), "Occupied")

class TestMaintenanceModel(unittest.TestCase):
    def test_open_not_resolved(self):
        self.assertFalse(MaintenanceRequest(1,1,1,"desc","medium","open").is_resolved())
    def test_resolved(self):
        self.assertTrue(MaintenanceRequest(1,1,1,"desc","medium","resolved").is_resolved())

# ─── Service tests ─────────────────────────────────────────────────────
class TestAuthService(unittest.TestCase):
    def setUp(self): self.s = AuthService()
    def test_valid_login(self):
        u = self.s.login("admin1@pams.com","admin123")
        self.assertIsNotNone(u); self.assertEqual(u.role,"admin")
    def test_wrong_password(self):
        self.assertIsNone(self.s.login("admin1@pams.com","wrong"))
    def test_unknown_email(self):
        self.assertIsNone(self.s.login("nobody@pams.com","x"))
    def test_role_correct(self):
        self.assertEqual(self.s.login("frontdesk1@pams.com","desk123").role,"front_desk")
    def test_location_correct(self):
        self.assertEqual(self.s.login("admin1@pams.com","admin123").location,"Bristol")

class TestTenantService(unittest.TestCase):
    def setUp(self): self.s = TenantService()
    def test_get_all(self):
        self.assertGreater(len(self.s.get_all()), 0)
    def test_create_and_get(self):
        tid,err = self.s.create("ZZ999999Z","Test Person","07000000001","test@test.com","Tester","Ref",1)
        self.assertIsNone(err); t = self.s.get_by_id(tid)
        self.assertEqual(t.name,"Test Person")
    def test_duplicate_ni_error(self):
        self.s.create("XX111111X","P1","07000000002","p1@test.com","J","R",1)
        _,err = self.s.create("XX111111X","P2","07000000003","p2@test.com","J","R",1)
        self.assertIsNotNone(err)
    def test_update(self):
        tid,_ = self.s.create("YY222222Y","Old","07000000010","old@test.com","J","R",1)
        self.s.update(tid,"New Name","07000000011","new@test.com","J2","R2")
        self.assertEqual(self.s.get_by_id(tid).name,"New Name")
    def test_search(self):
        results = self.s.search("Ahmed Hassan")
        self.assertTrue(any(t.name=="Ahmed Hassan" for t in results))
    def test_delete(self):
        tid,_ = self.s.create("WW333333W","Del","07000000099","del@test.com","X","X",1)
        self.s.delete(tid)
        self.assertIsNone(self.s.get_by_id(tid))

class TestApartmentService(unittest.TestCase):
    def setUp(self): self.s = ApartmentService()
    def test_get_all(self): self.assertGreater(len(self.s.get_all()),0)
    def test_create(self):
        aid = self.s.create("Z999","Manchester","studio",0,1,750.0)
        self.assertIn(aid,[a.apartment_id for a in self.s.get_all("Manchester")])
    def test_available_not_occupied(self):
        for a in self.s.get_available(): self.assertFalse(a.is_occupied)
    def test_assign_and_vacate(self):
        aid = self.s.create("TEMP01","Bristol","1-bed",1,3,900.0)
        self.s.assign_tenant(aid,1)
        t = next(a for a in self.s.get_all("Bristol") if a.apartment_id==aid)
        self.assertTrue(t.is_occupied)
        self.s.vacate(aid)
        t2 = next(a for a in self.s.get_all("Bristol") if a.apartment_id==aid)
        self.assertFalse(t2.is_occupied)

class TestFinanceService(unittest.TestCase):
    def setUp(self): self.s = FinanceService()
    def test_generate_invoice(self):
        iid = self.s.generate_invoice(1,1,950.0,"2025-05-01",1)
        self.assertTrue(any(i.invoice_id==iid for i in self.s.get_invoices(1)))
    def test_record_payment(self):
        iid = self.s.generate_invoice(2,2,1200.0,"2025-05-01",1)
        self.s.record_payment(iid,1200.0,"bank_transfer",1)
        paid = next(i for i in self.s.get_invoices(2) if i.invoice_id==iid)
        self.assertEqual(paid.status,"paid")
    def test_summary_keys(self):
        s = self.s.financial_summary()
        for k in ("collected","pending","total_invoices"): self.assertIn(k,s)
    def test_mark_overdue(self):
        iid = self.s.generate_invoice(3,3,500.0,"2020-01-01",1)
        self.s.mark_overdue()
        inv = next((i for i in self.s.get_invoices(3) if i.invoice_id==iid),None)
        if inv: self.assertEqual(inv.status,"overdue")

class TestMaintenanceService(unittest.TestCase):
    def setUp(self): self.s = MaintenanceService()
    def test_create(self):
        rid = self.s.create(1,1,"Broken light","low",2)
        self.assertTrue(any(r.request_id==rid for r in self.s.get_all()))
    def test_resolve(self):
        rid = self.s.create(1,1,"Dripping tap","medium",2)
        self.s.resolve(rid,"Fixed",1.5,45.0)
        r = next(r for r in self.s.get_all() if r.request_id==rid)
        self.assertEqual(r.status,"resolved"); self.assertEqual(r.cost,45.0)
    def test_cost_summary_keys(self):
        s = self.s.get_cost_summary()
        for k in ("total_cost","total_requests","avg_time_hrs"): self.assertIn(k,s)

class TestReportService(unittest.TestCase):
    def setUp(self): self.s = ReportService()
    def test_occupancy_structure(self):
        for _,d in self.s.occupancy_report().items():
            for k in ("total","occupied","available","rate"): self.assertIn(k,d)
    def test_maint_cost_list(self):
        self.assertIsInstance(self.s.maintenance_cost_report(),list)
    def test_complaint_log_list(self):
        self.assertIsInstance(self.s.complaint_log(),list)

class TestNotificationService(unittest.TestCase):
    def setUp(self): self.s = NotificationService()
    def test_send_and_retrieve(self):
        self.s.send(1,"Test notif","info")
        self.assertTrue(any(n.message=="Test notif" for n in self.s.get_unread(1)))
    def test_mark_read(self):
        self.s.send(1,"Mark me","info")
        n = next(n for n in self.s.get_unread(1) if n.message=="Mark me")
        self.s.mark_read(n.notif_id)
        self.assertFalse(any(x.notif_id==n.notif_id for x in self.s.get_unread(1)))

class TestSecurity(unittest.TestCase):
    def test_password_not_plaintext(self):
        conn=get_connection()
        row=conn.execute("SELECT password_hash FROM users WHERE email='admin1@pams.com'").fetchone()
        conn.close()
        self.assertNotEqual(row["password_hash"],"admin123")
        self.assertEqual(len(row["password_hash"]),64)
    def test_hash_deterministic(self):
        self.assertEqual(hash_password("secret"),hash_password("secret"))
    def test_different_hashes(self):
        self.assertNotEqual(hash_password("a"),hash_password("b"))

class TestUserService(unittest.TestCase):
    def setUp(self): self.s = UserService()
    def test_get_all(self): self.assertGreater(len(self.s.get_all()),0)
    def test_create(self):
        uid = self.s.create("New Staff","newstaff@pams.com","pass123","front_desk","Bristol")
        self.assertTrue(any(u.user_id==uid for u in self.s.get_all()))
    def test_deactivate(self):
        uid = self.s.create("Temp","temp@pams.com","pass123","finance","Bristol")
        self.s.deactivate(uid)
        conn=get_connection()
        row=conn.execute("SELECT is_active FROM users WHERE user_id=?",(uid,)).fetchone()
        conn.close()
        self.assertEqual(row["is_active"],0)
    def test_filter_by_location(self):
        for u in self.s.get_all("London"): self.assertEqual(u.location,"London")

if __name__ == "__main__":
    unittest.main(verbosity=2)
