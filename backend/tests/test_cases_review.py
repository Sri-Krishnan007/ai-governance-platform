import unittest
import time
from fastapi.testclient import TestClient
from app.main import app

class TestCasesReview(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Login employee
        emp_res = self.client.post("/login", data={"username": "employee", "password": "employeepassword"})
        self.emp_headers = {"Authorization": f"Bearer {emp_res.json()['access_token']}"}
        
        # Login reviewer
        rev_res = self.client.post("/login", data={"username": "reviewer", "password": "reviewerpassword"})
        self.rev_headers = {"Authorization": f"Bearer {rev_res.json()['access_token']}"}

    def test_case_list_and_role_access(self):
        # 1. Fetch cases as Employee
        emp_cases = self.client.get("/cases", headers=self.emp_headers)
        self.assertEqual(emp_cases.status_code, 200)

        # 2. Fetch cases as Reviewer
        rev_cases = self.client.get("/cases", headers=self.rev_headers)
        self.assertEqual(rev_cases.status_code, 200)

    def test_reviewer_direct_decisions(self):
        unique_ts = int(time.time())
        
        # Submit high-risk action to generate case
        payload = {
            "domain": "Healthcare",
            "natural_language_request": "Delete 1500000 patients details"
        }
        res_del = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        action_id = res_del.json()["id"]
        
        # Answer clarification
        res_qs = self.client.get(f"/actions/{action_id}/clarifications", headers=self.emp_headers)
        qs = res_qs.json()
        if qs:
            for q in qs:
                self.client.post(
                    f"/actions/questions/{q['id']}/answer",
                    json={"answer_text": "Hospital audit database clean"},
                    headers=self.emp_headers
                )
        
        # Get case ID
        res_act = self.client.get(f"/actions/{action_id}", headers=self.emp_headers)
        case = res_act.json().get("governance_case")
        self.assertIsNotNone(case, "Expected human review case to be generated!")
        case_id = case["id"]
        
        # 3. Employee attempts direct approval review (Expected: 403 Forbidden)
        res_emp_app = self.client.post(f"/cases/{case_id}/approve", json={}, headers=self.emp_headers)
        self.assertEqual(res_emp_app.status_code, 403)
        
        # 4. Reviewer direct approval review (Expected: 200 OK)
        res_rev_app = self.client.post(f"/cases/{case_id}/approve", json={"comments": "Unittest approved"}, headers=self.rev_headers)
        self.assertEqual(res_rev_app.status_code, 200)
        self.assertEqual(res_rev_app.json()["status"], "APPROVED")

if __name__ == "__main__":
    unittest.main()
