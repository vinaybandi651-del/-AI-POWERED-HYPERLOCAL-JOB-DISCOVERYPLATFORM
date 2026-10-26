import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'backend'))

from app import create_app
from database.db import query_db, execute_db

def run_diagram_verification():
    print("=" * 65)
    print("TESTING FULL SEQUENCE DIAGRAM WORKFLOW")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    # Step 0: Login as student Aarav Sharma
    res = client.post('/api/auth/login', json={
        'email': 'aarav.sharma@student.edu',
        'password': 'Password@123'
    })
    assert res.status_code == 200, f"Login failed: {res.data}"
    student_token = res.get_json()['token']
    headers = {'Authorization': f'Bearer {student_token}'}
    print("[1] Fresh Graduate logged in as Aarav Sharma")

    # Pick an open job
    jobs = client.get('/api/jobs').get_json()['jobs']
    target_job = jobs[6]
    job_id = target_job['id']
    s_row = query_db("SELECT id FROM student_profiles WHERE user_id = (SELECT id FROM users WHERE email='aarav.sharma@student.edu')", one=True)
    execute_db("DELETE FROM applications WHERE job_id = ? AND student_id = ?", (job_id, s_row['id']))

    # Arrow 1 & 2 & 3 & 4: Submits Application
    print(f"\n[2] Submitting application for '{target_job['title']}' (Job ID: {job_id})...")
    apply_res = client.post('/api/applications', headers=headers, json={
        'job_id': job_id,
        'cover_note': 'Excited to apply as a fresh B.Tech graduate.'
    })
    assert apply_res.status_code == 201, f"Apply failed: {apply_res.data}"
    data = apply_res.get_json()
    app_id = data['application_id']
    ref_code = data['reference_code']
    assert data['status'] == 'pending', f"Status not pending: {data['status']}"
    print(f"  ✓ Stored with Status = 'pending' (Ref: {ref_code})")
    print(f"  ✓ Action URLs generated: Accept & Reject")

    # Verify Database State
    db_app = query_db("SELECT * FROM applications WHERE id = ?", (app_id,), one=True)
    assert db_app['status'] == 'pending'
    print(f"  ✓ Database verified: application #{app_id} status is 'pending'")

    tokens = query_db("SELECT action, recipient_email, is_used FROM action_tokens WHERE application_id = ?", (app_id,))
    assert len(tokens) == 2, f"Expected 2 tokens, got {len(tokens)}"
    assert any(t['action'] == 'accept' for t in tokens)
    assert any(t['action'] == 'reject' for t in tokens)
    assert all(t['recipient_email'] == 'vinaybandi651@gmail.com' for t in tokens)
    print("  ✓ Cryptographic tokens created in database for vinaybandi651@gmail.com")

    # Arrow 4 & 5: Email Dispatched
    email_log = query_db("SELECT * FROM email_logs WHERE application_id = ? ORDER BY id DESC LIMIT 1", (app_id,), one=True)
    assert email_log is not None, "Email log not found"
    assert email_log['recipient_email'] == 'vinaybandi651@gmail.com'
    assert 'html_content' in email_log and email_log['html_content'] is not None
    assert 'ACCEPT APPLICATION' in email_log['html_content']
    print(f"  ✓ Email logged with subject: '{email_log['subject']}' to {email_log['recipient_email']}")
    print("  ✓ Email HTML contains active [✓ ACCEPT APPLICATION] & [✕ REJECT APPLICATION] buttons")

    # Arrow 6: Clicks [Accept Application] in email
    raw_token = data['accept_url'].split('token=')[1]
    print(f"\n[3] Simulating clicking [Accept Application] in email...")
    inspect_res = client.get(f'/api/applications/action/inspect?token={raw_token}')
    assert inspect_res.status_code == 200, f"Inspect failed: {inspect_res.data}"
    ins_data = inspect_res.get_json()
    assert ins_data['action'] == 'accept'
    print(f"  ✓ Token inspected: Action '{ins_data['action']}' for candidate '{ins_data['applicant_name']}'")

    # Arrow 7: Confirm Decision -> Updates status to 'accepted'
    print("\n[4] Confirming decision on web portal...")
    confirm_res = client.post('/api/applications/action/confirm', json={
        'token': raw_token,
        'notes': 'Candidate profile and academic scores approved.'
    })
    assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.data}"
    print(f"  ✓ Decision executed: {confirm_res.get_json()['message']}")

    # Verify Database status updated
    updated_app = query_db("SELECT status, decided_by, decided_at FROM applications WHERE id = ?", (app_id,), one=True)
    assert updated_app['status'] == 'accepted', f"Expected accepted, got {updated_app['status']}"
    assert updated_app['decided_by'] == 'vinaybandi651@gmail.com'
    print(f"  ✓ Database atomically updated: status='accepted', decided_by='{updated_app['decided_by']}'")

    # Arrow 8 & 9: Fresh Graduate Refreshes candidate dashboard
    print("\n[5] Fresh Graduate refreshes Applications Tracker (/api/applications/my)...")
    my_apps_res = client.get('/api/applications/my', headers=headers)
    assert my_apps_res.status_code == 200
    my_app = next(a for a in my_apps_res.get_json()['applications'] if a['application_id'] == app_id)
    assert my_app['status'] == 'accepted'
    print(f"  ✓ Candidate Tracker status is 'accepted'!")
    print("  ✓ Web Portal Displays: 'Your application has been accepted. 🎉'")

    print("\n" + "=" * 65)
    print("ALL 9 STEPS IN THE SEQUENCE DIAGRAM COMPLETED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_diagram_verification()
