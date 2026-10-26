import numpy as np
from collections import defaultdict

def build_interaction_matrix(interactions):
    """
    Build student-job interaction score matrix from raw interaction records.
    interactions: list of dicts with 'student_id', 'job_id', 'interaction_weight'
    Returns:
    - student_ids: sorted list of student IDs
    - job_ids: sorted list of job IDs
    - matrix: 2D numpy array [n_students, n_jobs]
    - student_map: dict student_id -> row index
    - job_map: dict job_id -> col index
    """
    if not interactions:
        return [], [], np.zeros((0, 0)), {}, {}

    student_set = sorted(list({i['student_id'] for i in interactions}))
    job_set = sorted(list({i['job_id'] for i in interactions}))

    student_map = {sid: idx for idx, sid in enumerate(student_set)}
    job_map = {jid: idx for idx, jid in enumerate(job_set)}

    matrix = np.zeros((len(student_set), len(job_set)), dtype=np.float32)

    # Accumulate interaction weights
    for record in interactions:
        s_idx = student_map[record['student_id']]
        j_idx = job_map[record['job_id']]
        weight = float(record.get('interaction_weight', 1))
        matrix[s_idx, j_idx] += weight

    return student_set, job_set, matrix, student_map, job_map

def compute_cosine_similarity_matrix(matrix):
    """Compute cosine similarity between columns (items) or rows (users)."""
    norms = np.linalg.norm(matrix, axis=0, keepdims=True)
    norms[norms == 0] = 1e-9
    normalized = matrix / norms
    sim_matrix = np.dot(normalized.T, normalized)
    return sim_matrix

def calculate_collaborative_score(student_id, target_job_id, interactions):
    """
    Calculate collaborative filtering score for a given student and job.
    Uses Item-based collaborative filtering with User-based fallback.
    Returns:
    - score: float 0.0 to 1.0
    - reason: explanation string
    - is_cold_start: boolean
    """
    if not interactions:
        return 0.5, "New system baseline (Cold-start)", True

    student_ids, job_ids, matrix, student_map, job_map = build_interaction_matrix(interactions)

    # Check if student is new (Cold-start)
    if student_id not in student_map:
        # Check overall popularity of target job
        if target_job_id in job_map:
            col_idx = job_map[target_job_id]
            job_interactions = matrix[:, col_idx]
            popularity = float(np.sum(job_interactions > 0)) / max(1, len(student_ids))
            score = 0.5 + min(0.4, popularity * 0.5)
            reason = f"Popular among students ({int(np.sum(job_interactions > 0))} student interactions)"
            return score, reason, True
        return 0.5, "Cold-start profile: initial matching based on content & location", True

    s_idx = student_map[student_id]
    student_vector = matrix[s_idx, :]

    # Check if student has no interactions
    if np.sum(student_vector) == 0:
        return 0.5, "Cold-start profile: initial matching based on content & location", True

    # If target job is not in interactions history yet
    if target_job_id not in job_map:
        return 0.5, "Newly posted opportunity", False

    target_j_idx = job_map[target_job_id]

    # Item-based collaborative filtering:
    # Compute job-job similarity matrix
    job_sim = compute_cosine_similarity_matrix(matrix) # [n_jobs, n_jobs]
    target_similarities = job_sim[target_j_idx, :]

    # Calculate weighted interaction score from jobs this student liked/applied
    numerator = np.dot(target_similarities, student_vector)
    denominator = np.sum(np.abs(target_similarities[student_vector > 0]))

    if denominator > 0:
        raw_score = numerator / denominator
        # Normalize into [0, 1] range (interactions range from 1 to 20+)
        cf_score = min(1.0, max(0.0, raw_score / 10.0))
        # Ensure meaningful baseline
        cf_score = max(0.2, cf_score)
        reason = "Recommended based on similar jobs you and your peers engaged with"
        return round(float(cf_score), 3), reason, False

    # User-based collaborative filtering fallback:
    # Student-student cosine similarity
    s_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    s_norms[s_norms == 0] = 1e-9
    s_normed = matrix / s_norms
    user_sims = np.dot(s_normed, s_normed[s_idx, :]) # [n_students]
    user_sims[s_idx] = 0 # Don't compare with self

    top_similar_users = np.argsort(user_sims)[::-1][:5]
    if len(top_similar_users) > 0 and user_sims[top_similar_users[0]] > 0.1:
        peer_interactions = matrix[top_similar_users, target_j_idx]
        if np.any(peer_interactions > 0):
            return 0.85, "Students with matching career preferences applied to this role", False

    return 0.55, "Matches platform peer trend", False
