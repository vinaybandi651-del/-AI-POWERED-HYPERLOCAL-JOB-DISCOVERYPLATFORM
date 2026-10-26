import unittest
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from utils.geo import haversine_distance
from recommendation.content_based import calculate_content_score
from recommendation.location_matching import evaluate_location_match
from recommendation.collaborative import calculate_collaborative_score
from recommendation.hybrid_recommender import (
    calculate_availability_score,
    calculate_salary_score,
    rank_jobs_for_student
)

class RecommendationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_skill_and_content_matching(self):
        """Test content-based filtering produces higher scores for high skill/category overlap."""
        student = {
            'bio': 'Passionate Python developer building web applications with Flask and React.',
            'preferred_categories': ['Tech & IT'],
            'preferred_job_type': 'Part-time',
            'experience_level': 'Intermediate'
        }
        student_skills = ['Python', 'Flask', 'React', 'SQL', 'Git']

        # Job A: Highly relevant Tech role
        job_relevant = {
            'title': 'Junior Python Backend Assistant',
            'description': 'Help build RESTful microservices in Python and Flask with PostgreSQL database.',
            'category': 'Tech & IT',
            'job_type': 'Part-time',
            'experience_required': 'Intermediate'
        }
        job_a_skills = ['Python', 'Flask', 'SQL']

        # Job B: Irrelevant Cafe Barista role
        job_irrelevant = {
            'title': 'Espresso Barista and Coffee Maker',
            'description': 'Steam milk, brew espresso, grind specialty beans and maintain counter cleanliness.',
            'category': 'Hospitality & Food',
            'job_type': 'Weekend Gig',
            'experience_required': 'No Experience'
        }
        job_b_skills = ['Barista', 'Latte Art', 'Food Safety']

        score_a, reasons_a = calculate_content_score(student, job_relevant, student_skills, job_a_skills)
        score_b, reasons_b = calculate_content_score(student, job_irrelevant, student_skills, job_b_skills)

        # Relevant job should have substantially higher score
        self.assertGreater(score_a, score_b)
        self.assertGreaterEqual(score_a, 0.70)
        self.assertLess(score_b, 0.40)
        self.assertTrue(any('skill' in r.lower() for r in reasons_a))

    def test_02_location_calculation(self):
        """Test Haversine distance and location proximity decay score."""
        # Cyber Towers (17.4504, 78.3808) to Inorbit Mall (17.4348, 78.3872) ~1.8 km
        lat1, lon1 = 17.4504, 78.3808
        lat2, lon2 = 17.4348, 78.3872
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertAlmostEqual(dist, 1.84, delta=0.5)

        student = {'latitude': 17.4483, 'longitude': 78.3915, 'max_distance_km': 10.0}
        
        # Nearby job (~1 km)
        job_close = {'latitude': 17.4504, 'longitude': 78.3808}
        score_close, dist_close, _ = evaluate_location_match(student, job_close)
        self.assertLess(dist_close, 2.0)
        self.assertGreaterEqual(score_close, 0.85)

        # Far job (~25 km away)
        job_far = {'latitude': 17.2400, 'longitude': 78.4200}
        score_far, dist_far, _ = evaluate_location_match(student, job_far)
        self.assertGreater(dist_far, 20.0)
        self.assertLessEqual(score_far, 0.30)

    def test_03_availability_matching(self):
        """Test matching calendar days and working hours."""
        student = {
            'available_days': ['Saturday', 'Sunday'],
            'available_time_start': '10:00',
            'available_time_end': '19:00'
        }

        # Matching job: Saturday within hours
        job_match = {
            'date_needed': 'Saturday',
            'start_time': '11:00',
            'end_time': '16:00'
        }
        score_match, reason_match = calculate_availability_score(student, job_match)
        self.assertGreaterEqual(score_match, 0.90)

        # Clashing job: Tuesday during college hours
        job_clash = {
            'date_needed': 'Tuesday',
            'start_time': '09:00',
            'end_time': '17:00'
        }
        score_clash, reason_clash = calculate_availability_score(student, job_clash)
        self.assertLess(score_clash, score_match)
        self.assertIn('clash', reason_clash.lower())

    def test_04_salary_matching(self):
        """Test compensation target alignment."""
        student = {'expected_salary': 600.0, 'salary_type': 'day'}

        # Job pays 800 (exceeds) -> score 1.0
        job_good = {'pay_amount': 800.0, 'pay_frequency': 'day'}
        score_good, _ = calculate_salary_score(student, job_good)
        self.assertEqual(score_good, 1.0)

        # Job pays 200 (far below expectation) -> lower score
        job_low = {'pay_amount': 200.0, 'pay_frequency': 'day'}
        score_low, _ = calculate_salary_score(student, job_low)
        self.assertLess(score_low, 0.5)

    def test_05_collaborative_filtering_and_cold_start(self):
        """Test collaborative filtering with history vs cold-start fallback."""
        interactions = [
            {'student_id': 1, 'job_id': 10, 'interaction_weight': 5},
            {'student_id': 1, 'job_id': 11, 'interaction_weight': 3},
            {'student_id': 2, 'job_id': 10, 'interaction_weight': 5},
            {'student_id': 2, 'job_id': 12, 'interaction_weight': 5},
        ]

        # Student with interaction history
        score_warm, reason_warm, is_cold = calculate_collaborative_score(1, 10, interactions)
        self.assertFalse(is_cold)
        self.assertGreater(score_warm, 0.3)
        self.assertLessEqual(score_warm, 1.0)

        # New student with 0 interactions (Cold start on known job)
        score_cold_pop, reason_pop, is_cold_flag1 = calculate_collaborative_score(999, 10, interactions)
        self.assertTrue(is_cold_flag1)
        self.assertGreaterEqual(score_cold_pop, 0.5)

        # New student with unseen job
        score_cold_unseen, reason_unseen, is_cold_flag2 = calculate_collaborative_score(999, 9999, interactions)
        self.assertTrue(is_cold_flag2)
        self.assertEqual(score_cold_unseen, 0.5)

    def test_06_hybrid_score_calculation(self):
        """Test the 5-factor hybrid ensemble formula bounds and weights."""
        student = {
            'id': 1,
            'bio': 'Python software engineering student',
            'preferred_categories': ['Tech & IT'],
            'preferred_job_type': 'Part-time',
            'experience_level': 'Intermediate',
            'latitude': 17.4483,
            'longitude': 78.3915,
            'max_distance_km': 10.0,
            'expected_salary': 600.0,
            'salary_type': 'day',
            'available_days': ['Saturday', 'Sunday'],
            'available_time_start': '10:00',
            'available_time_end': '19:00'
        }
        student_skills = ['Python', 'SQL', 'Flask']

        jobs = [{
            'id': 101,
            'title': 'Junior Python Developer',
            'description': 'Develop backend REST APIs using Python and Flask.',
            'category': 'Tech & IT',
            'job_type': 'Part-time',
            'experience_required': 'Intermediate',
            'latitude': 17.4500,
            'longitude': 78.3900,
            'pay_amount': 700.0,
            'pay_frequency': 'day',
            'date_needed': 'Saturday',
            'start_time': '10:00',
            'end_time': '18:00'
        }]
        job_skills_map = {101: ['Python', 'Flask', 'SQL']}
        interactions = [{'student_id': 1, 'job_id': 101, 'interaction_weight': 5}]

        results = rank_jobs_for_student(student, jobs, student_skills, job_skills_map, interactions)
        self.assertEqual(len(results), 1)
        res = results[0]

        # Check bounds: 0 <= match_score <= 100
        self.assertGreaterEqual(res['match_score'], 0)
        self.assertLessEqual(res['match_score'], 100)
        # Should be a top match for high skill, location, and salary alignment
        self.assertGreaterEqual(res['match_score'], 80)

        # Check breakdown components exist
        self.assertIn('scores_breakdown', res)
        b = res['scores_breakdown']
        self.assertIn('content_score', b)
        self.assertIn('location_score', b)
        self.assertIn('availability_score', b)
        self.assertIn('collaborative_score', b)
        self.assertIn('salary_score', b)

        # Check dynamic explanation reasons
        self.assertGreater(len(res['reasons']), 0)
        self.assertTrue(any('skill' in r.lower() for r in res['reasons']))

    def test_07_recommendations_api(self):
        """Test GET /api/recommendations/my returns ranked jobs for student."""
        res_login = self.client.post('/api/auth/login', json={
            'email': 'aarav.sharma@student.edu',
            'password': 'Password@123'
        })
        token = res_login.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}

        rec_res = self.client.get('/api/recommendations/my', headers=headers)
        self.assertEqual(rec_res.status_code, 200)
        data = rec_res.get_json()
        self.assertIn('recommendations', data)
        recs = data['recommendations']
        self.assertGreater(len(recs), 0)

        # Verify sorted descending by match score
        scores = [r['match_score'] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))

if __name__ == '__main__':
    unittest.main()
