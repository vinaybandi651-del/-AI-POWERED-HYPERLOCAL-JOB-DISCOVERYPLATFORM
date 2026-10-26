import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EXPERIENCE_LEVELS = {
    'no experience': 0,
    'fresher': 0,
    'fresher / 0 years': 0,
    'entry-level': 1,
    'beginner': 1,
    '0-1 years': 1,
    'intermediate': 2,
    '1-2 years': 2,
    'experienced': 3,
    '2+ years': 3,
    'advanced': 3
}

RELATED_DEGREES = {
    'b.tech': ['b.e.', 'bca', 'mca', 'm.tech', 'b.sc', 'diploma'],
    'bca': ['b.tech', 'mca', 'b.sc', 'diploma'],
    'mca': ['bca', 'b.tech', 'm.tech', 'b.sc'],
    'b.sc': ['b.tech', 'bca', 'm.sc'],
    'b.com': ['bba', 'mba', 'm.com'],
    'bba': ['b.com', 'mba', 'bms'],
    'mba': ['bba', 'b.com', 'pgdm'],
    'diploma': ['b.tech', 'polytechnic', 'bca']
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text).lower())
    return ' '.join(text.split())

def calculate_skills_similarity(student_skills, job_skills):
    """
    Calculate direct skill overlap score and return matched / missing skills.
    student_skills: list of string skill names
    job_skills: list of string skill names
    """
    if not job_skills:
        return 1.0, [], []

    s_skills_lower = {s.strip().lower() for s in student_skills if s and s.strip()}
    j_skills_lower = {j.strip().lower() for j in job_skills if j and j.strip()}

    if not j_skills_lower:
        return 1.0, [], []

    matched = s_skills_lower.intersection(j_skills_lower)
    missing = j_skills_lower - s_skills_lower

    # Ratio of required skills matched
    score = len(matched) / len(j_skills_lower)
    return round(score, 3), list(matched), list(missing)

def calculate_qualification_score(student, job):
    """
    Evaluate educational qualification compatibility.
    Supports: B.Tech, B.Sc, B.Com, BBA, BCA, MCA, MBA, Diploma, Any Graduate, etc.
    """
    s_deg = (student.get('degree') or student.get('education') or '').strip().lower()
    j_qual = (job.get('min_qualification') or 'Any Graduate').strip().lower()

    if not j_qual or 'any graduate' in j_qual or 'all' in j_qual:
        return 1.0, "Open to Any Graduate qualification"

    if not s_deg:
        return 0.8, "Educational qualification under review"

    # Exact or substring match
    if s_deg in j_qual or j_qual in s_deg:
        return 1.0, f"Degree matches required qualification ({job.get('min_qualification')})"

    # Related degree check
    related = RELATED_DEGREES.get(s_deg, [])
    if any(rel in j_qual for rel in related):
        return 0.85, f"Related academic qualification ({job.get('min_qualification')})"

    return 0.5, f"Minimum required qualification: {job.get('min_qualification')}"

def calculate_experience_score(student, job):
    """
    Evaluate candidate experience fit with special support for fresh graduates.
    Jobs open to freshers (0 exp / fresher friendly) give full 1.0 score to freshers!
    """
    is_fresher_friendly = job.get('is_fresher_friendly', 1)
    min_exp_years = float(job.get('min_experience_years') or 0.0)
    j_exp_str = (job.get('experience_required') or 'Fresher / 0 Years').lower()

    s_exp_str = (student.get('fresher_status') or student.get('experience_level') or 'Fresher').lower()

    # Special consideration for jobs open to fresh graduates
    if is_fresher_friendly == 1 or min_exp_years == 0.0 or 'fresher' in j_exp_str or 'no experience' in j_exp_str:
        if 'fresher' in s_exp_str or 'beginner' in s_exp_str or 'entry' in s_exp_str or 'no experience' in s_exp_str:
            return 1.0, "Fresher-Friendly: 0 years experience required, ideal for fresh graduates!"
        return 1.0, f"Your profile meets experience criteria ({job.get('experience_required', 'Fresher')})"

    s_exp = EXPERIENCE_LEVELS.get(s_exp_str, 1)
    j_exp = EXPERIENCE_LEVELS.get(j_exp_str, 0)

    if s_exp >= j_exp:
        return 1.0, f"Your experience level meets required {job.get('experience_required')}"
    elif s_exp == j_exp - 1:
        return 0.65, f"Entry-level match for {job.get('experience_required')}"
    else:
        return 0.35, f"Requires {job.get('experience_required')}"

def calculate_content_score(student, job, student_skills, job_skills):
    """
    Calculate comprehensive content-based similarity score (0.0 to 1.0) for fresh graduates.
    Features:
    - Skills match (direct overlap + fuzzy TF-IDF)
    - Qualification & Degree fit
    - Experience / Fresher suitability (zero experience accommodated)
    - Job category and target role match
    - Text semantic similarity (bio, projects, education vs job description & responsibilities)
    """
    reasons = []

    # 1. Skill overlap (Weight: 40% of content score)
    skill_score, matched_skills, missing_skills = calculate_skills_similarity(student_skills, job_skills)
    if matched_skills:
        reasons.append(f"Matched skills: {', '.join([s.title() for s in matched_skills])}")
    elif job_skills:
        reasons.append(f"Skills gap: requires {', '.join([s.title() for s in job_skills])}")

    # 2. Qualification / Degree match (Weight: 20% of content score)
    qual_score, qual_reason = calculate_qualification_score(student, job)
    if qual_reason:
        reasons.append(qual_reason)

    # 3. Experience & Fresher suitability (Weight: 15% of content score)
    exp_score, exp_reason = calculate_experience_score(student, job)
    if exp_reason:
        reasons.append(exp_reason)

    # 4. Category & Target Role match (Weight: 15% of content score)
    preferred_categories = []
    if student.get('preferred_categories'):
        try:
            if isinstance(student['preferred_categories'], list):
                preferred_categories = [c.lower() for c in student['preferred_categories']]
            else:
                preferred_categories = [c.lower() for c in json.loads(student['preferred_categories'])]
        except Exception:
            preferred_categories = [student['preferred_categories'].lower()]

    job_category = (job.get('category') or '').lower()
    job_title = (job.get('title') or '').lower()

    # Preferred roles check
    preferred_roles = []
    if student.get('preferred_roles'):
        try:
            if isinstance(student['preferred_roles'], list):
                preferred_roles = [r.lower() for r in student['preferred_roles']]
            else:
                preferred_roles = [r.lower() for r in json.loads(student['preferred_roles'])]
        except Exception:
            preferred_roles = [student['preferred_roles'].lower()]

    role_or_cat_matched = False
    if any(job_category in cat or cat in job_category for cat in preferred_categories):
        role_or_cat_matched = True
        reasons.append(f"Category '{job.get('category')}' matches your career interests")
    elif any(role in job_title or job_title in role for role in preferred_roles):
        role_or_cat_matched = True
        reasons.append(f"Role '{job.get('title')}' matches your target career roles")

    if role_or_cat_matched:
        category_score = 1.0
    elif not preferred_categories and not preferred_roles:
        category_score = 0.8
    else:
        category_score = 0.4

    # 4. Job type & Qualification match (Weight: 10% of content score)
    pref_job_type = (student.get('preferred_job_type') or 'Part-time').lower()
    job_type = (job.get('job_type') or 'Part-time').lower()
    if pref_job_type in job_type or job_type in pref_job_type:
        job_type_score = 1.0
        reasons.append(f"Job schedule type matches your preference ({job.get('job_type')})")
    else:
        job_type_score = 0.6

    if job.get('min_qualification'):
        qual_score, qual_reason = calculate_qualification_score(student, job)
        if qual_reason:
            reasons.append(qual_reason)
        pref_score = (job_type_score * 0.5) + (qual_score * 0.5)
    else:
        pref_score = job_type_score

    # 5. TF-IDF text semantic similarity (Weight: 10% of content score)
    student_text = f"{student.get('bio', '')} {student.get('education', '')} {student.get('degree', '')} {student.get('specialization', '')} {student.get('projects', '')} {' '.join(student_skills)} {' '.join(preferred_categories)}"
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('category', '')} {job.get('min_qualification', '')} {job.get('responsibilities', '')} {' '.join(job_skills)}"

    try:
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform([clean_text(student_text), clean_text(job_text)])
        text_sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
    except Exception:
        text_sim = 0.5

    # Weighted Content Score (sums to 1.0)
    total_content_score = (
        (skill_score * 0.45) +
        (category_score * 0.20) +
        (exp_score * 0.15) +
        (pref_score * 0.10) +
        (text_sim * 0.10)
    )

    return min(1.0, max(0.0, total_content_score)), reasons

