import unittest
import time
from fastapi.testclient import TestClient
from app.main import app

class TestAdaptiveLearning(unittest.TestCase):
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

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_approval_risk_offsets(self):
        unique_ts = int(time.time())
        domain_finance = f"CustomFinance_Suite_{unique_ts}"
        
        payload = {
            "domain": domain_finance,
            "natural_language_request": "Transfer 15,000 rupees from account 1001 to account 2002"
        }
        
        # First transfer
        res_1 = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        initial_risk = res_1.json()["risk_score"]
        action_id = res_1.json()["id"]
        
        # Manually set status to APPROVED in database to simulate past approval
        from app.database import SessionLocal
        from app.models import Action
        db_sess = SessionLocal()
        try:
            act = db_sess.query(Action).filter(Action.id == action_id).first()
            act.status = "APPROVED"
            db_sess.commit()
        finally:
            db_sess.close()
        
        # Second duplicate transfer (expecting -5 points decrement)
        res_2 = self.client.post("/actions/evaluate", json=payload, headers=self.emp_headers)
        second_risk = res_2.json()["risk_score"]
        
        self.assertEqual(second_risk, initial_risk - 5)
        self.assertIn("decreased by 5", res_2.json()["risk_breakdown"]["explanation"])

if __name__ == "__main__":
    unittest.main()
