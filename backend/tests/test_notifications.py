import unittest
import time
from fastapi.testclient import TestClient
from app.main import app

class TestNotificationEngine(unittest.TestCase):
    def setUp(self):
        from app.database import get_db
        from app.database import SessionLocal
        from app.models import Policy
        
        def get_db_override():
            db = SessionLocal()
            original_query = db.query
            def patched_query(*args, **kwargs):
                if args and args[0] == Policy:
                    return original_query(*args, **kwargs).filter(
                        Policy.name.in_([
                            "Finance Limit Safeguard",
                            "Healthcare Patient Deletion Restrictor",
                            "Bulk Deletion Guardrail",
                            "Production Change Safeguard"
                        ])
                    )
                return original_query(*args, **kwargs)
            db.query = patched_query
            try:
                yield db
            finally:
                db.close()
                
        app.dependency_overrides[get_db] = get_db_override

        self.client = TestClient(app)
        # Login employee
        emp_res = self.client.post("/login", data={"username": "employee", "password": "employeepassword"})
        self.emp_headers = {"Authorization": f"Bearer {emp_res.json()['access_token']}"}
        
        # Login reviewer
        rev_res = self.client.post("/login", data={"username": "reviewer", "password": "reviewerpassword"})
        self.rev_headers = {"Authorization": f"Bearer {rev_res.json()['access_token']}"}

        # Login admin
        adm_res = self.client.post("/login", data={"username": "admin", "password": "adminpassword"})
        self.adm_headers = {"Authorization": f"Bearer {adm_res.json()['access_token']}"}

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_confirmation_required_notification(self):
        # Submit action requiring confirmation (Finance transfer > 50,000)
        payload = {
            "domain": "Finance",
            "natural_language_request": "Transfer ₹65,000 to vendor account"
        }
        res = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        self.assertEqual(res.status_code, 201)
        action_id = res.json()["id"]
        
        # Answer any clarifications if present
        res_qs = self.client.get(f"/actions/{action_id}/clarifications", headers=self.emp_headers)
        qs = res_qs.json()
        if qs:
            for q in qs:
                self.client.post(
                    f"/actions/questions/{q['id']}/answer",
                    json={"answer_text": "Vendor payment"},
                    headers=self.emp_headers
                )
                
        # Re-fetch action to check confirmation required
        res_act = self.client.get(f"/actions/{action_id}", headers=self.emp_headers)
        self.assertEqual(res_act.json()["autonomy_level"], "USER_CONFIRMATION")
        
        # Fetch employee's notifications
        res_notes = self.client.get("/notifications?unread_only=true", headers=self.emp_headers)
        self.assertEqual(res_notes.status_code, 200)
        notes = res_notes.json()
        
        # Verify employee received CONFIRMATION_REQUIRED notification
        self.assertTrue(any(n["notification_type"] == "CONFIRMATION_REQUIRED" for n in notes))

    def test_new_case_reviewer_and_resolved_employee_notifications(self):
        # Submit high risk action to generate case (Delete in Prod)
        payload = {
            "domain": "Healthcare",
            "natural_language_request": "Delete 1500 patient records in Production"
        }
        res_del = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        self.assertEqual(res_del.status_code, 201)
        action_id = res_del.json()["id"]
        
        # Answer clarification
        res_qs = self.client.get(f"/actions/{action_id}/clarifications", headers=self.emp_headers)
        qs = res_qs.json()
        if qs:
            for q in qs:
                self.client.post(
                    f"/actions/questions/{q['id']}/answer",
                    json={"answer_text": "Old archive clean"},
                    headers=self.emp_headers
                )
                
        # Re-fetch action to get case ID
        res_act = self.client.get(f"/actions/{action_id}", headers=self.emp_headers)
        action_data = res_act.json()
        case = action_data.get("governance_case")
        self.assertIsNotNone(case, "Expected case to be generated")
        case_id = case["id"]
        
        # Fetch reviewer's notifications
        res_rev_notes = self.client.get("/notifications?unread_only=true", headers=self.rev_headers)
        self.assertEqual(res_rev_notes.status_code, 200)
        rev_notes = res_rev_notes.json()
        
        # Verify reviewer received NEW_CASE or ESCALATED_CASE notification
        self.assertTrue(any(n["notification_type"] in ["NEW_CASE", "ESCALATED_CASE"] for n in rev_notes))
        
        # Reviewer approves the case
        res_app = self.client.post(
            f"/cases/{case_id}/approve",
            json={"comments": "Approved via unit test"},
            headers=self.rev_headers
        )
        self.assertEqual(res_app.status_code, 200)
        
        # Fetch employee's notifications
        res_emp_notes = self.client.get("/notifications?unread_only=true", headers=self.emp_headers)
        emp_notes = res_emp_notes.json()
        
        # Verify employee received CASE_APPROVED notification
        self.assertTrue(any(n["notification_type"] == "CASE_APPROVED" for n in emp_notes))

    def test_mark_as_read_endpoints(self):
        # Fetch current notifications
        res_notes = self.client.get("/notifications?unread_only=true", headers=self.emp_headers)
        notes = res_notes.json()
        if not notes:
            # Generate one if empty
            payload = {
                "domain": "Finance",
                "natural_language_request": "Transfer ₹65000 to vendor"
            }
            self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
            res_notes = self.client.get("/notifications?unread_only=true", headers=self.emp_headers)
            notes = res_notes.json()
            
        self.assertTrue(len(notes) > 0)
        note_id = notes[0]["id"]
        
        # Mark single notification as read
        res_read = self.client.post(f"/notifications/{note_id}/read", headers=self.emp_headers)
        self.assertEqual(res_read.status_code, 200)
        self.assertEqual(res_read.json()["read"], True)
        
        # Mark all notifications as read
        res_read_all = self.client.post("/notifications/read-all", headers=self.emp_headers)
        self.assertEqual(res_read_all.status_code, 200)
        self.assertIn("All notifications marked as read", res_read_all.json()["detail"])
        
        # Check unread count is 0
        res_notes_after = self.client.get("/notifications?unread_only=true", headers=self.emp_headers)
        self.assertEqual(len(res_notes_after.json()), 0)

if __name__ == "__main__":
    unittest.main()
