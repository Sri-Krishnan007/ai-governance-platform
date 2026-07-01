import unittest
import io
from fastapi.testclient import TestClient
from app.main import app

class TestPolicyTextManagement(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Login admin
        adm_res = self.client.post("/login", data={"username": "admin", "password": "adminpassword"})
        self.adm_headers = {"Authorization": f"Bearer {adm_res.json()['access_token']}"}

    def test_policy_crud_operations(self):
        # Create a policy manually
        payload = {
            "name": "Manual Test Policy",
            "domain": "Finance",
            "description": "Checks transfer limit rules",
            "action_type": "TRANSFER",
            "severity": "CRITICAL",
            "rule_definition": {
                "category": "Compliance",
                "condition_type": "threshold",
                "operator": ">",
                "threshold_value": 75000,
                "regulation": "Internal"
            },
            "is_active": True
        }
        res_post = self.client.post("/policies", json=payload, headers=self.adm_headers)
        self.assertEqual(res_post.status_code, 201)
        policy_id = res_post.json()["id"]
        self.assertEqual(res_post.json()["name"], "Manual Test Policy")
        
        # Get policies list
        res_get = self.client.get("/policies", headers=self.adm_headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertTrue(any(p["id"] == policy_id for p in res_get.json()))
        
        # Modify policy
        payload["name"] = "Modified Manual Policy"
        res_put = self.client.put(f"/policies/{policy_id}", json=payload, headers=self.adm_headers)
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.json()["name"], "Modified Manual Policy")
        
        # Delete policy
        res_del = self.client.delete(f"/policies/{policy_id}", headers=self.adm_headers)
        self.assertEqual(res_del.status_code, 204)
        
        # Verify deleted
        res_get2 = self.client.get("/policies", headers=self.adm_headers)
        self.assertFalse(any(p["id"] == policy_id for p in res_get2.json()))

    def test_structured_file_upload(self):
        # Structured file mock data
        file_content = (
            "Name: Test Upload Policy\n"
            "Domain: Healthcare\n"
            "Action Type: DELETE\n"
            "Severity: CRITICAL\n"
            "Description: Strict HIPAA deletion safeguards.\n"
            "Condition: records > 500\n"
        )
        
        file_obj = io.BytesIO(file_content.encode("utf-8"))
        res_upload = self.client.post(
            "/policies/upload",
            files={"file": ("healthcare_compliance.txt", file_obj, "text/plain")},
            headers=self.adm_headers
        )
        
        self.assertEqual(res_upload.status_code, 200)
        new_policies = res_upload.json()
        self.assertEqual(len(new_policies), 1)
        policy = new_policies[0]
        self.assertEqual(policy["name"], "Test Upload Policy")
        self.assertEqual(policy["domain"], "Healthcare")
        self.assertEqual(policy["action_type"], "DELETE")
        self.assertEqual(policy["severity"], "CRITICAL")
        self.assertEqual(policy["rule_definition"]["condition_type"], "bulk_threshold")
        self.assertEqual(policy["rule_definition"]["threshold_value"], 500)
        
        # Cleanup
        self.client.delete(f"/policies/{policy['id']}", headers=self.adm_headers)

    def test_unstructured_file_upload_fallback(self):
        # Unstructured file content (plain paragraph)
        file_content = (
            "Ensure that any system reset action on HR machinery does not trigger critical limits.\n"
            "This rule applies strictly when updating the primary database servers in production.\n"
        )
        
        file_obj = io.BytesIO(file_content.encode("utf-8"))
        res_upload = self.client.post(
            "/policies/upload",
            files={"file": ("hr_system_rules.txt", file_obj, "text/plain")},
            headers=self.adm_headers
        )
        
        self.assertEqual(res_upload.status_code, 200)
        new_policies = res_upload.json()
        self.assertEqual(len(new_policies), 1)
        policy = new_policies[0]
        self.assertIn("Ensure that any system reset", policy["name"])
        self.assertEqual(policy["domain"], "HR") # Inferred from filename "hr_system_rules.txt"
        self.assertEqual(policy["rule_definition"]["condition_type"], "production_check")
        
        # Cleanup
        self.client.delete(f"/policies/{policy['id']}", headers=self.adm_headers)

if __name__ == "__main__":
    unittest.main()
