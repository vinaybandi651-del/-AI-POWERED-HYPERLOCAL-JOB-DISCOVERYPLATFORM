"""Check exact API response structure for profile page."""
import sys, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import create_app
from database.db import query_db
from utils.security import create_access_token

app = create_app()

with app.test_client() as c:
    # Test with student
    student = query_db(
        "SELECT id, email, role, full_name FROM users WHERE role='student' LIMIT 1",
        (), one=True
    )
    token = create_access_token(student['id'], student['email'], student['role'], student['full_name'])
    hdrs = {'Authorization': 'Bearer ' + token}

    r = c.get('/api/users/profile', headers=hdrs)
    d = json.loads(r.data)
    print("=== /api/users/profile response keys ===")
    print("Top-level keys:", list(d.keys()))
    print("user keys:", list(d.get('user', {}).keys()))
    print("profile keys:", list(d.get('profile', {}).keys()))
    print()
    print("user.full_name:", d.get('user', {}).get('full_name'))
    print("user.avatar_url:", d.get('user', {}).get('avatar_url'))
    print("user.is_verified:", d.get('user', {}).get('is_verified'))
    print("profile.degree:", d.get('profile', {}).get('degree'))
    print("profile.skills:", d.get('profile', {}).get('skills'))
    print("profile.bio:", d.get('profile', {}).get('bio'))

    # Test with employer
    emp = query_db(
        "SELECT id, email, role, full_name FROM users WHERE role='employer' LIMIT 1",
        (), one=True
    )
    if emp:
        token2 = create_access_token(emp['id'], emp['email'], emp['role'], emp['full_name'])
        r2 = c.get('/api/users/profile', headers={'Authorization': 'Bearer ' + token2})
        d2 = json.loads(r2.data)
        print()
        print("=== Employer profile keys ===")
        print("profile keys:", list(d2.get('profile', {}).keys()))
        print("profile.company_name:", d2.get('profile', {}).get('company_name'))

    # Check what the students/profile endpoint returns (old endpoint)
    r3 = c.get('/api/students/profile', headers=hdrs)
    d3 = json.loads(r3.data)
    print()
    print("=== /api/students/profile response keys ===")
    print("Top-level keys:", list(d3.keys()))
    if 'profile' in d3:
        print("profile.full_name:", d3['profile'].get('full_name'))
        print("profile.degree:", d3['profile'].get('degree'))
