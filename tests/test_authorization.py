import unittest
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from database.db import query_db

class AuthorizationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Login student
        s_res = self.client.post('/api/auth/login', json={
            'email': 'aarav.sharma@student.edu',
            'password': 'Password@123'
        })
        self.stud_token = s_res.get_json()['token']
        self.stud_headers = {'Authorization': f'Bearer {self.stud_token}'}

        # Login employer 1 (Brew and Bean)
        e1_res = self.client.post('/api/auth/login', json={
            'email': 'hiring@brewandbean.in',
            'password': 'Password@123'
        })
        self.emp1_token = e1_res.get_json()['token']
        self.emp1_headers = {'Authorization': f'Bearer {self.emp1_token}'}

        # Login employer 2 (ByteWave)
        e2_res = self.client.post('/api/auth/login', json={
            'email': 'campus@bytewave.io',
            'password': 'Password@123'
        })
        self.emp2_token = e2_res.get_json()['token']
        self.emp2_headers = {'Authorization': f'Bearer {self.emp2_token}'}

        # Login admin
        a_res = self.client.post('/api/auth/login', json={
            'email': 'admin@hyperlocaljobs.com',
            'password': 'Admin@123'
        })
        self.admin_token = a_res.get_json()['token']
        self.admin_headers = {'Authorization': f'Bearer {self.admin_token}'}

    def test_01_student_cannot_access_employer_functions(self):
        """Test student role is forbidden from employer-only endpoints."""
        # 1. Student trying to post a job
        job_payload = {
            'title': 'Hacker Job',
            'description': 'Student trying to post',
            'category': 'Tech & IT',
            'pay_amount': 999.0
        }
        res_post = self.client.post('/api/jobs', json=job_payload, headers=self.stud_headers)
        self.assertEqual(res_post.status_code, 403)
        self.assertIn('not allowed', res_post.get_json()['error'].lower())

        # 2. Student trying to update an application status
        res_patch = self.client.patch('/api/applications/1/status', json={'status': 'accepted'}, headers=self.stud_headers)
        self.assertEqual(res_patch.status_code, 403)

    def test_02_employer_cannot_modify_another_employers_jobs(self):
        """Test an employer cannot update or delete jobs belonging to a different business."""
        # Find a job owned by employer 1
        emp1_user = query_db("SELECT id FROM users WHERE email = 'hiring@brewandbean.in'", one=True)
        emp1_profile = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (emp1_user['id'],), one=True)
        job1 = query_db("SELECT id, title FROM jobs WHERE employer_id = ? LIMIT 1", (emp1_profile['id'],), one=True)
        job_id = job1['id']

        # Employer 2 attempts to edit Employer 1's job
        edit_payload = {
            'title': 'Hijacked Job Title By Competitor',
            'pay_amount': 1.0
        }
        res_edit = self.client.put(f'/api/jobs/{job_id}', json=edit_payload, headers=self.emp2_headers)
        self.assertEqual(res_edit.status_code, 403)
        self.assertIn('cannot modify another employer', res_edit.get_json()['error'].lower())

        # Employer 2 attempts to delete Employer 1's job
        res_del = self.client.delete(f'/api/jobs/{job_id}', headers=self.emp2_headers)
        self.assertEqual(res_del.status_code, 403)
        self.assertIn('cannot modify another employer', res_del.get_json()['error'].lower())

        # Verify job is intact in database
        check_job = query_db("SELECT title FROM jobs WHERE id = ?", (job_id,), one=True)
        self.assertNotEqual(check_job['title'], 'Hijacked Job Title By Competitor')

    def test_03_normal_user_cannot_access_admin_apis(self):
        """Test students and employers cannot access admin endpoints, but admin can."""
        # Student denied
        res_s = self.client.get('/api/admin/overview', headers=self.stud_headers)
        self.assertEqual(res_s.status_code, 403)

        # Employer denied
        res_e = self.client.get('/api/admin/analytics', headers=self.emp2_headers)
        self.assertEqual(res_e.status_code, 403)

        # Admin allowed
        res_a = self.client.get('/api/admin/overview', headers=self.admin_headers)
        self.assertEqual(res_a.status_code, 200)
        data = res_a.get_json()
        self.assertIn('total_users', data)
        self.assertIn('total_jobs', data)
        self.assertIn('total_applications', data)

if __name__ == '__main__':
    unittest.main()
