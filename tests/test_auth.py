import unittest
import json
import os
import sys

# Ensure backend directory is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from database.db import get_db, init_db, execute_db

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        # Activate email mock so tests don't hit real SMTP
        os.environ['FLASK_TESTING'] = '1'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        os.environ.pop('FLASK_TESTING', None)

    def _force_verify(self, email):
        """Mark a registered user as email-verified so login tests can proceed."""
        with self.app.app_context():
            execute_db("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))


    def test_01_student_registration(self):
        """Test student registration creates account and profile."""
        import uuid
        email = f"student_{uuid.uuid4().hex[:8]}@university.edu"
        payload = {
            'email': email,
            'password': 'SecurePassword@123',
            'full_name': 'Test Student',
            'role': 'student',
            'phone': '+91 9123456780',
            'education': 'B.Tech IT (3rd Year)',
            'institution': 'State Engineering College',
            'skills': ['Python', 'SQL', 'Flask']
        }
        res = self.client.post('/api/auth/register', json=payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertIn('token', data)
        self.assertIn('verification_token', data)
        self.assertEqual(data['user']['email'], email)
        self.assertEqual(data['user']['role'], 'student')

    def test_02_employer_registration(self):
        """Test employer registration creates employer account and profile."""
        import uuid
        email = f"employer_{uuid.uuid4().hex[:8]}@business.com"
        payload = {
            'email': email,
            'password': 'EmployerPass@123',
            'full_name': 'Business Hiring Lead',
            'role': 'employer',
            'phone': '+91 9876500000',
            'company_name': 'Sunrise Artisanal Bakery',
            'business_type': 'Hospitality & Food'
        }
        res = self.client.post('/api/auth/register', json=payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.get_json()
        self.assertIn('token', data)
        self.assertIn('verification_token', data)
        self.assertEqual(data['user']['role'], 'employer')

    def test_03_registration_validation(self):
        """Test registration rejects missing email, weak password, or bad email format."""
        # Missing required fields
        res1 = self.client.post('/api/auth/register', json={'email': '', 'password': 'pass'})
        self.assertEqual(res1.status_code, 400)

        # Invalid email syntax
        res2 = self.client.post('/api/auth/register', json={
            'email': 'not-an-email',
            'password': 'Password123',
            'full_name': 'Test User',
            'role': 'student'
        })
        self.assertEqual(res2.status_code, 400)

    def test_04_duplicate_email(self):
        """Test that registering an already existing email returns 409 Conflict."""
        import uuid
        email = f"dup_{uuid.uuid4().hex[:8]}@student.edu"
        payload = {
            'email': email,
            'password': 'Password@123',
            'full_name': 'Original User',
            'role': 'student'
        }
        res1 = self.client.post('/api/auth/register', json=payload)
        self.assertIn(res1.status_code, [200, 201])

        # Attempt to register with the exact same email
        res2 = self.client.post('/api/auth/register', json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertIn('already exists', res2.get_json()['error'].lower())

    def test_05_login_success(self):
        """Test login with valid credentials."""
        import uuid
        email = f"login_ok_{uuid.uuid4().hex[:8]}@student.edu"
        # Register user first
        reg_payload = {
            'email': email,
            'password': 'CorrectPassword@123',
            'full_name': 'Login Tester',
            'role': 'student'
        }
        self.client.post('/api/auth/register', json=reg_payload)

        # Force email verification so login is not blocked
        self._force_verify(email)

        # Attempt login
        login_res = self.client.post('/api/auth/login', json={
            'email': email,
            'password': 'CorrectPassword@123'
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], email)

    def test_06_login_wrong_password(self):
        """Test login with wrong password returns 401 Unauthorized."""
        import uuid
        email = f"wrong_pwd_{uuid.uuid4().hex[:8]}@student.edu"
        # Register user first
        reg_payload = {
            'email': email,
            'password': 'TheRealPassword@123',
            'full_name': 'Tester Wrong Pwd',
            'role': 'student'
        }
        self.client.post('/api/auth/register', json=reg_payload)

        # Force email verification so the account is valid (only the password should be wrong)
        self._force_verify(email)

        # Attempt login with invalid password
        login_res = self.client.post('/api/auth/login', json={
            'email': email,
            'password': 'IncorrectPassword'
        })
        self.assertEqual(login_res.status_code, 401)
        data = login_res.get_json()
        self.assertIn('invalid', data['error'].lower())


    def test_07_login_nonexistent_user(self):
        """Test login with an unknown email returns 401."""
        login_res = self.client.post('/api/auth/login', json={
            'email': 'unknown_person_99999@doesnotexist.com',
            'password': 'SomePassword@123'
        })
        self.assertEqual(login_res.status_code, 401)

if __name__ == '__main__':
    unittest.main()
