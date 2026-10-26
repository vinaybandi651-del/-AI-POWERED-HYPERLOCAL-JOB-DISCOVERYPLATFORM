from flask import Blueprint, request, jsonify
import os
import re
from datetime import datetime, timezone, timedelta
from database.db import query_db, execute_db, get_db
from utils.security import token_required, role_required
from config import Config, BASE_DIR, PROJECT_ROOT
from utils.email_service import (
    is_smtp_configured,
    send_email,
    generate_secure_token,
    build_application_notification_email
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/overview', methods=['GET'])
@admin_bp.route('/stats', methods=['GET'])
@token_required
@role_required('admin')
def get_admin_overview():
    total_users = query_db("SELECT COUNT(*) as count FROM users", one=True)['count']
    total_students = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'student'", one=True)['count']
    total_employers = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'employer'", one=True)['count']
    total_jobs = query_db("SELECT COUNT(*) as count FROM jobs", one=True)['count']
    active_jobs = query_db("SELECT COUNT(*) as count FROM jobs WHERE status = 'active'", one=True)['count']
    completed_jobs = query_db("SELECT COUNT(*) as count FROM jobs WHERE status = 'completed'", one=True)['count']
    total_applications = query_db("SELECT COUNT(*) as count FROM applications", one=True)['count']
    accepted_matches = query_db("SELECT COUNT(*) as count FROM applications WHERE status IN ('accepted', 'completed')", one=True)['count']
    total_interactions = query_db("SELECT COUNT(*) as count FROM job_interactions", one=True)['count']

    match_rate = round((accepted_matches / max(1, total_applications)) * 100, 1)

    return jsonify({
        'total_users': total_users,
        'total_students': total_students,
        'total_employers': total_employers,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'total_applications': total_applications,
        'accepted_matches': accepted_matches,
        'total_interactions': total_interactions,
        'match_success_rate': match_rate
    })

@admin_bp.route('/analytics', methods=['GET'])
@token_required
@role_required('admin')
def get_admin_analytics():
    # 1. Job categories distribution
    categories = query_db("""
        SELECT category, COUNT(*) as count
        FROM jobs
        GROUP BY category
        ORDER BY count DESC
    """)

    # 2. Application funnel
    funnel = query_db("""
        SELECT status, COUNT(*) as count
        FROM applications
        GROUP BY status
    """)

    # 3. User distribution
    roles = query_db("""
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
    """)

    # 4. Top skills in demand
    top_skills = query_db("""
        SELECT skill_name, COUNT(*) as count
        FROM job_skills
        GROUP BY skill_name
        ORDER BY count DESC
        LIMIT 8
    """)

    # 5. Interaction breakdown
    interactions = query_db("""
        SELECT interaction_type, COUNT(*) as count
        FROM job_interactions
        GROUP BY interaction_type
        ORDER BY count DESC
    """)

    return jsonify({
        'categories': categories,
        'application_funnel': funnel,
        'user_distribution': roles,
        'top_skills': top_skills,
        'interactions': interactions
    })

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def list_users():
    users = query_db("""
        SELECT u.id, u.email, u.role, u.full_name, u.phone, u.avatar_url, u.created_at,
               COALESCE(sp.id, ep.id) as profile_id,
               COALESCE(sp.institution, ep.company_name) as organization,
               COALESCE(sp.education, ep.business_type) as details
        FROM users u
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        LEFT JOIN employer_profiles ep ON u.id = ep.user_id
        ORDER BY u.created_at DESC
    """)
    return jsonify({'users': users})

@admin_bp.route('/jobs', methods=['GET'])
@token_required
@role_required('admin')
def list_jobs_moderation():
    jobs = query_db("""
        SELECT j.*, ep.company_name, u.email as employer_email,
               (SELECT COUNT(*) FROM applications WHERE job_id = j.id) as applicant_count
        FROM jobs j
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN users u ON ep.user_id = u.id
        ORDER BY j.created_at DESC
    """)
    return jsonify({'jobs': jobs})

@admin_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_job_admin(job_id):
    execute_db("DELETE FROM jobs WHERE id = ?", (job_id,))
    return jsonify({'message': 'Job removed successfully'})

@admin_bp.route('/weights', methods=['GET'])
@token_required
@role_required('admin')
def get_weights():
    w = query_db("SELECT * FROM recommendation_weights ORDER BY id DESC LIMIT 1", one=True)
    return jsonify({'weights': w})

@admin_bp.route('/weights', methods=['PUT', 'POST'])
@token_required
@role_required('admin')
def update_weights():
    data = request.get_json() or {}
    cw = float(data.get('content_weight', 0.40))
    lw = float(data.get('location_weight', 0.25))
    aw = float(data.get('availability_weight', 0.15))
    cfw = float(data.get('collaborative_weight', 0.10))
    sw = float(data.get('salary_weight', 0.10))

    total = cw + lw + aw + cfw + sw
    if abs(total - 1.0) > 0.05:
        # Normalize
        cw, lw, aw, cfw, sw = cw/total, lw/total, aw/total, cfw/total, sw/total

    execute_db("""
        UPDATE recommendation_weights SET
            content_weight = ?,
            location_weight = ?,
            availability_weight = ?,
            collaborative_weight = ?,
            salary_weight = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = (SELECT id FROM recommendation_weights ORDER BY id DESC LIMIT 1)
    """, (cw, lw, aw, cfw, sw))

    return jsonify({'message': 'Recommendation engine weights updated successfully'})


@admin_bp.route('/applications', methods=['GET'])
@token_required
@role_required('admin')
def list_applications_admin():
    apps = query_db("""
        SELECT a.id as application_id, a.job_id, a.student_id, a.status, a.reference_code,
               a.cover_note, a.resume_url, a.status_notes, a.applied_at, a.decided_at, a.decided_by,
               j.title as job_title, ep.company_name,
               u_s.full_name as student_name, u_s.email as student_email,
               sp.degree, sp.college_name, sp.graduation_year,
               sp.resume_url as profile_resume_url
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u_s ON sp.user_id = u_s.id
        ORDER BY a.applied_at DESC
    """)
    return jsonify({'applications': apps})
 
 
@admin_bp.route('/email-config', methods=['GET'])
@token_required
@role_required('admin')
def get_email_config():
    pwd = (Config.SMTP_APP_PASSWORD or '').strip()
    is_placeholder = (not pwd) or pwd in ('your_google_app_password', 'your_16_character_google_app_password')
    masked = 'Not configured'
    if not is_placeholder:
        masked = pwd[:3] + '••••••••' + pwd[-3:] if len(pwd) >= 6 else '••••••••'

    return jsonify({
        'admin_email': Config.ADMIN_EMAIL,
        'smtp_host': Config.SMTP_HOST,
        'smtp_port': Config.SMTP_PORT,
        'smtp_configured': is_smtp_configured(),
        'has_app_password': not is_placeholder,
        'masked_password': masked
    })


@admin_bp.route('/update-smtp-password', methods=['POST'])
@token_required
@role_required('admin')
def update_smtp_password():
    data = request.get_json() or {}
    raw_pwd = data.get('password', '').strip()
    pwd = raw_pwd.replace(' ', '')
    if not pwd:
        return jsonify({'error': 'Password cannot be empty'}), 400

    def update_file(path):
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            c = f.read()
        pat = r'^SMTP_APP_PASSWORD=.*$'
        if re.search(pat, c, flags=re.MULTILINE):
            c = re.sub(pat, f'SMTP_APP_PASSWORD={pwd}', c, flags=re.MULTILINE)
        else:
            c = c.rstrip() + f'\nSMTP_APP_PASSWORD={pwd}\n'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)

    update_file(os.path.join(PROJECT_ROOT, '.env'))
    update_file(os.path.join(BASE_DIR, '.env'))
    os.environ['SMTP_APP_PASSWORD'] = pwd
    os.environ['SMTP_PASSWORD'] = pwd
    Config.SMTP_APP_PASSWORD = pwd
    Config.SMTP_PASSWORD = pwd

    return jsonify({
        'success': True,
        'message': f'Google App Password successfully saved and applied! ({len(pwd)} characters)'
    })


@admin_bp.route('/test-email', methods=['POST'])
@token_required
@role_required('admin')
def test_email_endpoint():
    data = request.get_json() or {}
    temp_pwd = (data.get('password') or '').strip().replace(' ', '')

    if temp_pwd:
        os.environ['SMTP_APP_PASSWORD'] = temp_pwd
        os.environ['SMTP_PASSWORD'] = temp_pwd
        Config.SMTP_APP_PASSWORD = temp_pwd
        Config.SMTP_PASSWORD = temp_pwd

    if not is_smtp_configured():
        return jsonify({
            'success': False,
            'error': 'SMTP is not configured. Please enter your 16-character Google App Password first.'
        }), 400

    subject = "✅ Live Test Notification | GradMatch AI Job Portal"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
        <div style="background: linear-gradient(135deg, #1e40af, #1e3a8a); padding: 20px; border-radius: 8px; color: #ffffff; text-align: center;">
            <h2 style="margin: 0; font-size: 22px;">🎓 GradMatch AI Notification Test</h2>
            <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.9;">Email Delivery Service Verification</p>
        </div>
        <div style="padding: 20px 0;">
            <p style="font-size: 15px; color: #1e293b;">Hello <strong>Admin</strong>,</p>
            <p style="font-size: 14px; color: #475569; line-height: 1.6;">
                This confirms that your <strong>Gmail SMTP integration is working 100% correctly!</strong>
            </p>
            <p style="font-size: 14px; color: #475569; line-height: 1.6;">
                Whenever a student applies for a job, you will immediately receive the application with <strong>Accept</strong> and <strong>Reject</strong> buttons right here at <code>{Config.ADMIN_EMAIL}</code>.
            </p>
            <div style="margin: 24px 0; text-align: center;">
                <a href="{Config.APPLICATION_BASE_URL}/admin.html" style="background: #1e40af; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 14px;">Open Admin Dashboard</a>
            </div>
        </div>
        <div style="border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: 12px; color: #94a3b8; text-align: center;">
            Sent to {Config.ADMIN_EMAIL} via {Config.SMTP_HOST}:{Config.SMTP_PORT}
        </div>
    </div>
    """
    text_content = f"GradMatch AI Email Test - Successfully connected to {Config.ADMIN_EMAIL}"

    success, msg = send_email([Config.ADMIN_EMAIL], subject, html_content, text_content)
    if success:
        return jsonify({
            'success': True,
            'message': f'Test email delivered successfully to {Config.ADMIN_EMAIL}! Check your inbox or spam tab.'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to send email: {msg}'
        }), 500


@admin_bp.route('/email-logs', methods=['GET'])
@token_required
@role_required('admin')
def get_email_logs():
    logs = query_db("""
        SELECT id, recipient_email, subject, status, error_message, application_id, created_at,
               (html_content IS NOT NULL AND length(html_content) > 0) as has_html
        FROM email_logs
        ORDER BY id DESC
        LIMIT 25
    """)
    return jsonify({'logs': logs})


@admin_bp.route('/emails/<int:log_id>/view', methods=['GET'])
def view_email_html(log_id):
    """Render full HTML email for browser viewing / simulator."""
    row = query_db("SELECT html_content, subject FROM email_logs WHERE id = ?", (log_id,), one=True)
    if not row or not row['html_content']:
        return "<div style='font-family:sans-serif; padding:2rem; text-align:center;'><h3>Email content not found</h3></div>", 404
    return row['html_content']


@admin_bp.route('/emails/latest/view', methods=['GET'])
def view_latest_email_html():
    """Render the latest dispatched HTML email."""
    row = query_db("SELECT html_content, subject FROM email_logs WHERE html_content IS NOT NULL ORDER BY id DESC LIMIT 1", one=True)
    if not row or not row['html_content']:
        return "<div style='font-family:sans-serif; padding:2rem; text-align:center;'><h3>No email recorded yet</h3></div>", 404
    return row['html_content']


@admin_bp.route('/resend-application-email/<int:app_id>', methods=['POST'])
@token_required
@role_required('admin')
def resend_application_email(app_id):
    app = query_db("SELECT * FROM applications WHERE id = ?", (app_id,), one=True)
    if not app:
        return jsonify({'error': 'Application not found'}), 404

    job = query_db("""
        SELECT j.*, ep.user_id as employer_user_id, ep.company_name
        FROM jobs j
        JOIN employer_profiles ep ON j.employer_id = ep.id
        WHERE j.id = ?
    """, (app['job_id'],), one=True)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    student = query_db("""
        SELECT sp.*, u.full_name, u.email as student_email, u.phone as student_phone
        FROM student_profiles sp
        JOIN users u ON sp.user_id = u.id
        WHERE sp.id = ?
    """, (app['student_id'],), one=True)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    skills_records = query_db("SELECT skill_name FROM student_skills WHERE student_id = ?", (student['id'],))
    skills_list = [s['skill_name'] for s in skills_records]

    admin_email = Config.ADMIN_EMAIL
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    applied_at_str = app.get('applied_at') or datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

    salary_display = None
    if job.get('salary_min') and job.get('salary_max'):
        salary_display = f"₹{float(job['salary_min']):,.0f} - ₹{float(job['salary_max']):,.0f} / year CTC"
    elif job.get('pay_amount'):
        salary_display = f"₹{float(job['pay_amount']):,.0f} / {job.get('pay_frequency', 'year')}"

    # Generate single-use cryptographic tokens
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
        cover_note=app.get('cover_note') or '',
        reference_code=app.get('reference_code') or f"APP-2026-{app_id}",
        applied_at=applied_at_str,
        accept_url=accept_url,
        reject_url=reject_url,
        degree=student.get('degree'),
        college=student.get('college_name') or student.get('institution'),
        graduation_year=student.get('graduation_year'),
        projects=student.get('projects'),
        work_arrangement=job.get('work_arrangement'),
        salary_display=salary_display,
        resume_url=app.get('resume_url') or student.get('resume_url')
    )

    subject = f"New Job Application | {job['title']} | {student['full_name']} (Ref: {app.get('reference_code')})"
    success, msg = send_email([admin_email], subject, html_content, text_content, application_id=app_id)

    if success:
        return jsonify({
            'success': True,
            'message': f'Application notification email successfully sent to {admin_email}!'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to dispatch email: {msg}'
        }), 400
