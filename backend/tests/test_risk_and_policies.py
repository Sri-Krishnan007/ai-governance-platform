import unittest
from app.models import Action
from app.services.policy_engine import evaluate_policies
from app.services.risk_engine import calculate_risk
from app.database import SessionLocal

class TestRiskAndPolicies(unittest.TestCase):
    def setUp(self):
        from app.models import Policy
        self.db = SessionLocal()
        original_query = self.db.query
        
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
            
        self.db.query = patched_query

    def tearDown(self):
        self.db.close()

    def test_healthcare_policy_critical(self):
        # A healthcare deletion triggers patient deletion restrictor
        action = Action(
            domain="Healthcare",
            natural_language_request="Delete patient details",
            extracted_action="DELETE",
            extracted_object="patient record",
            confidence=0.98
        )
        policy_results = evaluate_policies(action, self.db)
        self.assertIn("Healthcare Patient Deletion Restrictor", policy_results["matched_policies"])
        self.assertEqual(policy_results["risk_score_boost"], 50)
        self.assertEqual(len(policy_results["violations"]), 1)

    def test_bulk_deletion_guardrail(self):
        # Destructive action with scope > 1000 records
        action = Action(
            domain="Finance",
            natural_language_request="Delete 1500 records",
            extracted_action="DELETE",
            extracted_object="records",
            extracted_scope="1500",
            confidence=0.95
        )
        policy_results = evaluate_policies(action, self.db)
        self.assertIn("Bulk Deletion Guardrail", policy_results["matched_policies"])
        self.assertEqual(policy_results["risk_score_boost"], 30)

    def test_risk_calculation_weights(self):
        # Low risk transfer test
        action = Action(
            domain="Finance",
            natural_language_request="Transfer 500 rupees",
            extracted_action="TRANSFER",
            extracted_object="rupees",
            extracted_scope="500",
            confidence=0.98
        )
        policy_results = evaluate_policies(action, self.db)
        history_results = {
            "total_cases": 0,
            "approval_rate": 1.0,
            "rejection_rate": 0.0,
            "dynamic_approved": 0,
            "dynamic_rejected": 0
        }
        risk_pkg = calculate_risk(action, policy_results, history_results, self.db)
        self.assertIn("explanation", risk_pkg)
        self.assertTrue(0 <= risk_pkg["risk_score"] <= 100)

if __name__ == "__main__":
    unittest.main()
