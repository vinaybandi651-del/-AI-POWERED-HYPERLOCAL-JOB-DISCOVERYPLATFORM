from utils.geo import haversine_distance, calculate_location_score, format_distance

def evaluate_location_match(student, job):
    """
    Evaluate geographic suitability between candidate and job.
    Supports:
    - Remote jobs (work from anywhere with full 1.0 location score)
    - Hybrid arrangements
    - Relocation willingness
    - Haversine distance proximity decay
    Returns:
    - location_score: float 0.0 to 1.0
    - distance_km: float distance in km or None
    - reason: explanation string
    """
    work_arrangement = (job.get('work_arrangement') or '').strip().lower()
    loc_address = (job.get('location_address') or '').strip().lower()
    job_type = (job.get('job_type') or '').strip().lower()

    # Remote job check: remote jobs should not be penalized by distance
    if work_arrangement == 'remote' or 'remote' in loc_address or 'remote' in job_type or 'work from home' in loc_address:
        return 1.0, 0.0, "Remote role (Work from anywhere with zero commute)"

    s_lat = student.get('latitude')
    s_lon = student.get('longitude')
    j_lat = job.get('latitude')
    j_lon = job.get('longitude')
    max_dist = student.get('max_distance_km', 15.0) or 15.0
    relocate = bool(student.get('willingness_to_relocate', 0))

    if s_lat is None or s_lon is None or j_lat is None or j_lon is None:
        return 0.65, None, f"Location: {job.get('location_address') or 'Location available upon request'}"

    distance = haversine_distance(s_lat, s_lon, j_lat, j_lon)
    score = calculate_location_score(distance, max_dist)

    if distance <= 1.0:
        reason = f"Hyperlocal! Only {format_distance(distance)} from your location"
    elif distance <= max_dist:
        reason = f"{format_distance(distance)} (within your {max_dist:.0f} km preference)"
    elif relocate:
        # Candidate is willing to relocate for the job
        score = max(score, 0.60)
        reason = f"{format_distance(distance)} (Candidate open to relocation)"
    else:
        reason = f"{format_distance(distance)} (exceeds your {max_dist:.0f} km limit)"

    # Minor boost for hybrid flexibility
    if work_arrangement == 'hybrid':
        score = min(1.0, score + 0.10)
        reason += " [Hybrid Flexibility]"

    return score, distance, reason

