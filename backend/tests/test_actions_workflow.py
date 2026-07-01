import unittest
import time
from fastapi.testclient import TestClient
from app.main import app

class TestActionsWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Login employee
        login_res = self.client.post("/login", data={
            "username": "employee",
            "password": "employeepassword"
        })
        self.emp_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    def test_clarification_and_resolution_flow(self):
        unique_ts = int(time.time())
        domain = f"Workflow_Domain_{unique_ts}"
        
        # 1. Submit action missing required info
        payload = {
            "domain": domain,
            "natural_language_request": "Transfer rupees from account 1001"
        }
        res_submit = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        self.assertEqual(res_submit.status_code, 201)
        data = res_submit.json()
        self.assertEqual(data["status"], "AWAITING_CLARIFICATION")
        action_id = data["id"]
        
        # 2. Get questions
        res_qs = self.client.get(f"/actions/{action_id}/clarifications", headers=self.emp_headers)
        self.assertEqual(res_qs.status_code, 200)
        qs = res_qs.json()
        self.assertTrue(len(qs) > 0)
        
        # 3. Answer ALL questions
        for q in qs:
            res_ans = self.client.post(
                f"/actions/questions/{q['id']}/answer",
                json={"answer_text": f"Routine details for {q['parameter_name']}"},
                headers=self.emp_headers
            )
            self.assertEqual(res_ans.status_code, 201)
        
        # 4. Action details now updated (should not be awaiting clarification anymore)
        res_act = self.client.get(f"/actions/{action_id}", headers=self.emp_headers)
        self.assertEqual(res_act.status_code, 200)
        self.assertNotEqual(res_act.json()["status"], "AWAITING_CLARIFICATION")

if __name__ == "__main__":
    unittest.main()
