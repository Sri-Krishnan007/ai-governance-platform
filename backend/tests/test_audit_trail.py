import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAuditTrail(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Login employee
        emp_res = self.client.post("/login", data={"username": "employee", "password": "employeepassword"})
        self.emp_headers = {"Authorization": f"Bearer {emp_res.json()['access_token']}"}
        
        # Login admin
        admin_res = self.client.post("/login", data={"username": "admin", "password": "adminpassword"})
        self.admin_headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

    def test_audit_security_and_immutability(self):
        # 1. Fetch audit logs as Employee (Expected: 403 Forbidden)
        res_emp = self.client.get("/audit", headers=self.emp_headers)
        self.assertEqual(res_emp.status_code, 403)

        # 2. Fetch audit logs as Admin (Expected: 200 OK)
        res_admin = self.client.get("/audit", headers=self.admin_headers)
        self.assertEqual(res_admin.status_code, 200)

        # 3. Test delete route omission (Expected: 404 or 405)
        res_del = self.client.delete("/audit", headers=self.admin_headers)
        self.assertIn(res_del.status_code, [404, 405])

if __name__ == "__main__":
    unittest.main()
