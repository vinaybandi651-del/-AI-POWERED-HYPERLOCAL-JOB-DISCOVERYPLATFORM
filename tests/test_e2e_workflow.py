import unittest
import json
import os
import sys
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from database.db import query_db, execute_db

class EndToEndWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['FLASK_TESTING'] = '1'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        os.environ.pop('FLASK_TESTING', None)

    def _force_verify(self, email):
        with self.app.app_context():
            execute_db("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))


    def test_complete_student_to_employer_workflow(self):
        """
        Executes Requirement 35 & 36:
        Full student & employer paired workflow:
        Student registers -> edits profile -> checks AI recommendations -> saves job -> applies.
        Employer registers -> posts job -> views applicants -> shortlists -> chats -> accepts.
        Application status transitions: APPLIED -> SHORTLISTED -> ACCEPTED.
        Job completed -> Review submitted -> Interaction recorded.
        """
        uid = uuid.uuid4().hex[:8]
        s_email = f"e2e_student_{uid}@college.edu"
        e_email = f"e2e_employer_{uid}@company.com"
        password = "SecurePassword@123"

        # -------------------------------------------------------------
        # 1. STUDENT REGISTRATION & LOGIN
        # -------------------------------------------------------------
        s_reg = self.client.post('/api/auth/register', json={
            'email': s_email,
            'password': password,
            'full_name': 'E2E Test Student',
            'role': 'student',
            'phone': '+91 9888877771'
        })
        self.assertEqual(s_reg.status_code, 201)

        self._force_verify(s_email)

        s_login = self.client.post('/api/auth/login', json={'email': s_email, 'password': password})
        self.assertEqual(s_login.status_code, 200)
        s_token = s_login.get_json()['token']
        s_headers = {'Authorization': f'Bearer {s_token}'}
        s_user_id = s_login.get_json()['user']['id']

        # -------------------------------------------------------------
        # 2. STUDENT COMPLETES PROFILE (Skills, Location, Availability, Pay)
        # -------------------------------------------------------------
        profile_update = {
            'education': 'B.Tech CSE (Final Year)',
            'institution': 'Hyderabad Institute of Technology',
            'experience_level': 'Intermediate',
            'bio': 'Passionate student coder and cafe enthusiast looking for nearby weekend gigs.',
            'preferred_categories': ['Hospitality & Food', 'Tech & IT'],
            'preferred_job_type': 'Weekend Gig',
            'expected_salary': 650.0,
            'salary_type': 'day',
            'max_distance_km': 10.0,
            'latitude': 17.4483,
            'longitude': 78.3915,
            'address': 'Madhapur Metro Station, Hyderabad',
            'available_days': ['Saturday', 'Sunday'],
            'available_time_start': '10:00',
            'available_time_end': '19:00',
            'skills': ['Customer Service', 'Barista', 'Python', 'Communication']
        }
        p_res = self.client.put('/api/students/profile', json=profile_update, headers=s_headers)
        self.assertEqual(p_res.status_code, 200)

        get_p = self.client.get('/api/students/profile', headers=s_headers)
        self.assertEqual(get_p.status_code, 200)
        self.assertGreaterEqual(get_p.get_json()['profile']['completion_percentage'], 80)

        # -------------------------------------------------------------
        # 3. EMPLOYER REGISTRATION & PROFILE
        # -------------------------------------------------------------
        e_reg = self.client.post('/api/auth/register', json={
            'email': e_email,
            'password': password,
            'full_name': 'E2E Cafe Manager',
            'role': 'employer',
            'phone': '+91 9999911112',
            'company_name': 'Aroma Wave Specialty Roasters',
            'business_type': 'Hospitality & Food'
        })
        self.assertEqual(e_reg.status_code, 201)

        self._force_verify(e_email)

        e_login = self.client.post('/api/auth/login', json={'email': e_email, 'password': password})
        self.assertEqual(e_login.status_code, 200)
        e_token = e_login.get_json()['token']
        e_headers = {'Authorization': f'Bearer {e_token}'}
        e_user_id = e_login.get_json()['user']['id']

        # -------------------------------------------------------------
        # 4. EMPLOYER POSTS A JOB
        # -------------------------------------------------------------
        job_payload = {
            'title': 'Weekend Artisan Barista & Cashier',
            'description': 'Help serve specialty pour-overs and cold brew on busy weekend mornings.',
            'category': 'Hospitality & Food',
            'job_type': 'Weekend Gig',
            'pay_amount': 700.0,
            'pay_frequency': 'day',
            'date_needed': 'Saturday & Sunday',
            'start_time': '10:00',
            'end_time': '17:00',
            'workers_needed': 1,
            'experience_required': 'Beginner',
            'location_address': 'Madhapur Hub, Hyderabad',
            'latitude': 17.4490,
            'longitude': 78.3910, # Very close (~0.1 km)
            'skills': ['Barista', 'Customer Service', 'Cashier']
        }
        job_res = self.client.post('/api/jobs', json=job_payload, headers=e_headers)
        self.assertEqual(job_res.status_code, 201)
        job_id = job_res.get_json()['job_id']

        # -------------------------------------------------------------
        # 5. STUDENT CHECKS AI RECOMMENDATIONS & VERIFIES SCORES
        # -------------------------------------------------------------
        rec_res = self.client.get('/api/recommendations/my', headers=s_headers)
        self.assertEqual(rec_res.status_code, 200)
        recs = rec_res.get_json()['recommendations']
        self.assertGreater(len(recs), 0)

        # Find the newly posted job in recommendations
        target_rec = next((r for r in recs if r['id'] == job_id), None)
        self.assertIsNotNone(target_rec, "Newly posted nearby job must be present in recommendations")
        
        # Verify AI Match Breakdown components
        self.assertGreaterEqual(target_rec['match_score'], 80, "High skill + close proximity + availability must score >= 80%")
        b = target_rec['scores_breakdown']
        self.assertGreaterEqual(b['content_score'], 70)
        self.assertGreaterEqual(b['location_score'], 90)
        self.assertGreaterEqual(b['availability_score'], 85)
        self.assertGreaterEqual(b['salary_score'], 90)
        self.assertGreater(len(target_rec['reasons']), 0)

        # -------------------------------------------------------------
        # 6. STUDENT SAVES (BOOKMARKS) THE JOB
        # -------------------------------------------------------------
        save_res = self.client.post(f'/api/saved_jobs/{job_id}', headers=s_headers)
        self.assertEqual(save_res.status_code, 200)
        self.assertTrue(save_res.get_json()['saved'])

        # Verify in saved list
        saved_list = self.client.get('/api/saved_jobs', headers=s_headers).get_json()['saved_jobs']
        self.assertTrue(any(j['id'] == job_id for j in saved_list))

        # -------------------------------------------------------------
        # 7. STUDENT APPLIES TO THE JOB
        # -------------------------------------------------------------
        app_res = self.client.post('/api/applications', json={
            'job_id': job_id,
            'cover_note': 'I have weekend availability and barista training!'
        }, headers=s_headers)
        self.assertEqual(app_res.status_code, 201)
        application_id = app_res.get_json()['application_id']

        # Verify initial status is 'applied'
        my_apps = self.client.get('/api/applications/my', headers=s_headers).get_json()['applications']
        target_app = next(a for a in my_apps if a['application_id'] == application_id)
        self.assertEqual(target_app['status'], 'applied')

        # -------------------------------------------------------------
        # 8. EMPLOYER VIEWS APPLICANTS
        # -------------------------------------------------------------
        applicants_res = self.client.get(f'/api/applications/job/{job_id}', headers=e_headers)
        self.assertEqual(applicants_res.status_code, 200)
        applicants = applicants_res.get_json()['applicants']
        self.assertEqual(len(applicants), 1)
        self.assertEqual(applicants[0]['student_email'], s_email)
        self.assertIn('barista', [s.lower() for s in applicants[0]['matched_skills']])

        # -------------------------------------------------------------
        # 9. EMPLOYER SHORTLISTS STUDENT (Status: applied -> shortlisted)
        # -------------------------------------------------------------
        sl_res = self.client.patch(f'/api/applications/{application_id}/status', json={'status': 'shortlisted'}, headers=e_headers)
        self.assertEqual(sl_res.status_code, 200)

        # Student verifies status changed to 'shortlisted'
        s_apps1 = self.client.get('/api/applications/my', headers=s_headers).get_json()['applications']
        app_state1 = next(a for a in s_apps1 if a['application_id'] == application_id)
        self.assertEqual(app_state1['status'], 'shortlisted')

        # -------------------------------------------------------------
        # 10. REAL CHAT MESSAGING BETWEEN EMPLOYER AND STUDENT
        # -------------------------------------------------------------
        # Employer sends message
        msg_e = self.client.post('/api/chat/messages', json={
            'receiver_id': s_user_id,
            'job_id': job_id,
            'message_text': 'Hi! Can you come in for a quick 10-minute trial this Saturday?'
        }, headers=e_headers)
        self.assertIn(msg_e.status_code, [200, 201])

        # Student receives message in chat thread
        chat_thread = self.client.get(f'/api/chat/messages/{e_user_id}', headers=s_headers)
        self.assertEqual(chat_thread.status_code, 200)
        msgs = chat_thread.get_json()['messages']
        self.assertEqual(len(msgs), 1)
        self.assertIn('trial this Saturday', msgs[0]['message_text'])

        # Student replies
        msg_s = self.client.post('/api/chat/messages', json={
            'receiver_id': e_user_id,
            'job_id': job_id,
            'message_text': 'Yes absolutely, see you at 10 AM on Saturday!'
        }, headers=s_headers)
        self.assertIn(msg_s.status_code, [200, 201])

        # -------------------------------------------------------------
        # 11. EMPLOYER ACCEPTS STUDENT (Status: shortlisted -> accepted)
        # -------------------------------------------------------------
        acc_res = self.client.patch(f'/api/applications/{application_id}/status', json={'status': 'accepted'}, headers=e_headers)
        self.assertEqual(acc_res.status_code, 200)

        # Student verifies status is 'accepted'
        s_apps2 = self.client.get('/api/applications/my', headers=s_headers).get_json()['applications']
        app_state2 = next(a for a in s_apps2 if a['application_id'] == application_id)
        self.assertEqual(app_state2['status'], 'accepted')

        # -------------------------------------------------------------
        # 12. EMPLOYER COMPLETES JOB & SUBMITS REVIEWS
        # -------------------------------------------------------------
        job_done_res = self.client.patch(f'/api/jobs/{job_id}/status', json={'status': 'completed'}, headers=e_headers)
        self.assertEqual(job_done_res.status_code, 200)

        # Student submits review for employer
        rev_res = self.client.post('/api/reviews', json={
            'job_id': job_id,
            'reviewee_id': e_user_id,
            'rating': 5.0,
            'comment': 'Fantastic cafe environment, great supportive staff and fair on-time payment!'
        }, headers=s_headers)
        self.assertEqual(rev_res.status_code, 201)

        # Verify reviews retrievable
        job_revs = self.client.get(f'/api/reviews/job/{job_id}').get_json()['reviews']
        self.assertEqual(len(job_revs), 1)
        self.assertEqual(job_revs[0]['rating'], 5.0)

        # Verify RATE_JOB interaction was recorded in database
        student_prof = query_db("SELECT id FROM student_profiles WHERE user_id = ?", (s_user_id,), one=True)
        rate_interaction = query_db("SELECT * FROM job_interactions WHERE student_id = ? AND job_id = ? AND interaction_type = 'RATE_JOB'", (student_prof['id'], job_id), one=True)
        self.assertIsNotNone(rate_interaction)
        self.assertEqual(rate_interaction['interaction_weight'], 8)

if __name__ == '__main__':
    unittest.main()
