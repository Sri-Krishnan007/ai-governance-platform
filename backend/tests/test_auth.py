import unittest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_password_hash, verify_password, create_access_token, decode_token
from app.database import SessionLocal
from app.models import Role

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        db = SessionLocal()
        employee_role = db.query(Role).filter(Role.name == "Employee").first()
        self.emp_role_id = employee_role.id if employee_role else 1
        db.close()

    def test_password_hashing(self):
        pwd = "myprivatepassword"
        hashed = get_password_hash(pwd)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("wrongpassword", hashed))

    def test_jwt_token_flow(self):
        username = "jwttestuser"
        token = create_access_token(data={"sub": username})
        decoded = decode_token(token)
        self.assertEqual(decoded.get("sub"), username)

    def test_api_auth_endpoints(self):
        unique_ts = int(time.time())
        username = f"auth_user_{unique_ts}"
        email = f"auth_user_{unique_ts}@example.com"
        
        # Test root register
        reg_res = self.client.post("/register", json={
            "username": username,
            "email": email,
            "password": "mypassword123",
            "role_id": self.emp_role_id
        })
        self.assertEqual(reg_res.status_code, 201)
        self.assertEqual(reg_res.json()["username"], username)

        # Test root login
        login_res = self.client.post("/login", data={
            "username": username,
            "password": "mypassword123"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.json())

if __name__ == "__main__":
    unittest.main()
