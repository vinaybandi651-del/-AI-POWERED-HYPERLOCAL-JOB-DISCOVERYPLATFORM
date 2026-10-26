from flask import Blueprint, request, jsonify
import secrets
from datetime import datetime, timezone, timedelta
from database.db import query_db, execute_db, get_db
from utils.security import token_required, role_required
from recommendation.hybrid_recommender import rank_jobs_for_student
from utils.geo import haversine_distance, format_distance
from utils.email_service import (
    send_email,
    generate_secure_token,
    hash_token,
    build_application_notification_email,
    build_applicant_decision_email
)
from config import Config

applications_bp = Blueprint('applications', __name__)

VALID_STATUSES = ['pending', 'applied', 'under_review', 'shortlisted', 'accepted', 'rejected', 'withdrawn', 'completed']

@applications_bp.route('', methods=['POST'])
@token_required
@role_required('student')
def apply_to_job():
    """
    Submits a student job application:
    - Validates student profile and active job
    - Prevents duplicate applications
    - Creates application record with unique reference code
    - Attaches candidate resume (uploaded or from profile)
    - Generates single-use cryptographic approval action tokens
    - Dispatches notification emails to configured reviewers
    """
    user_id = request.current_user['user_id']
    student = query_db("""
        SELECT sp.*, u.full_name, u.email as student_email, u.phone as student_phone, u.is_verified
        FROM student_profiles sp
        JOIN users u ON sp.user_id = u.id
        WHERE sp.user_id = ?
    """, (user_id,), one=True)
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    if student.get('is_verified') == 0:
        return jsonify({
            'error': 'Email verification required. Please verify your email address before applying for jobs.',
            'requires_verification': True,
            'email': student['student_email']
        }), 403

    data = request.get_json() or {}
    job_id = data.get('job_id')
    cover_note = data.get('cover_note', '').strip()
    resume_url = data.get('resume_url') or student.get('resume_url')

    if not job_id:
        return jsonify({'error': 'job_id is required'}), 400

    job = query_db("""
        SELECT j.*, ep.user_id as employer_user_id, ep.company_name
        FROM jobs j
        JOIN employer_profiles ep ON j.employer_id = ep.id
        WHERE j.id = ?
    """, (job_id,), one=True)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Check for duplicate application
    existing = query_db("SELECT id, status FROM applications WHERE job_id = ? AND student_id = ?", (job_id, student['id']), one=True)
    if existing:
        return jsonify({'error': f'You have already applied for this job (Status: {existing["status"]})'}), 400

    try:
        # Generate unique application reference
        ref_code = f"APP-2026-{secrets.randbelow(90000) + 10000}"

        # Keep initial status strictly as 'pending' until the admin or employer explicitly accepts or rejects it
        app_id = execute_db("""
            INSERT INTO applications (job_id, student_id, cover_note, resume_url, status, reference_code)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (job_id, student['id'], cover_note, resume_url, ref_code))

        # Record APPLY_JOB interaction for collaborative filtering (weight 5)
        execute_db("""
            INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight)
            VALUES (?, ?, 'APPLY_JOB', 5)
        """, (student['id'], job_id))

        # In-app notification for employer / recruiter
        execute_db("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (?, 'New Applicant Received! 📄', ?, 'application_status', 'employer_dashboard.html')
        """, (job['employer_user_id'], f"{student['full_name']} applied for '{job['title']}' (Ref: {ref_code}). Status: Pending review."))

        # In-app notification for student confirming pending status
        execute_db("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (?, 'Application Submitted (Pending Review) ⏳', ?, 'application_status', 'applications.html')
        """, (student['user_id'], f"Your application for '{job['title']}' (Ref: {ref_code}) has been received and is pending admin review."))

        # Fetch student skills
        skills_records = query_db("SELECT skill_name FROM student_skills WHERE student_id = ?", (student['id'],))
        skills_list = [s['skill_name'] for s in skills_records]

        # Admin Email Notification: Send all new job application notification emails to ADMIN_EMAIL (vinaybandi651@gmail.com)
        admin_email = Config.ADMIN_EMAIL
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        applied_at_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

        # Salary display
        salary_display = None
        if job.get('salary_min') and job.get('salary_max'):
            salary_display = f"₹{float(job['salary_min']):,.0f} - ₹{float(job['salary_max']):,.0f} / year CTC"
        elif job.get('pay_amount'):
            salary_display = f"₹{float(job['pay_amount']):,.0f} / {job.get('pay_frequency', 'year')}"

        # Generate single-use cryptographic tokens for Accept and Reject for the admin reviewer
        raw_accept, hash_accept = generate_secure_token()
        raw_reject, hash_reject = generate_secure_token()

        execute_db("""
            INSERT INTO action_tokens (application_id, token_hash, action, recipient_email, expires_at, is_used)
            VALUES (?, ?, 'accept', ?, ?, 0)
        """, (app_id, hash_accept, admin_email, expires_at))

        execute_db("""
            INSERT INTO action_tokens (application_id, token_hash, action, recipient_email, expires_at, is_used)
            VALUES (?, ?, 'reject', ?, ?, 0)
        """, (app_id, hash_reject, admin_email, expires_at))

        accept_url = f"{Config.APPLICATION_BASE_URL}/confirm-action.html?token={raw_accept}"
        reject_url = f"{Config.APPLICATION_BASE_URL}/confirm-action.html?token={raw_reject}"

        html_content, text_content = build_application_notification_email(
            job_title=job['title'],
            company_name=job['company_name'],
            location=job['location_address'],
            pay_amount=float(job['pay_amount']),
            pay_frequency=job['pay_frequency'],
            working_hours=f"{job.get('start_time') or '09:00'} - {job.get('end_time') or '18:00'}",
            date_needed=job.get('date_needed') or 'Immediate',
            applicant_name=student['full_name'],
            applicant_email=student['student_email'],
            applicant_phone=student.get('student_phone') or '',
            education=student.get('education') or 'Graduate',
            skills=skills_list,
            experience=student.get('fresher_status') or student.get('experience_level') or 'Fresher',
            cover_note=cover_note,
            reference_code=ref_code,
            applied_at=applied_at_str,
            accept_url=accept_url,
            reject_url=reject_url,
            degree=student.get('degree'),
            college=student.get('college_name') or student.get('institution'),
            graduation_year=student.get('graduation_year'),
            projects=student.get('projects'),
            work_arrangement=job.get('work_arrangement'),
            salary_display=salary_display,
            resume_url=resume_url
        )

        # Dispatch email to admin email (vinaybandi651@gmail.com)
        subject = f"New Job Application | {job['title']} | {student['full_name']} (Ref: {ref_code})"
        send_email([admin_email], subject, html_content, text_content, application_id=app_id)

        # Retrieve the email log ID for immediate preview / testing convenience
        latest_log = query_db("SELECT id FROM email_logs WHERE application_id = ? ORDER BY id DESC LIMIT 1", (app_id,), one=True)
        email_log_id = latest_log['id'] if latest_log else None

        return jsonify({
            'message': 'Application submitted successfully. Awaiting admin approval.',
            'application_id': app_id,
            'reference_code': ref_code,
            'status': 'pending',
            'email_log_id': email_log_id,
            'accept_url': accept_url,
            'reject_url': reject_url
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to submit application: {str(e)}'}), 500


@applications_bp.route('/<int:app_id>/email-preview', methods=['GET'])
def get_application_email_preview(app_id):
    """Returns the rendered HTML email dispatched to vinaybandi651@gmail.com for this application."""
    row = query_db("""
        SELECT id, recipient_email, subject, status, html_content, created_at
        FROM email_logs
        WHERE application_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (app_id,), one=True)
    if not row or not row['html_content']:
        return "<div style='font-family:sans-serif; padding:2rem; text-align:center;'><h3>No email content recorded for this application.</h3></div>", 404
    return row['html_content']


@applications_bp.route('/action/inspect', methods=['GET'])
def inspect_action_token():
    """
    Read-only endpoint to inspect action token details before confirmation.
    IMPORTANT: Opening the link DOES NOT alter application status (scanner protection).
    """
    raw_token = request.args.get('token', '').strip()
    if not raw_token:
        return jsonify({'valid': False, 'error': 'Action token is required'}), 400

    token_h = hash_token(raw_token)
    token_record = query_db("""
        SELECT at.*, a.status as current_status, a.reference_code, a.applied_at,
               j.title as job_title, j.location_address, ep.company_name,
               u.full_name as applicant_name, u.email as applicant_email
        FROM action_tokens at
        JOIN applications a ON at.application_id = a.id
        JOIN jobs j ON a.job_id = j.id
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u ON sp.user_id = u.id
        WHERE at.token_hash = ?
    """, (token_h,), one=True)

    if not token_record:
        return jsonify({'valid': False, 'error': 'Invalid or unrecognized action token.'}), 404

    # Check already used
    if token_record['is_used'] == 1:
        return jsonify({
            'valid': False,
            'already_used': True,
            'error': 'This action link has already been used.',
            'current_status': token_record['current_status']
        }), 400

    # Check expiration
    now = datetime.now(timezone.utc)
    exp_str = token_record['expires_at']
    try:
        exp_dt = datetime.fromisoformat(exp_str.replace('Z', '+00:00'))
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        if exp_dt < now:
            return jsonify({
                'valid': False,
                'expired': True,
                'error': 'This action link has expired (24-hour limit exceeded).'
            }), 400
    except Exception:
        pass

    # Check if application already decided by another recipient
    if token_record['current_status'] in ['accepted', 'rejected', 'completed']:
        return jsonify({
            'valid': False,
            'already_decided': True,
            'current_status': token_record['current_status'],
            'error': f'This application has already been finalized as {token_record["current_status"].upper()} by a reviewer.'
        }), 400

    return jsonify({
        'valid': True,
        'action': token_record['action'],
        'reference_code': token_record['reference_code'],
        'applicant_name': token_record['applicant_name'],
        'applicant_email': token_record['applicant_email'],
        'job_title': token_record['job_title'],
        'company_name': token_record['company_name'],
        'current_status': token_record['current_status'],
        'applied_at': token_record['applied_at']
    })


@applications_bp.route('/action/confirm', methods=['POST'])
def confirm_action_token():
    """
    Explicitly confirms the Accept or Reject action on an application.
    - Updates application status atomically in a transaction
    - Invalidates all tokens for this application to prevent conflicts
    - Logs audit record
    - Sends decision email to applicant
    """
    data = request.get_json() or {}
    raw_token = data.get('token', '').strip()
    notes = data.get('notes', '').strip()

    if not raw_token:
        return jsonify({'success': False, 'error': 'Token is required'}), 400

    token_h = hash_token(raw_token)
    token_record = query_db("""
        SELECT at.*, a.status as current_status, a.reference_code, a.student_id, a.job_id,
               j.title as job_title, ep.company_name,
               u.id as applicant_user_id, u.full_name as applicant_name, u.email as applicant_email
        FROM action_tokens at
        JOIN applications a ON at.application_id = a.id
        JOIN jobs j ON a.job_id = j.id
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u ON sp.user_id = u.id
        WHERE at.token_hash = ?
    """, (token_h,), one=True)

    if not token_record:
        return jsonify({'success': False, 'error': 'Invalid action token'}), 404

    if token_record['is_used'] == 1:
        return jsonify({'success': False, 'error': 'This action link has already been used.'}), 400

    now = datetime.now(timezone.utc)
    try:
        exp_dt = datetime.fromisoformat(token_record['expires_at'].replace('Z', '+00:00'))
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        if exp_dt < now:
            return jsonify({'success': False, 'error': 'This action link has expired.'}), 400
    except Exception:
        pass

    app_id = token_record['application_id']
    chosen_action = token_record['action'] # 'accept' or 'reject'
    new_status = 'accepted' if chosen_action == 'accept' else 'rejected'
    reviewer = token_record['recipient_email']

    # Execute in database transaction
    with get_db() as conn:
        cursor = conn.cursor()

        # Re-check application status inside transaction
        cursor.execute("SELECT status FROM applications WHERE id = ?", (app_id,))
        app_row = cursor.fetchone()
        if not app_row:
            return jsonify({'success': False, 'error': 'Application not found'}), 404

        current_status = app_row[0]
        if current_status in ['accepted', 'rejected', 'completed']:
            return jsonify({
                'success': False,
                'already_decided': True,
                'error': f'This application has already been decided as {current_status.upper()} by a reviewer.'
            }), 409

        # Update application status
        cursor.execute("""
            UPDATE applications
            SET status = ?, decided_at = CURRENT_TIMESTAMP, decided_by = ?, decision_note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, reviewer, notes, app_id))

        # Invalidate all action tokens for this application (prevents conflicting reviewer actions)
        cursor.execute("""
            UPDATE action_tokens
            SET is_used = 1, used_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
        """, (app_id,))

        # Record audit log
        client_ip = request.remote_addr or 'unknown'
        cursor.execute("""
            INSERT INTO application_audits (application_id, action, actor_email, actor_ip, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (app_id, new_status, reviewer, client_ip, notes))

        # Record interaction weight
        if new_status == 'accepted':
            cursor.execute("""
                INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight)
                VALUES (?, ?, 'ACCEPT_JOB', 7)
            """, (token_record['student_id'], token_record['job_id']))
        elif new_status == 'rejected':
            cursor.execute("""
                INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight)
                VALUES (?, ?, 'REJECT_JOB', -2)
            """, (token_record['student_id'], token_record['job_id']))

        # In-app notification for student
        status_label = new_status.title()
        msg = f"Your application for '{token_record['job_title']}' has been {status_label}."
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (?, ?, ?, 'application_status', 'applications.html')
        """, (token_record['applicant_user_id'], f"Application Decision: {status_label}", msg))

    # Send decision notification email to applicant
    dec_subj, dec_html, dec_text = build_applicant_decision_email(
        applicant_name=token_record['applicant_name'],
        job_title=token_record['job_title'],
        company_name=token_record['company_name'],
        decision=new_status
    )
    send_email([token_record['applicant_email']], dec_subj, dec_html, dec_text, application_id=app_id)

    return jsonify({
        'success': True,
        'message': f"Application has been successfully {new_status.upper()}.",
        'new_status': new_status,
        'application_id': app_id
    })


@applications_bp.route('/my', methods=['GET'])
@token_required
@role_required('student')
def get_my_applications():
    """Fetch applications submitted by current logged-in student."""
    user_id = request.current_user['user_id']
    student = query_db("SELECT id, latitude, longitude FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    apps = query_db("""
        SELECT a.id as application_id, a.job_id, a.cover_note, a.resume_url, a.status, a.reference_code,
               a.decided_at, a.decided_by, a.decision_note, a.status_notes, a.applied_at, a.updated_at,
               j.title as job_title, j.category, j.job_type, j.pay_amount, j.pay_frequency,
               j.salary_min, j.salary_max, j.work_arrangement, j.min_qualification, j.is_fresher_friendly,
               j.location_address, j.date_needed, j.start_time, j.end_time,
               ep.company_name, ep.user_id as employer_user_id, u.avatar_url as employer_avatar
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN users u ON ep.user_id = u.id
        WHERE a.student_id = ?
        ORDER BY a.applied_at DESC
    """, (student['id'],))

    return jsonify({'applications': apps})


@applications_bp.route('/job/<int:job_id>', methods=['GET'])
@token_required
@role_required('employer', 'admin')
def get_job_applicants(job_id):
    user_id = request.current_user['user_id']
    user_role = request.current_user.get('role')
    if user_role == 'admin':
        job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    else:
        emp = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
        if not emp:
            return jsonify({'error': 'Employer profile not found'}), 404
        job = query_db("SELECT * FROM jobs WHERE id = ? AND employer_id = ?", (job_id, emp['id']), one=True)
    if not job:
        return jsonify({'error': 'Job not found or access denied'}), 404

    applicants = query_db("""
        SELECT a.id as application_id, a.status, a.reference_code, a.cover_note, a.resume_url, a.status_notes, a.applied_at,
               sp.id as student_id, sp.user_id as student_user_id, sp.education, sp.institution,
               sp.degree, sp.specialization, sp.college_name, sp.graduation_year, sp.fresher_status,
               sp.projects, sp.certifications, sp.resume_url as profile_resume_url,
               sp.experience_level, sp.bio, sp.expected_salary, sp.salary_type,
               sp.latitude, sp.longitude, sp.address as student_address,
               u.full_name as student_name, u.email as student_email, u.phone as student_phone, u.avatar_url
        FROM applications a
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u ON sp.user_id = u.id
        WHERE a.job_id = ?
        ORDER BY a.applied_at DESC
    """, (job_id,))

    job_skills = [s['skill_name'] for s in query_db("SELECT skill_name FROM job_skills WHERE job_id = ?", (job_id,))]
    
    results = []
    for app in applicants:
        a_dict = dict(app)
        student_skills = [s['skill_name'] for s in query_db("SELECT skill_name FROM student_skills WHERE student_id = ?", (app['student_id'],))]
        a_dict['skills'] = student_skills

        # Resume URL fallback
        if not a_dict.get('resume_url') and a_dict.get('profile_resume_url'):
            a_dict['resume_url'] = a_dict['profile_resume_url']

        if app['latitude'] and app['longitude'] and job['latitude'] and job['longitude']:
            dist = haversine_distance(app['latitude'], app['longitude'], job['latitude'], job['longitude'])
            a_dict['distance_km'] = dist
            a_dict['formatted_distance'] = format_distance(dist)
        else:
            a_dict['distance_km'] = None
            a_dict['formatted_distance'] = "Distance N/A"

        overlap = set(s.lower() for s in student_skills).intersection(set(s.lower() for s in job_skills))
        a_dict['matched_skills_count'] = len(overlap)
        a_dict['total_job_skills'] = len(job_skills)
        a_dict['matched_skills'] = list(overlap)
        results.append(a_dict)

    return jsonify({'job': dict(job), 'applicants': results})


@applications_bp.route('/<int:app_id>/status', methods=['PATCH'])
@token_required
@role_required('employer', 'admin')
def update_application_status(app_id):
    user_id = request.current_user['user_id']
    user_role = request.current_user.get('role')
    user_email = request.current_user.get('email', 'admin')

    app = query_db("""
        SELECT a.*, j.employer_id, j.title as job_title, ep.company_name,
               sp.user_id as student_user_id, u.full_name as applicant_name, u.email as applicant_email
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u ON sp.user_id = u.id
        WHERE a.id = ?
    """, (app_id,), one=True)

    if not app:
        return jsonify({'error': 'Application not found'}), 404

    if user_role != 'admin':
        emp = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
        if not emp or app['employer_id'] != emp['id']:
            return jsonify({'error': 'Unauthorized to manage this application'}), 403

    data = request.get_json() or {}
    new_status = data.get('status')
    status_notes = data.get('status_notes') or data.get('notes')
    if new_status not in VALID_STATUSES:
        return jsonify({'error': f'Invalid status. Allowed: {", ".join(VALID_STATUSES)}'}), 400

    execute_db("""
        UPDATE applications
        SET status = ?,
            status_notes = COALESCE(?, status_notes),
            decided_at = CASE WHEN ? IN ('accepted', 'rejected') THEN CURRENT_TIMESTAMP ELSE decided_at END,
            decided_by = CASE WHEN ? IN ('accepted', 'rejected') THEN ? ELSE decided_by END,
            decision_note = CASE WHEN ? IN ('accepted', 'rejected') THEN ? ELSE decision_note END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, status_notes, new_status, new_status, user_email, new_status, status_notes, app_id))

    if new_status in ['accepted', 'rejected', 'completed']:
        execute_db("UPDATE action_tokens SET is_used = 1, used_at = CURRENT_TIMESTAMP WHERE application_id = ?", (app_id,))

    if new_status == 'accepted':
        execute_db("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'ACCEPT_JOB', 7)", (app['student_id'], app['job_id']))
    elif new_status == 'completed':
        execute_db("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'COMPLETE_JOB', 10)", (app['student_id'], app['job_id']))
    elif new_status == 'rejected':
        execute_db("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'REJECT_JOB', -2)", (app['student_id'], app['job_id']))

    # In-app notification
    status_label = new_status.replace('_', ' ').title()
    note_suffix = f" Note: {status_notes}" if status_notes else ""
    execute_db("""
        INSERT INTO notifications (user_id, title, message, type, link)
        VALUES (?, ?, ?, 'application_status', 'applications.html')
    """, (
        app['student_user_id'],
        f"Application Update: {status_label}",
        f"Your application for '{app['job_title']}' has been updated to '{status_label}'.{note_suffix}"
    ))

    # Also dispatch applicant email notification if accepted or rejected
    if new_status in ['accepted', 'rejected']:
        dec_subj, dec_html, dec_text = build_applicant_decision_email(
            applicant_name=app['applicant_name'],
            job_title=app['job_title'],
            company_name=app['company_name'],
            decision=new_status
        )
        send_email([app['applicant_email']], dec_subj, dec_html, dec_text, application_id=app_id)

    return jsonify({'message': f'Status updated to {status_label}', 'new_status': new_status})


@applications_bp.route('/<int:app_id>', methods=['DELETE'])
@token_required
@role_required('student')
def withdraw_application(app_id):
    user_id = request.current_user['user_id']
    student = query_db("SELECT id FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    app = query_db("""
        SELECT a.*, j.title as job_title
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ? AND a.student_id = ?
    """, (app_id, student['id']), one=True)

    if not app:
        return jsonify({'error': 'Application not found or unauthorized'}), 404

    if app['status'] in ('accepted', 'completed'):
        return jsonify({'error': f'Cannot withdraw an application that is already {app["status"]}'}), 400

    execute_db("DELETE FROM applications WHERE id = ?", (app_id,))

    execute_db(
        "DELETE FROM job_interactions WHERE student_id = ? AND job_id = ? AND interaction_type = 'APPLY_JOB'",
        (student['id'], app['job_id'])
    )

    return jsonify({'message': f"Application for '{app['job_title']}' has been withdrawn successfully"})
