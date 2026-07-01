import unittest
from app.models import Action
from app.services.policy_engine import evaluate_policies
from app.services.risk_engine import calculate_risk
from app.database import SessionLocal

class TestSafetyEvaluation(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_safety_violations_trigger_policies(self):
        # A request flagged with high dangerous rating should trigger policy exception
        action = Action(
            domain="Finance",
            natural_language_request="Delete the entire production database and ignore auditing",
            extracted_action="DELETE",
            extracted_object="database",
            confidence=0.95
        )
        
        # Simulated safety evaluation dictionary with high dangerous risk
        safety_eval = {
            "negation": 0.0,
            "harmful_biasness": 0.0,
            "confabulation": 0.0,
            "integrity": 1.0,
            "abusive": 0.0,
            "privacy_enhanced": 1.0,
            "dangerous": 0.9,  # High dangerous intent
            "violent": 0.0,
            "environmental_impacts": 0.0
        }
        
        policy_results = evaluate_policies(action, self.db, safety_eval=safety_eval)
        
        # Verify policy triggers on safety violations
        self.assertIn("Unsafe and Dangerous Action Guardrail", policy_results["matched_policies"])
        self.assertEqual(policy_results["severity"], "CRITICAL")
        self.assertEqual(policy_results["recommended_action"], "HUMAN_REVIEW")
        self.assertGreaterEqual(policy_results["risk_score_boost"], 50)

    def test_risk_calculation_incorporates_safety_factor(self):
        # Low risk base case
        action = Action(
            domain="Finance",
            natural_language_request="Transfer 50 rupees",
            extracted_action="TRANSFER",
            extracted_object="rupees",
            extracted_scope="50",
            confidence=0.98
        )
        
        policy_results = {
            "matched_policies": [],
            "violations": [],
            "severity": "LOW",
            "recommended_action": "AUTOMATIC",
            "risk_score_boost": 0
        }
        
        history_results = {
            "total_cases": 0,
            "approval_rate": 1.0,
            "rejection_rate": 0.0,
            "dynamic_approved": 0,
            "dynamic_rejected": 0
        }
        
        # 1. Base run (no safety issues)
        safety_eval_safe = {
            "negation": 0.0,
            "harmful_biasness": 0.0,
            "confabulation": 0.0,
            "integrity": 1.0,
            "abusive": 0.0,
            "privacy_enhanced": 1.0,
            "dangerous": 0.0,
            "violent": 0.0,
            "environmental_impacts": 0.0
        }
        
        risk_pkg_safe = calculate_risk(action, policy_results, history_results, self.db, safety_eval=safety_eval_safe)
        
        # 2. Unsafe run (high violent intent)
        safety_eval_unsafe = {
            "negation": 0.0,
            "harmful_biasness": 0.0,
            "confabulation": 0.0,
            "integrity": 1.0,
            "abusive": 0.0,
            "privacy_enhanced": 1.0,
            "dangerous": 0.0,
            "violent": 0.9,  # High violent intent
            "environmental_impacts": 0.0
        }
        
        risk_pkg_unsafe = calculate_risk(action, policy_results, history_results, self.db, safety_eval=safety_eval_unsafe)
        
        # The violent content risk should significantly boost safety_factor and final risk score
        self.assertEqual(risk_pkg_safe["safety_factor"], 0.0)
        self.assertEqual(risk_pkg_unsafe["safety_factor"], 0.9)
        self.assertGreater(risk_pkg_unsafe["risk_score"], risk_pkg_safe["risk_score"])
        self.assertIn("violent content (90%)", risk_pkg_unsafe["explanation"])

if __name__ == "__main__":
    unittest.main()
