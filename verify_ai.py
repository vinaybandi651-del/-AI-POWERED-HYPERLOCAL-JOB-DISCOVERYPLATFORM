import sys
import os

# Ensure backend directory is in path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from database.db import query_db
from recommendation.hybrid_recommender import rank_jobs_for_student

def verify_student_job(student_email=None):
    """Run real AI matching algorithm on student and jobs and print detailed breakdown."""
    if not student_email:
        student_email = 'aarav.sharma@student.edu'

    student_user = query_db("SELECT id, full_name, email FROM users WHERE email = ?", (student_email,), one=True)
    if not student_user:
        print(f"Error: Student with email '{student_email}' not found in database.")
        return

    student = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (student_user['id'],), one=True)
    if not student:
        print(f"Error: Profile for '{student_email}' not found.")
        return

    student_skills = [s['skill_name'] for s in query_db("SELECT skill_name FROM student_skills WHERE student_id = ?", (student['id'],))]
    jobs = query_db("SELECT * FROM jobs WHERE status = 'active'")
    job_ids = [j['id'] for j in jobs]

    # Job skills map
    job_skills_map = {}
    if job_ids:
        placeholders = ','.join(['?'] * len(job_ids))
        skills_records = query_db(f"SELECT job_id, skill_name FROM job_skills WHERE job_id IN ({placeholders})", job_ids)
        for r in skills_records:
            job_skills_map.setdefault(r['job_id'], []).append(r['skill_name'])

    # Interactions
    interactions = query_db("SELECT * FROM job_interactions")

    # Weights
    weights_rec = query_db("SELECT * FROM recommendation_weights ORDER BY id DESC LIMIT 1", one=True)
    custom_weights = None
    if weights_rec:
        custom_weights = {
            'content': weights_rec['content_weight'],
            'location': weights_rec['location_weight'],
            'availability': weights_rec['availability_weight'],
            'collaborative': weights_rec['collaborative_weight'],
            'salary': weights_rec['salary_weight']
        }

    # Execute Hybrid Recommender
    results = rank_jobs_for_student(student, jobs, student_skills, job_skills_map, interactions, custom_weights)

    print("=" * 70)
    print(f"AI RECOMMENDATION VERIFICATION FOR STUDENT: {student_user['full_name']} ({student_user['email']})")
    print(f"Skills: {', '.join(student_skills)}")
    print(f"Location: ({student['latitude']:.4f}, {student['longitude']:.4f}) | Max Dist: {student['max_distance_km']} km")
    print("=" * 70)

    for idx, r in enumerate(results[:3], start=1):
        b = r['scores_breakdown']
        w = r['weights_used']
        print(f"\n--- Match #{idx} ---")
        print(f"Student:             {student_user['full_name']}")
        print(f"Job:                 {r['title']} ({r.get('location_address', 'Hyderabad')})")
        print(f"Distance:            {r['formatted_distance']}")
        print(f"Content Score:       {b['content_score']}%  (Weight: {w['content']*100:.0f}%)")
        print(f"Location Score:      {b['location_score']}%  (Weight: {w['location']*100:.0f}%)")
        print(f"Availability Score:  {b['availability_score']}%  (Weight: {w['availability']*100:.0f}%)")
        print(f"Salary Score:        {b['salary_score']}%  (Weight: {w['salary']*100:.0f}%)")
        print(f"Collaborative Score: {b['collaborative_score']}%  (Weight: {w['collaborative']*100:.0f}%)")
        print(f"--------------------------------------------------")
        print(f"Final Score:         {r['match_score']}% Match")
        print(f"AI Explanation Reasons:")
        for reason in r['reasons']:
            print(f"  {reason}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    email = sys.argv[1] if len(sys.argv) > 1 else 'aarav.sharma@student.edu'
    verify_student_job(email)
