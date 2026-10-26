from flask import Blueprint, request, jsonify
from database.db import query_db, execute_db, get_db
from utils.security import token_required, role_required
from utils.geo import haversine_distance, format_distance

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('', methods=['GET'])
def get_jobs():
    """
    Search and filter jobs.
    Query params:
    - search: keyword
    - category: string
    - job_type: string
    - min_pay: number
    - max_distance: km float
    - lat, lon: reference user location
    - experience: string
    - employer_id: int
    - status: default 'active'
    - sort_by: 'latest', 'pay_desc', 'nearest'
    """
    search = request.args.get('search', '').strip().lower()
    category = request.args.get('category', '').strip()
    job_type = request.args.get('job_type', '').strip()
    experience = request.args.get('experience', '').strip()
    work_arrangement = request.args.get('work_arrangement', '').strip()
    qualification = request.args.get('qualification', '').strip()
    fresher_only = request.args.get('fresher_only', '').strip().lower() in ['1', 'true', 'yes']
    min_pay = request.args.get('min_pay', type=float)
    max_dist = request.args.get('max_distance', type=float)
    ref_lat = request.args.get('lat', type=float)
    ref_lon = request.args.get('lon', type=float)
    emp_id = request.args.get('employer_id', type=int)
    status = request.args.get('status', 'active')
    sort_by = request.args.get('sort_by', 'latest')

    query = """
        SELECT j.*, ep.company_name, ep.business_type, ep.address as company_address, u.avatar_url as employer_avatar
        FROM jobs j
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN users u ON ep.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status and status != 'all':
        query += " AND j.status = ?"
        params.append(status)

    if emp_id:
        query += " AND j.employer_id = ?"
        params.append(emp_id)

    if category and category != 'All':
        query += " AND j.category = ?"
        params.append(category)

    if job_type and job_type != 'All':
        query += " AND j.job_type = ?"
        params.append(job_type)

    if experience and experience != 'All':
        query += " AND j.experience_required = ?"
        params.append(experience)

    if work_arrangement and work_arrangement != 'All':
        query += " AND (LOWER(j.work_arrangement) = ? OR LOWER(j.location_address) LIKE ?)"
        params.extend([work_arrangement.lower(), f"%{work_arrangement.lower()}%"])

    if qualification and qualification != 'All':
        query += " AND (LOWER(j.min_qualification) LIKE ? OR LOWER(j.min_qualification) = 'any graduate' OR LOWER(j.description) LIKE ?)"
        params.extend([f"%{qualification.lower()}%", f"%{qualification.lower()}%"])

    if fresher_only:
        query += " AND (j.is_fresher_friendly = 1 OR j.min_experience_years <= 0 OR LOWER(j.experience_required) LIKE '%fresher%' OR LOWER(j.experience_required) LIKE '%no experience%')"

    if min_pay:
        query += " AND (j.pay_amount >= ? OR j.salary_max >= ?)"
        params.extend([min_pay, min_pay])

    if search:
        query += " AND (LOWER(j.title) LIKE ? OR LOWER(j.description) LIKE ? OR LOWER(ep.company_name) LIKE ? OR LOWER(j.location_address) LIKE ? OR LOWER(COALESCE(j.responsibilities, '')) LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    query += " ORDER BY j.created_at DESC"

    jobs = query_db(query, params)

    # Attach skills and compute distances
    job_ids = [j['id'] for j in jobs]
    skills_map = {}
    if job_ids:
        placeholders = ','.join(['?'] * len(job_ids))
        skills_records = query_db(f"SELECT job_id, skill_name FROM job_skills WHERE job_id IN ({placeholders})", job_ids)
        for r in skills_records:
            skills_map.setdefault(r['job_id'], []).append(r['skill_name'])

    processed = []
    for job in jobs:
        j_dict = dict(job)
        j_dict['skills'] = skills_map.get(job['id'], [])
        
        # Calculate distance
        is_remote = (j_dict.get('work_arrangement') or '').lower() == 'remote' or 'remote' in (j_dict.get('location_address') or '').lower()
        if is_remote:
            j_dict['distance_km'] = 0.0
            j_dict['formatted_distance'] = "Remote (Work from Anywhere)"
        elif ref_lat is not None and ref_lon is not None and job['latitude'] is not None and job['longitude'] is not None:
            dist = haversine_distance(ref_lat, ref_lon, job['latitude'], job['longitude'])
            j_dict['distance_km'] = dist
            j_dict['formatted_distance'] = format_distance(dist)
        else:
            j_dict['distance_km'] = None
            j_dict['formatted_distance'] = "Distance N/A"

        # Apply distance radius filter if specified (remote jobs pass through distance filter)
        if max_dist is not None and not is_remote and j_dict['distance_km'] is not None:
            if j_dict['distance_km'] > max_dist:
                continue

        processed.append(j_dict)

    # Sorting
    if sort_by == 'pay_desc':
        processed.sort(key=lambda x: x['pay_amount'], reverse=True)
    elif sort_by == 'nearest':
        processed.sort(key=lambda x: (x['distance_km'] is None, x['distance_km']))

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # cap at 100
    total = len(processed)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    paged = processed[start:start + per_page]

    return jsonify({
        'jobs': paged,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    })

@jobs_bp.route('/<int:job_id>', methods=['GET'])
def get_job_detail(job_id):
    ref_lat = request.args.get('lat', type=float)
    ref_lon = request.args.get('lon', type=float)

    job = query_db("""
        SELECT j.*, ep.company_name, ep.business_type, ep.description as company_bio,
               ep.address as company_address, ep.user_id as employer_user_id,
               u.avatar_url as employer_avatar, u.phone as employer_phone
        FROM jobs j
        JOIN employer_profiles ep ON j.employer_id = ep.id
        JOIN users u ON ep.user_id = u.id
        WHERE j.id = ?
    """, (job_id,), one=True)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    job_dict = dict(job)
    job_dict['skills'] = [s['skill_name'] for s in query_db("SELECT skill_name FROM job_skills WHERE job_id = ?", (job_id,))]

    if ref_lat is not None and ref_lon is not None and job['latitude'] and job['longitude']:
        dist = haversine_distance(ref_lat, ref_lon, job['latitude'], job['longitude'])
        job_dict['distance_km'] = dist
        job_dict['formatted_distance'] = format_distance(dist)
    else:
        job_dict['distance_km'] = None
        job_dict['formatted_distance'] = "Distance N/A"

    return jsonify({'job': job_dict})

@jobs_bp.route('', methods=['POST'])
@token_required
@role_required('employer')
def create_job():
    user_id = request.current_user['user_id']
    profile = query_db("SELECT id, latitude, longitude, address FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
    if not profile:
        return jsonify({'error': 'Employer profile not found'}), 404

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    pay_amount = data.get('pay_amount')

    if not title or not description or not category or pay_amount is None:
        return jsonify({'error': 'Title, description, category, and pay amount are required'}), 400

    job_type = data.get('job_type', 'Part-time')
    pay_frequency = data.get('pay_frequency', 'day')
    date_needed = data.get('date_needed', 'Immediate')
    start_time = data.get('start_time', '10:00')
    end_time = data.get('end_time', '18:00')
    workers_needed = int(data.get('workers_needed', 1))
    experience_required = data.get('experience_required', 'No Experience')
    location_address = data.get('location_address') or profile['address'] or 'Hyderabad'
    lat = float(data.get('latitude', profile['latitude'] or 17.4483))
    lon = float(data.get('longitude', profile['longitude'] or 78.3915))
    deadline = data.get('application_deadline')

    min_qualification = data.get('min_qualification', 'Any Graduate')
    work_arrangement = data.get('work_arrangement', 'On-site')
    is_fresher_friendly = 1 if data.get('is_fresher_friendly', True) in [True, 1, '1', 'true'] else 0
    min_experience_years = float(data.get('min_experience_years', 0.0))
    salary_min = float(data.get('salary_min')) if data.get('salary_min') is not None else float(pay_amount)
    salary_max = float(data.get('salary_max')) if data.get('salary_max') is not None else float(pay_amount)
    responsibilities = data.get('responsibilities', '')
    eligibility = data.get('eligibility', '')
    benefits = data.get('benefits', '')

    try:
        job_id = execute_db("""
            INSERT INTO jobs (
                employer_id, title, description, category, job_type,
                pay_amount, pay_frequency, date_needed, start_time, end_time,
                workers_needed, experience_required, location_address,
                latitude, longitude, application_deadline, status,
                min_qualification, work_arrangement, is_fresher_friendly,
                min_experience_years, salary_min, salary_max,
                responsibilities, eligibility, benefits
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile['id'], title, description, category, job_type,
            pay_amount, pay_frequency, date_needed, start_time, end_time,
            workers_needed, experience_required, location_address,
            lat, lon, deadline,
            min_qualification, work_arrangement, is_fresher_friendly,
            min_experience_years, salary_min, salary_max,
            responsibilities, eligibility, benefits
        ))

        # Insert required skills
        skills = data.get('skills', [])
        if isinstance(skills, list):
            for sk in skills:
                if sk and str(sk).strip():
                    execute_db("INSERT INTO job_skills (job_id, skill_name) VALUES (?, ?)", (job_id, str(sk).strip()))

        return jsonify({
            'message': 'Job posted successfully',
            'job_id': job_id,
            'job': {'id': job_id, 'title': title}
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to create job: {str(e)}'}), 500

@jobs_bp.route('/<int:job_id>/status', methods=['PATCH'])
@token_required
@role_required('employer', 'admin')
def update_job_status(job_id):
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
        return jsonify({'error': 'Job not found or unauthorized'}), 404

    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ['active', 'filled', 'completed', 'cancelled', 'deactivated']:
        return jsonify({'error': 'Invalid status'}), 400

    execute_db("UPDATE jobs SET status = ? WHERE id = ?", (new_status, job_id))
    return jsonify({'message': f'Job marked as {new_status}'})

@jobs_bp.route('/<int:job_id>', methods=['PUT'])
@token_required
@role_required('employer', 'admin')
def update_job(job_id):
    user_id = request.current_user['user_id']
    user_role = request.current_user.get('role')

    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if user_role != 'admin':
        emp = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
        if not emp or job['employer_id'] != emp['id']:
            return jsonify({'error': "You cannot modify another employer's job"}), 403

    data = request.get_json() or {}
    title = data.get('title', job['title']).strip()
    description = data.get('description', job['description']).strip()
    category = data.get('category', job['category']).strip()
    job_type = data.get('job_type', job['job_type']).strip()
    pay_amount = float(data.get('pay_amount', job['pay_amount']))
    pay_frequency = data.get('pay_frequency', job['pay_frequency'])
    date_needed = data.get('date_needed', job['date_needed'])
    start_time = data.get('start_time', job['start_time'])
    end_time = data.get('end_time', job['end_time'])
    workers_needed = int(data.get('workers_needed', job['workers_needed']))
    experience_required = data.get('experience_required', job['experience_required'])
    location_address = data.get('location_address', job['location_address'])
    latitude = float(data.get('latitude', job['latitude']))
    longitude = float(data.get('longitude', job['longitude']))
    application_deadline = data.get('application_deadline', job['application_deadline'])

    min_qualification = data.get('min_qualification', job.get('min_qualification', 'Any Graduate'))
    work_arrangement = data.get('work_arrangement', job.get('work_arrangement', 'On-site'))
    is_fresher_friendly = int(data.get('is_fresher_friendly', job.get('is_fresher_friendly', 1)))
    min_experience_years = float(data.get('min_experience_years', job.get('min_experience_years', 0.0)))
    salary_min = float(data.get('salary_min', job.get('salary_min') or pay_amount))
    salary_max = float(data.get('salary_max', job.get('salary_max') or pay_amount))
    responsibilities = data.get('responsibilities', job.get('responsibilities') or '')
    eligibility = data.get('eligibility', job.get('eligibility') or '')
    benefits = data.get('benefits', job.get('benefits') or '')

    execute_db("""
        UPDATE jobs SET
            title = ?, description = ?, category = ?, job_type = ?,
            pay_amount = ?, pay_frequency = ?, date_needed = ?,
            start_time = ?, end_time = ?, workers_needed = ?,
            experience_required = ?, location_address = ?,
            latitude = ?, longitude = ?, application_deadline = ?,
            min_qualification = ?, work_arrangement = ?, is_fresher_friendly = ?,
            min_experience_years = ?, salary_min = ?, salary_max = ?,
            responsibilities = ?, eligibility = ?, benefits = ?
        WHERE id = ?
    """, (
        title, description, category, job_type,
        pay_amount, pay_frequency, date_needed,
        start_time, end_time, workers_needed,
        experience_required, location_address,
        latitude, longitude, application_deadline,
        min_qualification, work_arrangement, is_fresher_friendly,
        min_experience_years, salary_min, salary_max,
        responsibilities, eligibility, benefits, job_id
    ))

    # Update skills if passed
    if 'skills' in data and isinstance(data['skills'], list):
        execute_db("DELETE FROM job_skills WHERE job_id = ?", (job_id,))
        for sk in data['skills']:
            if sk and str(sk).strip():
                execute_db("INSERT INTO job_skills (job_id, skill_name) VALUES (?, ?)", (job_id, str(sk).strip()))

    return jsonify({'message': 'Job updated successfully', 'job_id': job_id}), 200

@jobs_bp.route('/<int:job_id>', methods=['DELETE'])
@token_required
def delete_job(job_id):
    user_id = request.current_user['user_id']
    role = request.current_user.get('role', '')

    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Allow if admin or owning employer
    if role == 'admin':
        pass
    elif role == 'employer':
        emp = query_db("SELECT id FROM employer_profiles WHERE user_id = ?", (user_id,), one=True)
        if not emp or job['employer_id'] != emp['id']:
            return jsonify({'error': "You cannot modify another employer's job"}), 403
    else:
        return jsonify({'error': 'Unauthorized to delete jobs'}), 403

    execute_db("DELETE FROM jobs WHERE id = ?", (job_id,))
    return jsonify({'message': 'Job deleted successfully'}), 200

