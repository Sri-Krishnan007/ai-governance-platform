import unittest
import time
from fastapi.testclient import TestClient
from app.main import app

class TestExplainabilityEngine(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Login employee
        emp_res = self.client.post("/login", data={"username": "employee", "password": "employeepassword"})
        self.emp_headers = {"Authorization": f"Bearer {emp_res.json()['access_token']}"}
        
        # Login reviewer
        rev_res = self.client.post("/login", data={"username": "reviewer", "password": "reviewerpassword"})
        self.rev_headers = {"Authorization": f"Bearer {rev_res.json()['access_token']}"}

    def test_get_explanation_success_and_access(self):
        # 1. Submit high-risk action to generate case
        payload = {
            "domain": "Healthcare",
            "natural_language_request": "Delete 2500 patient records in Production"
        }
        res_del = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        self.assertEqual(res_del.status_code, 201)
        action_id = res_del.json()["id"]
        
        # Resolve any clarification questions to get to evaluation
        res_qs = self.client.get(f"/actions/{action_id}/clarifications", headers=self.emp_headers)
        self.assertEqual(res_qs.status_code, 200)
        qs = res_qs.json()
        if qs:
            for q in qs:
                self.client.post(
                    f"/actions/questions/{q['id']}/answer",
                    json={"answer_text": "Compliance audit cleanup request"},
                    headers=self.emp_headers
                )
                
        # Re-fetch action to get case ID
        res_act = self.client.get(f"/actions/{action_id}", headers=self.emp_headers)
        action_data = res_act.json()
        case = action_data.get("governance_case")
        self.assertIsNotNone(case, "Expected human review case to be generated!")
        case_id = case["id"]
        
        # 2. Get explanation as Employee (should succeed because employee submitted the action)
        res_exp_emp = self.client.get(f"/cases/{case_id}/explanation", headers=self.emp_headers)
        self.assertEqual(res_exp_emp.status_code, 200)
        exp_data = res_exp_emp.json()
        
        self.assertEqual(exp_data["case_id"], case_id)
        self.assertIn("Delete 2500 patient records in Production", exp_data["action_text"])
        self.assertGreater(len(exp_data["risk_factors"]), 0)
        self.assertEqual(exp_data["final_risk"], action_data["risk_score"])
        self.assertEqual(exp_data["decision"], "Human Governance Review")
        
        # Check that matched policies match the list
        self.assertTrue(any(p["name"] == "Bulk Deletion Guardrail" for p in exp_data["matched_policies"]))
        self.assertTrue(any(p["name"] == "Production Change Safeguard" for p in exp_data["matched_policies"]))
        
        # 3. Get explanation as Reviewer (should succeed)
        res_exp_rev = self.client.get(f"/cases/{case_id}/explanation", headers=self.rev_headers)
        self.assertEqual(res_exp_rev.status_code, 200)
        
        # 4. Another employee trying to view this explanation (should fail with 403 Forbidden)
        # First register/login another employee
        # But we can just use no token or simulate forbidden by using another user if we want
        # Let's try getting explanation without Authorization headers (should return 401)
        res_exp_no_auth = self.client.get(f"/cases/{case_id}/explanation")
        self.assertEqual(res_exp_no_auth.status_code, 401)

if __name__ == "__main__":
    unittest.main()
