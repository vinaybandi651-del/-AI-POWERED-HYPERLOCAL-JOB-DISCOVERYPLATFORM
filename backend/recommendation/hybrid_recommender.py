import json
from .content_based import calculate_content_score
from .location_matching import evaluate_location_match
from .collaborative import calculate_collaborative_score
from utils.geo import format_distance

def calculate_availability_score(student, job):
    """
    Score compatibility between student schedule and job timing.
    Returns: score (0.0 to 1.0), reason string
    """
    score = 0.8 # default good baseline
    reasons = []

    s_days = []
    if student.get('available_days'):
        try:
            if isinstance(student['available_days'], list):
                s_days = [d.lower() for d in student['available_days']]
            else:
                s_days = [d.lower() for d in json.loads(student['available_days'])]
        except Exception:
            s_days = [d.strip().lower() for d in student['available_days'].split(',')]

    j_date = (job.get('date_needed') or '').lower()
    
    # Days matching
    day_matched = False
    if not s_days or not j_date or 'flexible' in j_date or 'any' in j_date or 'immediate' in j_date:
        score += 0.1
        day_matched = True
        reasons.append("Flexible date/schedule fits student calendar")
    else:
        for day in s_days:
            if day in j_date or ('weekend' in j_date and day in ['sat', 'sun', 'saturday', 'sunday']):
                day_matched = True
                break
        if day_matched:
            score += 0.1
            reasons.append(f"Available on required job days ({job.get('date_needed')})")
        else:
            score -= 0.3
            reasons.append(f"Job date ({job.get('date_needed')}) may clash with student schedule")

    # Time matching
    s_start = student.get('available_time_start')
    s_end = student.get('available_time_end')
    j_start = job.get('start_time')
    j_end = job.get('end_time')

    if j_start and j_end and s_start and s_end:
        try:
            # Simple HH:MM comparison
            if s_start <= j_start and s_end >= j_end:
                score += 0.1
                reasons.append(f"Shift hours ({j_start} - {j_end}) fit your available window")
            elif s_start <= j_end and s_end >= j_start:
                score += 0.05
                reasons.append(f"Partial time alignment with shift ({j_start} - {j_end})")
            else:
                score -= 0.2
        except Exception:
            pass

    final_score = min(1.0, max(0.1, score))
    return final_score, (reasons[0] if reasons else "Schedule compatibility confirmed")

def calculate_salary_score(student, job):
    """
    Score compatibility between candidate expected pay and job compensation.
    Returns: score (0.0 to 1.0), reason string
    """
    s_exp = float(student.get('expected_salary') or 500.0)
    s_freq = (student.get('salary_type') or 'day').lower()
    j_pay = float(job.get('pay_amount') or 500.0)
    j_freq = (job.get('pay_frequency') or 'day').lower()

    def to_annual(val, freq):
        if 'year' in freq or 'annual' in freq or 'lpa' in freq:
            return val
        if 'month' in freq:
            return val * 12
        if 'day' in freq:
            return val * 250
        if 'hour' in freq:
            return val * 2000
        return val

    # If job has salary_min and salary_max
    j_min = job.get('salary_min')
    j_max = job.get('salary_max')
    if j_min is not None and j_max is not None and float(j_max) > 0:
        j_min_ann = to_annual(float(j_min), j_freq)
        j_max_ann = to_annual(float(j_max), j_freq)
        s_ann = to_annual(s_exp, s_freq)
        if s_ann <= j_max_ann:
            return 1.0, f"Pay of ₹{float(j_min):,.0f} - ₹{float(j_max):,.0f}/{j_freq} meets your ₹{s_exp:,.0f} target"
        ratio = j_max_ann / s_ann if s_ann > 0 else 1.0
        return max(0.3, round(ratio, 3)), f"Pay range ₹{float(j_min):,.0f} - ₹{float(j_max):,.0f}/{j_freq} (Target: ₹{s_exp:,.0f})"

    # Normalize to daily pay estimate
    s_daily = s_exp * 4 if 'hour' in s_freq else (s_exp / 25 if 'month' in s_freq else (s_exp / 250 if 'year' in s_freq else s_exp))
    j_daily = j_pay * 4 if 'hour' in j_freq else (j_pay / 25 if 'month' in j_freq else (j_pay / 250 if 'year' in j_freq else j_pay))

    if s_daily <= 0:
        return 1.0, "Competitive compensation offered"

    ratio = j_daily / s_daily
    if ratio >= 1.0:
        score = 1.0
        reason = f"Pay of ₹{j_pay:,.0f}/{j_freq} meets or exceeds your ₹{s_exp:,.0f} target"
    elif ratio >= 0.8:
        score = 0.85
        reason = f"Pay of ₹{j_pay:,.0f}/{j_freq} is close to your expected ₹{s_exp:,.0f}"
    else:
        score = max(0.2, ratio)
        reason = f"Pay is ₹{j_pay:,.0f}/{j_freq} (Target: ₹{s_exp:,.0f}/{s_freq})"

    return round(score, 3), reason

def rank_jobs_for_student(student, jobs, student_skills, job_skills_map, interactions, custom_weights=None):
    """
    Hybrid Recommendation Engine for Fresh Graduates.
    Combines:
    - Content-Based Filtering (Skills, Degree/Qualification, Fresher suitability, Category, TF-IDF)
    - Location-Aware Matching (Haversine distance score & Remote role boost)
    - Availability Matching (Days & shift hours)
    - Collaborative Filtering (Interaction history & Peer behavior)
    - Salary Score (Pay target alignment)

    Default weights:
    - Content (Skills + Qualification + Experience fit): 0.40
    - Location & Remote proximity: 0.25
    - Availability / Timing: 0.15
    - Collaborative Filtering: 0.10
    - Salary Alignment: 0.10
    """
    weights = {
        'content': 0.40,
        'location': 0.25,
        'availability': 0.15,
        'collaborative': 0.10,
        'salary': 0.10
    }
    if custom_weights:
        weights.update(custom_weights)
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}

    s_skills_lower = {s.strip().lower() for s in student_skills if s and s.strip()}
    ranked_results = []

    for job in jobs:
        # Exclude closed or inactive jobs
        if job.get('status') and job['status'] in ['filled', 'completed', 'cancelled']:
            continue

        job_id = job['id']
        j_skills = job_skills_map.get(job_id, [])

        # 1. Content-based score
        c_score, c_reasons = calculate_content_score(student, job, student_skills, j_skills)

        # 2. Location score
        l_score, distance_km, l_reason = evaluate_location_match(student, job)

        # 3. Availability score
        a_score, a_reason = calculate_availability_score(student, job)

        # 4. Collaborative score
        cf_score, cf_reason, is_cold_start = calculate_collaborative_score(student['id'], job_id, interactions)

        # 5. Salary score
        s_score, s_reason = calculate_salary_score(student, job)

        # Hybrid Weighted Score
        raw_final_score = (
            (c_score * weights['content']) +
            (l_score * weights['location']) +
            (a_score * weights['availability']) +
            (cf_score * weights['collaborative']) +
            (s_score * weights['salary'])
        )

        final_percentage = int(round(min(1.0, max(0.05, raw_final_score)) * 100))

        # Skill match and gap calculation
        matched_skills = [s for s in student_skills if any(s.strip().lower() == js.strip().lower() for js in j_skills)]
        missing_skills = [js for js in j_skills if js.strip().lower() not in s_skills_lower]

        # Compile concise "Why this job matches you" explanations
        explanation_reasons = []
        if c_reasons:
            for r in c_reasons[:2]:
                explanation_reasons.append(f"✓ {r}")
        if l_reason:
            explanation_reasons.append(f"✓ {l_reason}")
        if s_reason and ("target" in s_reason.lower() or "meets" in s_reason.lower() or "close" in s_reason.lower()):
            explanation_reasons.append(f"✓ {s_reason}")
        if cf_reason and not is_cold_start:
            explanation_reasons.append(f"✓ {cf_reason}")

        result_item = {
            **dict(job),
            'distance_km': distance_km,
            'formatted_distance': format_distance(distance_km) if distance_km is not None else "Distance N/A",
            'match_score': final_percentage,
            'scores_breakdown': {
                'content_score': int(round(c_score * 100)),
                'location_score': int(round(l_score * 100)),
                'availability_score': int(round(a_score * 100)),
                'collaborative_score': int(round(cf_score * 100)),
                'salary_score': int(round(s_score * 100)),
            },
            'weights_used': weights,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'required_skills': j_skills,
            'reasons': explanation_reasons[:4],
            'is_cold_start': is_cold_start
        }

        ranked_results.append(result_item)

    # Sort descending by match_score, then proximity
    ranked_results.sort(key=lambda x: (x['match_score'], -(x['distance_km'] if x['distance_km'] is not None else 999)), reverse=True)

    return ranked_results

