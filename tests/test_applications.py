import unittest
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from database.db import query_db, execute_db

class ApplicationsTestCase(unittest.TestCase):
    def setUp(self):
        # Activate email mock so tests don't hit real SMTP
        os.environ['FLASK_TESTING'] = '1'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Login student (seeded user has is_verified=1)
        s_res = self.client.post('/api/auth/login', json={
            'email': 'priya.reddy@student.edu',
            'password': 'Password@123'
        })
        self.stud_token = s_res.get_json()['token']
        self.stud_headers = {'Authorization': f'Bearer {self.stud_token}'}

        # Login employer (seeded user has is_verified=1)
        e_res = self.client.post('/api/auth/login', json={
            'email': 'hiring@brewandbean.in',
            'password': 'Password@123'
        })
        self.emp_token = e_res.get_json()['token']
        self.emp_headers = {'Authorization': f'Bearer {self.emp_token}'}

        # Find a job owned by hiring@brewandbean.in
        emp_user = query_db("SELECT id FROM users WHERE email = 'hiring@brewandbean.in'", one=True)
        emp_profile = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (emp_user['id'],), one=True)
        job = query_db("SELECT id FROM jobs WHERE employer_id = ? LIMIT 1", (emp_profile['id'],), one=True)
        self.job_id = job['id']

    def tearDown(self):
        os.environ.pop('FLASK_TESTING', None)

    def _register_and_get_token(self, email, full_name='Test Applicant', role='student', password='Password@123'):
        """Register a new user, force-verify, then login and return the JWT token."""
        reg_payload = {
            'email': email,
            'password': password,
            'full_name': full_name,
            'role': role
        }
        self.client.post('/api/auth/register', json=reg_payload)
        # Force email verification (bypass real email OTP in tests)
        with self.app.app_context():
            execute_db("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
        # Login to get JWT
        login_res = self.client.post('/api/auth/login', json={'email': email, 'password': password})
        return login_res.get_json()['token']


    def test_01_apply_to_job(self):
        """Test student applies to a job successfully."""
        import uuid
        email = f"app_tester_{uuid.uuid4().hex[:8]}@student.edu"
        token = self._register_and_get_token(email, full_name='Applicant One', role='student')
        headers = {'Authorization': f'Bearer {token}'}

        payload = {
            'job_id': self.job_id,
            'cover_note': 'I am highly experienced with customer engagement and ready for weekend shifts.'
        }
        res = self.client.post('/api/applications', json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('application_id', data)
        app_id = data['application_id']

        # Verify application in DB
        app_record = query_db("SELECT * FROM applications WHERE id = ?", (app_id,), one=True)
        self.assertIsNotNone(app_record)
        self.assertIn(app_record['status'], ['applied', 'pending'])
        self.assertEqual(app_record['job_id'], self.job_id)

    def test_02_duplicate_application_prevention(self):
        """Test that applying twice to the same job returns 400 error."""
        import uuid
        email = f"app_dup_{uuid.uuid4().hex[:8]}@student.edu"
        token = self._register_and_get_token(email, full_name='Applicant Two', role='student')
        headers = {'Authorization': f'Bearer {token}'}

        payload = {'job_id': self.job_id, 'cover_note': 'First apply'}
        # First submission
        res1 = self.client.post('/api/applications', json=payload, headers=headers)
        self.assertEqual(res1.status_code, 201)

        # Duplicate submission
        res2 = self.client.post('/api/applications', json=payload, headers=headers)
        self.assertEqual(res2.status_code, 400)
        self.assertIn('already applied', res2.get_json()['error'].lower())

    def test_03_employer_shortlist_and_accept(self):
        """Test employer lifecycle: view applicant, shortlist, and accept student."""
        import uuid
        email = f"app_acc_{uuid.uuid4().hex[:8]}@student.edu"
        token = self._register_and_get_token(email, full_name='Applicant Three', role='student')
        headers = {'Authorization': f'Bearer {token}'}

        res = self.client.post('/api/applications', json={'job_id': self.job_id, 'cover_note': 'Good candidate'}, headers=headers)
        app_id = res.get_json()['application_id']

        # 1. Employer shortlists student
        shortlist_res = self.client.patch(f'/api/applications/{app_id}/status', json={'status': 'shortlisted'}, headers=self.emp_headers)
        self.assertEqual(shortlist_res.status_code, 200)

        check1 = query_db("SELECT status FROM applications WHERE id = ?", (app_id,), one=True)
        self.assertEqual(check1['status'], 'shortlisted')

        # 2. Employer accepts student
        accept_res = self.client.patch(f'/api/applications/{app_id}/status', json={'status': 'accepted'}, headers=self.emp_headers)
        self.assertEqual(accept_res.status_code, 200)

        check2 = query_db("SELECT status FROM applications WHERE id = ?", (app_id,), one=True)
        self.assertEqual(check2['status'], 'accepted')

        # Verify ACCEPT_JOB interaction recorded
        stud_prof = query_db("SELECT sp.id FROM student_profiles sp JOIN users u ON sp.user_id = u.id WHERE u.email = ?", (email,), one=True)
        interaction = query_db("SELECT * FROM job_interactions WHERE student_id = ? AND job_id = ? AND interaction_type = 'ACCEPT_JOB'", (stud_prof['id'], self.job_id), one=True)
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction['interaction_weight'], 7)

    def test_04_employer_reject(self):
        """Test employer rejecting an application updates status and registers interaction."""
        import uuid
        email = f"app_rej_{uuid.uuid4().hex[:8]}@student.edu"
        token = self._register_and_get_token(email, full_name='Applicant Four', role='student')
        headers = {'Authorization': f'Bearer {token}'}

        res = self.client.post('/api/applications', json={'job_id': self.job_id, 'cover_note': 'Apply to reject'}, headers=headers)
        app_id = res.get_json()['application_id']

        # Employer rejects
        reject_res = self.client.patch(f'/api/applications/{app_id}/status', json={'status': 'rejected'}, headers=self.emp_headers)
        self.assertEqual(reject_res.status_code, 200)

        check = query_db("SELECT status FROM applications WHERE id = ?", (app_id,), one=True)
        self.assertEqual(check['status'], 'rejected')

if __name__ == '__main__':
    unittest.main()

