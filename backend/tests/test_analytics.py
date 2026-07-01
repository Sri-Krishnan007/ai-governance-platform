import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAnalyticsDashboard(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Login employee
        emp_res = self.client.post("/login", data={"username": "employee", "password": "employeepassword"})
        self.emp_headers = {"Authorization": f"Bearer {emp_res.json()['access_token']}"}

    def test_analytics_endpoint(self):
        res = self.client.get("/analytics", headers=self.emp_headers)
        if res.status_code != 200:
            print("Server response:", res.text)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        # Verify KPIs are returned
        self.assertIn("kpis", data)
        kpis = data["kpis"]
        self.assertIn("total_requests", kpis)
        self.assertIn("average_risk", kpis)
        self.assertIn("review_time_hours", kpis)
        self.assertIn("auto_approval_rate", kpis)
        self.assertIn("escalation_rate", kpis)
        
        # Verify Charts are returned
        self.assertIn("risk_distribution", data)
        self.assertIn("policy_violations", data)
        self.assertIn("approval_trends", data)
        self.assertIn("department_risk", data)
        self.assertIn("monthly_statistics", data)
        self.assertIn("reviewer_performance", data)
        self.assertIn("llm_confidence_trend", data)
        
        # Verify formats
        self.assertIsInstance(data["risk_distribution"], dict)
        self.assertIsInstance(data["policy_violations"], dict)
        self.assertIsInstance(data["approval_trends"], list)
        self.assertIsInstance(data["department_risk"], list)
        self.assertIsInstance(data["monthly_statistics"], list)
        self.assertIsInstance(data["reviewer_performance"], list)
        self.assertIsInstance(data["llm_confidence_trend"], list)

if __name__ == "__main__":
    unittest.main()
