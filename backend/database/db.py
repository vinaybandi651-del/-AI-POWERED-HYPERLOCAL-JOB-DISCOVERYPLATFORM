import sqlite3
import os
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'hyperlocal_jobs.db')

def get_db_connection():
    """Get a SQLite database connection with row factory configured."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db():
    """Context manager for safe DB connection handling."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database tables using schema.sql and apply backward-compatible column migrations."""
    schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    with get_db() as conn:
        conn.executescript(schema_sql)
        cursor = conn.cursor()

        # Check and add missing columns in users table
        cursor.execute("PRAGMA table_info(users)")
        user_cols = [r[1] for r in cursor.fetchall()]
        if 'is_verified' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1")
        if 'first_name' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
        if 'last_name' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
        if 'failed_login_attempts' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
        if 'locked_until' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until DATETIME")

        # Check and add missing columns in student_profiles table
        cursor.execute("PRAGMA table_info(student_profiles)")
        sp_cols = [r[1] for r in cursor.fetchall()]
        if 'degree' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN degree TEXT DEFAULT 'B.Tech'")
        if 'specialization' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN specialization TEXT")
        if 'college_name' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN college_name TEXT")
        if 'graduation_year' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN graduation_year INTEGER")
        if 'fresher_status' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN fresher_status TEXT DEFAULT 'Fresher'")
        if 'preferred_roles' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN preferred_roles TEXT")
        if 'willingness_to_relocate' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN willingness_to_relocate INTEGER DEFAULT 1")
        if 'resume_url' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN resume_url TEXT")
        if 'projects' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN projects TEXT")
        if 'certifications' not in sp_cols:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN certifications TEXT")

        # Check and add missing columns in jobs table
        cursor.execute("PRAGMA table_info(jobs)")
        job_cols = [r[1] for r in cursor.fetchall()]
        if 'min_qualification' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN min_qualification TEXT DEFAULT 'Any Graduate'")
        if 'work_arrangement' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN work_arrangement TEXT DEFAULT 'On-site'")
        if 'is_fresher_friendly' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN is_fresher_friendly INTEGER DEFAULT 1")
        if 'min_experience_years' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN min_experience_years REAL DEFAULT 0.0")
        if 'salary_min' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN salary_min REAL")
        if 'salary_max' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN salary_max REAL")
        if 'responsibilities' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN responsibilities TEXT")
        if 'eligibility' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN eligibility TEXT")
        if 'benefits' not in job_cols:
            cursor.execute("ALTER TABLE jobs ADD COLUMN benefits TEXT")

        # Check and add missing columns in applications table
        cursor.execute("PRAGMA table_info(applications)")
        app_cols = [r[1] for r in cursor.fetchall()]
        if 'reference_code' not in app_cols:
            cursor.execute("ALTER TABLE applications ADD COLUMN reference_code TEXT")
        if 'resume_url' not in app_cols:
            cursor.execute("ALTER TABLE applications ADD COLUMN resume_url TEXT")
        if 'decided_at' not in app_cols:
            cursor.execute("ALTER TABLE applications ADD COLUMN decided_at DATETIME")
        if 'decided_by' not in app_cols:
            cursor.execute("ALTER TABLE applications ADD COLUMN decided_by TEXT")
        if 'decision_note' not in app_cols:
            cursor.execute("ALTER TABLE applications ADD COLUMN decision_note TEXT")
        if 'status_notes' not in app_cols:
            cursor.execute("ALTER TABLE applications ADD COLUMN status_notes TEXT")

        # Check and add missing columns in email_logs table
        cursor.execute("PRAGMA table_info(email_logs)")
        el_cols = [r[1] for r in cursor.fetchall()]
        if 'html_content' not in el_cols:
            cursor.execute("ALTER TABLE email_logs ADD COLUMN html_content TEXT")

        # Populate reference_code for existing applications if empty
        cursor.execute("SELECT id FROM applications WHERE reference_code IS NULL OR reference_code = ''")
        for row in cursor.fetchall():
            ref = f"APP-2026-{row[0]:04d}"
            cursor.execute("UPDATE applications SET reference_code = ? WHERE id = ?", (ref, row[0]))

        # Ensure applications table supports 'pending' and 'withdrawn' in CHECK constraint
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='applications'")
        app_sql_row = cursor.fetchone()
        if app_sql_row and "'pending'" not in app_sql_row[0]:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("""
                CREATE TABLE applications_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    cover_note TEXT,
                    resume_url TEXT,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'applied', 'under_review', 'shortlisted', 'accepted', 'rejected', 'withdrawn', 'completed')),
                    reference_code TEXT UNIQUE,
                    decided_at DATETIME,
                    decided_by TEXT,
                    decision_note TEXT,
                    status_notes TEXT,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
                    UNIQUE(job_id, student_id)
                )
            """)
            cursor.execute("""
                INSERT INTO applications_new (id, job_id, student_id, cover_note, resume_url, status, reference_code, decided_at, decided_by, decision_note, status_notes, applied_at, updated_at)
                SELECT id, job_id, student_id, cover_note, resume_url, status, reference_code, decided_at, decided_by, decision_note, status_notes, applied_at, updated_at
                FROM applications
            """)
            cursor.execute("DROP TABLE applications")
            cursor.execute("ALTER TABLE applications_new RENAME TO applications")
            cursor.execute("PRAGMA foreign_keys = ON")

        # Ensure default recommendation weights exist
        cursor.execute("SELECT COUNT(*) FROM recommendation_weights")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO recommendation_weights (content_weight, location_weight, availability_weight, collaborative_weight, salary_weight)
                VALUES (0.40, 0.25, 0.15, 0.10, 0.10)
            """)

def query_db(query, args=(), one=False):
    """Execute a read query and return dict or list of dicts."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, args)
        r = cur.fetchall()
        cur.close()
        return (dict(r[0]) if r else None) if one else [dict(row) for row in r]

def execute_db(query, args=()):
    """Execute an insert/update/delete query and return lastrowid."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, args)
        last_id = cur.lastrowid
        cur.close()
        return last_id
