from flask import Blueprint, request, jsonify
from database.db import query_db, execute_db
from utils.security import token_required, role_required

employers_bp = Blueprint('employers', __name__)

@employers_bp.route('/profile', methods=['GET'])
@token_required
@role_required('employer')
def get_employer_profile():
    user_id = request.current_user['user_id']
    profile = query_db("""
        SELECT ep.*, u.full_name, u.email, u.phone, u.avatar_url
        FROM employer_profiles ep
        JOIN users u ON ep.user_id = u.id
        WHERE ep.user_id = ?
    """, (user_id,), one=True)

    if not profile:
        return jsonify({'error': 'Employer profile not found'}), 404

    return jsonify({'profile': profile})

@employers_bp.route('/profile', methods=['PUT'])
@token_required
@role_required('employer')
def update_employer_profile():
    user_id = request.current_user['user_id']
    data = request.get_json() or {}

    profile = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
    if not profile:
        return jsonify({'error': 'Employer profile not found'}), 404

    if 'full_name' in data or 'phone' in data:
        execute_db("""
            UPDATE users SET
                full_name = COALESCE(?, full_name),
                phone = COALESCE(?, phone)
            WHERE id = ?
        """, (data.get('full_name'), data.get('phone'), user_id))

    execute_db("""
        UPDATE employer_profiles SET
            company_name = COALESCE(?, company_name),
            business_type = COALESCE(?, business_type),
            description = COALESCE(?, description),
            website = COALESCE(?, website),
            address = COALESCE(?, address),
            latitude = COALESCE(?, latitude),
            longitude = COALESCE(?, longitude)
        WHERE id = ?
    """, (
        data.get('company_name'), data.get('business_type'), data.get('description'),
        data.get('website'), data.get('address'), data.get('latitude'),
        data.get('longitude'), profile['id']
    ))

    return jsonify({'message': 'Company profile updated successfully'})

@employers_bp.route('/dashboard_stats', methods=['GET'])
@token_required
@role_required('employer')
def get_dashboard_stats():
    user_id = request.current_user['user_id']
    profile = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
    if not profile:
        return jsonify({'error': 'Employer profile not found'}), 404

    emp_id = profile['id']

    total_jobs = query_db("SELECT COUNT(*) as count FROM jobs WHERE employer_id = ?", (emp_id,), one=True)['count']
    active_jobs = query_db("SELECT COUNT(*) as count FROM jobs WHERE employer_id = ? AND status = 'active'", (emp_id,), one=True)['count']
    total_applicants = query_db("""
        SELECT COUNT(a.id) as count
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.employer_id = ?
    """, (emp_id,), one=True)['count']
    shortlisted = query_db("""
        SELECT COUNT(a.id) as count
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.employer_id = ? AND a.status IN ('shortlisted', 'accepted')
    """, (emp_id,), one=True)['count']

    return jsonify({
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applicants': total_applicants,
        'shortlisted_applicants': shortlisted
    })
