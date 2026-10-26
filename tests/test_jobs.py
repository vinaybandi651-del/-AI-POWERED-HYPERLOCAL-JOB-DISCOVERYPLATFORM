import unittest
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app

class JobsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Login employer
        res = self.client.post('/api/auth/login', json={
            'email': 'hiring@brewandbean.in',
            'password': 'Password@123'
        })
        self.emp_token = res.get_json()['token']
        self.emp_headers = {'Authorization': f'Bearer {self.emp_token}'}

    def test_01_create_job(self):
        """Test employer creates a new job posting with skills."""
        payload = {
            'title': 'Weekend Nitro Cold Brew Specialist',
            'description': 'Handle high volume craft cold brew setup and service on busy weekend shifts.',
            'category': 'Hospitality & Food',
            'job_type': 'Weekend Gig',
            'pay_amount': 750.0,
            'pay_frequency': 'day',
            'date_needed': 'Weekends',
            'start_time': '10:00',
            'end_time': '17:00',
            'workers_needed': 2,
            'experience_required': 'Beginner',
            'location_address': 'Madhapur Cafe Strip, Hyderabad',
            'latitude': 17.4483,
            'longitude': 78.3915,
            'skills': ['Barista', 'Customer Service', 'POS Billing']
        }
        res = self.client.post('/api/jobs', json=payload, headers=self.emp_headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('job_id', data)
        self.created_job_id = data['job_id']

        # Verify job is retrievable via GET
        detail_res = self.client.get(f'/api/jobs/{self.created_job_id}')
        self.assertEqual(detail_res.status_code, 200)
        job_data = detail_res.get_json()['job']
        self.assertEqual(job_data['title'], 'Weekend Nitro Cold Brew Specialist')
        self.assertIn('Barista', job_data['skills'])

    def test_02_edit_job(self):
        """Test employer modifies an existing job."""
        # Create a job to edit
        res = self.client.post('/api/jobs', json={
            'title': 'Job To Edit',
            'description': 'Initial description',
            'category': 'Retail & Sales',
            'pay_amount': 500.0,
            'skills': ['Communication']
        }, headers=self.emp_headers)
        job_id = res.get_json()['job_id']

        # Update the job
        update_payload = {
            'title': 'Senior Weekend Cashier & Inventory Helper',
            'description': 'Updated description with higher responsibility.',
            'category': 'Retail & Sales',
            'pay_amount': 680.0,
            'skills': ['Communication', 'Cashier', 'Inventory Management']
        }
        edit_res = self.client.put(f'/api/jobs/{job_id}', json=update_payload, headers=self.emp_headers)
        self.assertEqual(edit_res.status_code, 200)

        # Verify changes persisted in database
        check_res = self.client.get(f'/api/jobs/{job_id}')
        job = check_res.get_json()['job']
        self.assertEqual(job['title'], 'Senior Weekend Cashier & Inventory Helper')
        self.assertEqual(job['pay_amount'], 680.0)
        self.assertIn('Inventory Management', job['skills'])

    def test_03_delete_job(self):
        """Test employer deletes a job posting."""
        # Create a job to delete
        res = self.client.post('/api/jobs', json={
            'title': 'Temporary Job To Delete',
            'description': 'Short lived posting',
            'category': 'Events & Promotion',
            'pay_amount': 450.0
        }, headers=self.emp_headers)
        job_id = res.get_json()['job_id']

        # Delete it
        del_res = self.client.delete(f'/api/jobs/{job_id}', headers=self.emp_headers)
        self.assertEqual(del_res.status_code, 200)

        # Confirm 404
        get_res = self.client.get(f'/api/jobs/{job_id}')
        self.assertEqual(get_res.status_code, 404)

    def test_04_search_jobs(self):
        """Test searching jobs by keyword queries the database properly."""
        res = self.client.get('/api/jobs?search=Barista')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(data['total'], 0)
        for j in data['jobs']:
            match = 'barista' in j['title'].lower() or 'barista' in j['description'].lower() or any('barista' in s.lower() for s in j.get('skills', []))
            self.assertTrue(match)

    def test_05_filter_jobs(self):
        """Test category, pay, and distance filters."""
        # Category filter
        res_cat = self.client.get('/api/jobs?category=Tech%20%26%20IT')
        self.assertEqual(res_cat.status_code, 200)
        jobs_cat = res_cat.get_json()['jobs']
        self.assertGreater(len(jobs_cat), 0)
        for j in jobs_cat:
            self.assertEqual(j['category'], 'Tech & IT')

        # Min pay filter
        res_pay = self.client.get('/api/jobs?min_pay=700')
        self.assertEqual(res_pay.status_code, 200)
        jobs_pay = res_pay.get_json()['jobs']
        self.assertGreater(len(jobs_pay), 0)
        for j in jobs_pay:
            self.assertGreaterEqual(j['pay_amount'], 700.0)

        # Distance filter
        res_dist = self.client.get('/api/jobs?lat=17.4483&lon=78.3915&max_distance=3.0')
        self.assertEqual(res_dist.status_code, 200)
        jobs_dist = res_dist.get_json()['jobs']
        for j in jobs_dist:
            self.assertIsNotNone(j['distance_km'])
            self.assertLessEqual(j['distance_km'], 3.0)

if __name__ == '__main__':
    unittest.main()
