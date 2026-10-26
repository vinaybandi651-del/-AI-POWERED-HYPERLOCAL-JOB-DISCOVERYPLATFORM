from flask import Blueprint, request, jsonify
import json
import re
import secrets
from datetime import datetime, timezone, timedelta
from database.db import query_db, execute_db, get_db
from utils.security import hash_password, verify_password, create_access_token, token_required
from utils.email_service import (
    send_email,
    generate_secure_token,
    hash_token,
    build_verification_email
)
from config import Config

auth_bp = Blueprint('auth', __name__)

NAME_PART_REGEX = re.compile(r"^[A-Za-z0-9À-ÖØ-öø-ÿ\s'-]+$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_name_part(part: str, label: str) -> tuple[bool, str]:
    """Validates an individual first or last name part."""
    if not part or not part.strip():
        return False, f"{label} is required"
    trimmed = part.strip()
    if len(trimmed) < 2 or len(trimmed) > 50:
        return False, f"{label} must be between 2 and 50 characters"
    if not NAME_PART_REGEX.match(trimmed):
        return False, f"{label} contains invalid characters. Only letters, numbers, spaces, hyphens, and apostrophes are allowed"
    # Reject if it has no letters
    if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", trimmed):
        return False, f"{label} must contain letters"
    return True, trimmed

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate reasonable password strength: min 8 chars, at least 1 letter, at least 1 number."""
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, ""


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password')
    role = data.get('role', 'student').strip().lower()
    phone = data.get('phone', '').strip()

    # 1. Flexible & Robust Name Extraction & Normalization
    first_name_input = data.get('first_name', '').strip()
    last_name_input = data.get('last_name', '').strip()
    full_name_input = data.get('full_name', '').strip()

    if first_name_input and last_name_input:
        first_name = " ".join(first_name_input.split())
        last_name = " ".join(last_name_input.split())
        full_name = f"{first_name} {last_name}"
    elif first_name_input and not last_name_input:
        first_name = " ".join(first_name_input.split())
        last_name = ""
        full_name = first_name
    elif full_name_input:
        cleaned_full = " ".join(full_name_input.split())
        parts = cleaned_full.split(None, 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
        full_name = cleaned_full
    else:
        return jsonify({
            'success': False,
            'message': 'First name is required',
            'error': 'First name is required'
        }), 400

    # Ensure name length and validity
    if len(first_name) < 1 or len(full_name) > 100:
        return jsonify({
            'success': False,
            'message': 'Please provide a valid name',
            'error': 'Please provide a valid name'
        }), 400

    # 2. Email Validation
    if not email:
        return jsonify({'success': False, 'message': 'Email address is required', 'error': 'Email address is required'}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({'success': False, 'message': 'Invalid email address format', 'error': 'Invalid email address format'}), 400

    # Prevent duplicate accounts
    existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
    if existing:
        return jsonify({'success': False, 'message': 'An account with this email already exists. Please sign in.', 'error': 'An account with this email already exists'}), 409

    # 3. Role Validation
    if role not in ['student', 'employer']:
        return jsonify({'success': False, 'message': 'Invalid role. Must be student or employer', 'error': 'Invalid role. Must be student or employer'}), 400

    # 4. Password Strength & Confirmation
    ok_pwd, pwd_err = validate_password_strength(password)
    if not ok_pwd:
        return jsonify({'success': False, 'message': pwd_err, 'error': pwd_err}), 400

    if confirm_password is not None and confirm_password != password:
        return jsonify({'success': False, 'message': 'Passwords do not match', 'error': 'Passwords do not match'}), 400

    pwd_hash = hash_password(password)
    # No default or automatically generated avatars; empty until user uploads their own photo
    avatar = None

    try:
        # If SMTP is configured, require email verification; otherwise, auto-verify so any user can register & login immediately
        from utils.email_service import is_smtp_configured
        smtp_ready = is_smtp_configured()
        initial_verified = 0 if smtp_ready else 1

        user_id = execute_db("""
            INSERT INTO users (email, password_hash, role, full_name, first_name, last_name, phone, avatar_url, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, pwd_hash, role, full_name, first_name, last_name, phone, avatar, initial_verified))

        if role == 'student':
            degree = data.get('degree', 'B.Tech')
            spec = data.get('specialization', '')
            college = data.get('college_name') or data.get('institution', 'Hyderabad University')
            grad_year = data.get('graduation_year', 2026)
            fresher_stat = data.get('fresher_status') or data.get('experience_level', 'Fresher')
            education_text = data.get('education') or (f"{degree} in {spec}".strip() if spec else degree)

            execute_db("""
                INSERT INTO student_profiles (
                    user_id, education, institution, experience_level, bio,
                    preferred_categories, preferred_job_type, expected_salary, salary_type,
                    max_distance_km, latitude, longitude, address,
                    available_days, available_time_start, available_time_end, profile_completed,
                    degree, specialization, college_name, graduation_year, fresher_status,
                    preferred_roles, willingness_to_relocate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                education_text,
                college,
                fresher_stat,
                data.get('bio', 'Fresh graduate seeking entry-level career opportunities.'),
                json.dumps(data.get('preferred_categories', ['Tech & IT', 'Consulting'])),
                data.get('preferred_job_type', 'Full-time'),
                float(data.get('expected_salary', 350000)),
                data.get('salary_type', 'year'),
                float(data.get('max_distance_km', 15.0)),
                float(data.get('latitude', 17.4483)),
                float(data.get('longitude', 78.3915)),
                data.get('address', 'Madhapur, Hyderabad'),
                json.dumps(data.get('available_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])),
                data.get('available_time_start', '09:00'),
                data.get('available_time_end', '18:00'),
                degree,
                spec,
                college,
                int(grad_year) if grad_year else 2026,
                fresher_stat,
                json.dumps(data.get('preferred_roles', ['Software Engineer', 'Graduate Trainee'])),
                int(data.get('willingness_to_relocate', 1))
            ))
            skills = data.get('skills', ['Problem Solving', 'Communication'])
            s_profile = query_db("SELECT id FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
            if s_profile:
                for sk in skills:
                    execute_db("INSERT INTO student_skills (student_id, skill_name) VALUES (?, ?)", (s_profile['id'], sk))
        
        elif role == 'employer':
            execute_db("""
                INSERT INTO employer_profiles (user_id, company_name, business_type, description, address, latitude, longitude, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                user_id,
                data.get('company_name', full_name),
                data.get('business_type', 'Local Business'),
                data.get('description', 'Local business hiring student talent.'),
                data.get('address', 'Hitec City, Hyderabad'),
                float(data.get('latitude', 17.4504)),
                float(data.get('longitude', 78.3808))
            ))

        # Generate single-use verification token and 6-digit OTP
        raw_token, token_hash = generate_secure_token()
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        execute_db("""
            INSERT INTO email_verifications (user_id, token_hash, otp_code, expires_at, is_used)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, token_hash, otp_code, expires_at))

        # Dispatch verification email
        verify_url = f"{Config.APPLICATION_BASE_URL}/verify_email.html?token={raw_token}&email={email}"
        v_subj, v_html, v_text = build_verification_email(full_name, verify_url, otp_code)
        email_sent, email_msg = send_email(email, v_subj, v_html, v_text)

        token = create_access_token(user_id, email, role, full_name)

        return jsonify({
            'success': True,
            'message': 'Registration successful! Welcome to HyperLocal Job Match.',
            'token': token,
            'email_verification_required': smtp_ready,
            'email': email,
            'verification_token': raw_token,
            'otp_code': otp_code,
            'user': {
                'id': user_id,
                'email': email,
                'role': role,
                'full_name': full_name,
                'avatar_url': avatar
            }
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to create account: {str(e)}', 'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Mandatory Registration & Secure Login.
    Requires an existing, verified account. Never auto-creates accounts.
    Enforces account lockout after 5 consecutive failed attempts.
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required', 'error': 'Email and password are required'}), 400

    user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
    
    # 1. Mandatory registration: reject unregistered users
    if not user:
        return jsonify({
            'success': False,
            'message': 'Account not found. Please register first.',
            'error': 'Account not found. Please register first.'
        }), 401

    # 2. Check brute-force lockout
    now = datetime.now(timezone.utc)
    locked_until_str = user.get('locked_until')
    if locked_until_str:
        try:
            # Handle ISO string or SQLite timestamp
            locked_dt = datetime.fromisoformat(locked_until_str.replace('Z', '+00:00'))
            if locked_dt.tzinfo is None:
                locked_dt = locked_dt.replace(tzinfo=timezone.utc)
            if locked_dt > now:
                remaining_mins = max(1, int((locked_dt - now).total_seconds() / 60))
                return jsonify({
                    'success': False,
                    'message': f'Account temporarily locked due to too many failed login attempts. Please try again in {remaining_mins} minutes.',
                    'error': f'Account temporarily locked. Please try again in {remaining_mins} minutes.'
                }), 403
        except Exception:
            pass

    # 3. Verify password hash
    if not verify_password(password, user['password_hash']):
        # Increment failed attempts
        failed = (user.get('failed_login_attempts') or 0) + 1
        if failed >= 5:
            lockout_time = (now + timedelta(minutes=15)).isoformat()
            execute_db("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?", (failed, lockout_time, user['id']))
            return jsonify({
                'success': False,
                'message': 'Too many failed login attempts. Account temporarily locked for 15 minutes.',
                'error': 'Too many failed login attempts. Account temporarily locked for 15 minutes.'
            }), 403
        else:
            execute_db("UPDATE users SET failed_login_attempts = ? WHERE id = ?", (failed, user['id']))
            return jsonify({
                'success': False,
                'message': 'Invalid email or password.',
                'error': 'Invalid email or password.'
            }), 401

    # Reset failed attempts upon successful password match
    execute_db("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (user['id'],))

    # 4. Check email verification status: If SMTP is configured and user is unverified, require verification
    from utils.email_service import is_smtp_configured
    is_verified = user.get('is_verified')
    if is_smtp_configured() and is_verified is not None and int(is_verified) == 0:
        return jsonify({
            'success': False,
            'message': 'Please verify your email address before logging in.',
            'error': 'Please verify your email address before logging in.',
            'email_unverified': True,
            'email': user['email']
        }), 403

    # Fetch extra profile ID based on role
    profile_id = None
    if user['role'] == 'student':
        prof = query_db("SELECT id FROM student_profiles WHERE user_id = ?", (user['id'],), one=True)
        if prof:
            profile_id = prof['id']
    elif user['role'] == 'employer':
        prof = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user['id'],), one=True)
        if prof:
            profile_id = prof['id']

    token = create_access_token(user['id'], user['email'], user['role'], user['full_name'])
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'full_name': user['full_name'],
            'phone': user.get('phone', ''),
            'avatar_url': user.get('avatar_url', ''),
            'profile_id': profile_id
        }
    })


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify user account using either a 6-digit OTP code or verification token link.
    """
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    otp = data.get('otp', '').strip()
    email = data.get('email', '').strip().lower()

    if not token and not (otp and email):
        return jsonify({'success': False, 'message': 'Verification token or OTP with email is required', 'error': 'Verification token or OTP with email is required'}), 400

    record = None
    now = datetime.now(timezone.utc)

    if token:
        token_h = hash_token(token)
        record = query_db("""
            SELECT ev.*, u.email as user_email
            FROM email_verifications ev
            JOIN users u ON ev.user_id = u.id
            WHERE ev.token_hash = ? AND ev.is_used = 0
            ORDER BY ev.id DESC LIMIT 1
        """, (token_h,), one=True)
    elif otp and email:
        user = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if not user:
            return jsonify({'success': False, 'message': 'Account not found', 'error': 'Account not found'}), 404
        record = query_db("""
            SELECT ev.*, u.email as user_email
            FROM email_verifications ev
            JOIN users u ON ev.user_id = u.id
            WHERE ev.user_id = ? AND ev.otp_code = ? AND ev.is_used = 0
            ORDER BY ev.id DESC LIMIT 1
        """, (user['id'], otp), one=True)

    if not record:
        return jsonify({
            'success': False,
            'message': 'Invalid or expired verification code / link',
            'error': 'Invalid or expired verification code / link'
        }), 400

    # Check expiration
    expires_at_str = record['expires_at']
    try:
        exp_dt = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        if exp_dt < now:
            return jsonify({
                'success': False,
                'message': 'Verification link has expired. Please request a new verification code.',
                'error': 'Verification link has expired.'
            }), 400
    except Exception:
        pass

    # Mark as verified and mark record used
    execute_db("UPDATE email_verifications SET is_used = 1 WHERE id = ?", (record['id'],))
    execute_db("UPDATE users SET is_verified = 1 WHERE id = ?", (record['user_id'],))

    return jsonify({
        'success': True,
        'message': 'Email verified successfully! You may now sign in to your account.'
    })


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification OTP and link for unverified account."""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'success': False, 'message': 'Email address is required', 'error': 'Email address is required'}), 400

    user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
    if not user:
        return jsonify({'success': False, 'message': 'Account not found with this email', 'error': 'Account not found'}), 404

    if user.get('is_verified') == 1:
        return jsonify({'success': True, 'message': 'Account is already verified. Please proceed to sign in.'})

    raw_token, token_hash = generate_secure_token()
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    execute_db("""
        INSERT INTO email_verifications (user_id, token_hash, otp_code, expires_at, is_used)
        VALUES (?, ?, ?, ?, 0)
    """, (user['id'], token_hash, otp_code, expires_at))

    verify_url = f"{Config.APPLICATION_BASE_URL}/verify_email.html?token={raw_token}&email={email}"
    v_subj, v_html, v_text = build_verification_email(user['full_name'], verify_url, otp_code)
    send_email(email, v_subj, v_html, v_text)

    return jsonify({
        'success': True,
        'message': 'A new verification code has been sent to your email address.',
        'verification_token': raw_token,
        'otp_code': otp_code
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint."""
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    user = query_db("SELECT id, email, role, full_name, first_name, last_name, phone, avatar_url, is_verified, created_at FROM users WHERE id = ?", (request.current_user['user_id'],), one=True)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user})
