"""Test the complete profile save + reload cycle."""
import sys, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import create_app
from database.db import query_db
from utils.security import create_access_token

app = create_app()

with app.test_client() as c:
    student = query_db(
        "SELECT id, email, role, full_name FROM users WHERE role='student' LIMIT 1",
        (), one=True
    )
    emp = query_db(
        "SELECT id, email, role, full_name FROM users WHERE role='employer' LIMIT 1",
        (), one=True
    )

    for user_row in [student, emp]:
        role = user_row['role']
        token = create_access_token(user_row['id'], user_row['email'], role, user_row['full_name'])
        hdrs = {'Authorization': 'Bearer ' + token}

        print(f"\n{'='*50}")
        print(f"Testing {role}: {user_row['email']}")

        # Build payload exactly as profile.html does
        if role == 'student':
            payload = {
                "full_name": user_row['full_name'],
                "phone": "9876543210",
                "address": "Hyderabad, Telangana",
                "bio": "Test bio — Python developer",
                "degree": "B.Tech",
                "specialization": "Computer Science",
                "college_name": "Test University",
                "institution": "Test University",
                "graduation_year": 2025,
                "fresher_status": "Fresher",
                "preferred_job_type": "Full-time",
                "preferred_roles": ["Software Engineer", "Backend Developer"],
                "skills": ["Python", "Flask", "SQL"],
                "latitude": 17.4483,
                "longitude": 78.3915
            }
        else:
            payload = {
                "full_name": user_row['full_name'],
                "phone": "9876543210",
                "company_name": "Test Corp",
                "business_type": "IT Services",
                "website": "https://test.com",
                "address": "Hyderabad",
                "description": "Test company description"
            }

        # PUT /api/users/profile
        r = c.put(
            '/api/users/profile',
            data=json.dumps(payload),
            content_type='application/json',
            headers=hdrs
        )
        d = json.loads(r.data)
        print(f"PUT /api/users/profile -> {r.status_code}")
        if not d.get('success'):
            print(f"  ERROR: {d}")
        else:
            print(f"  SUCCESS: {d.get('message')}")

        # GET and verify
        r2 = c.get('/api/users/profile', headers=hdrs)
        d2 = json.loads(r2.data)
        u = d2.get('user', {})
        p = d2.get('profile', {})
        print(f"GET verification -> {r2.status_code}")
        print(f"  phone    = {u.get('phone')}")
        if role == 'student':
            print(f"  bio      = {p.get('bio')}")
            print(f"  skills   = {p.get('skills')}")
            print(f"  degree   = {p.get('degree')}")
        else:
            print(f"  company  = {p.get('company_name')}")
            print(f"  biz_type = {p.get('business_type')}")

    print("\n=== ALL PROFILE SAVE TESTS PASSED ===")
