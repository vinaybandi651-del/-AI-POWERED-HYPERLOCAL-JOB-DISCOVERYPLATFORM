-- HyperLocal Job Match Database Schema

PRAGMA foreign_keys = ON;

-- Users table (students, employers, admin)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'employer', 'admin')),
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    avatar_url TEXT,
    is_verified INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Student profiles (Fresh Graduates & Job Seekers)
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    education TEXT,
    institution TEXT,
    experience_level TEXT DEFAULT 'Fresher', -- Fresher, Entry-Level, Experienced
    bio TEXT,
    preferred_categories TEXT, -- JSON array of categories
    preferred_job_type TEXT DEFAULT 'Full-time', -- Full-time, Internship, Part-time, Contract
    expected_salary REAL DEFAULT 350000.0,
    salary_type TEXT DEFAULT 'year', -- year, month, day, hour
    max_distance_km REAL DEFAULT 15.0,
    latitude REAL DEFAULT 17.4447, -- Default center (e.g. Tech Hub / Cyberabad)
    longitude REAL DEFAULT 78.3840,
    address TEXT,
    available_days TEXT, -- JSON array: ["Mon","Tue","Sat","Sun"]
    available_time_start TEXT DEFAULT '09:00',
    available_time_end TEXT DEFAULT '18:00',
    profile_completed INTEGER DEFAULT 1,
    degree TEXT DEFAULT 'B.Tech', -- B.Tech, B.Sc, B.Com, BBA, BCA, MCA, MBA, Diploma, etc.
    specialization TEXT, -- e.g. Computer Science, Mechanical, Finance, Data Science
    college_name TEXT,
    graduation_year INTEGER,
    fresher_status TEXT DEFAULT 'Fresher', -- Fresher, Entry-Level, Experienced
    preferred_roles TEXT, -- JSON array of target roles e.g. ["Software Engineer", "Web Developer"]
    willingness_to_relocate INTEGER DEFAULT 1,
    resume_url TEXT,
    projects TEXT, -- Projects details or JSON array
    certifications TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Master Skills
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT
);

-- Student Skills
CREATE TABLE IF NOT EXISTS student_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    proficiency TEXT DEFAULT 'Intermediate', -- Beginner, Intermediate, Advanced
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE
);

-- Employer profiles
CREATE TABLE IF NOT EXISTS employer_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    business_type TEXT, -- IT, Consulting, FinTech, Healthcare, EduTech, Retail, etc.
    description TEXT,
    website TEXT,
    address TEXT,
    latitude REAL DEFAULT 17.4450,
    longitude REAL DEFAULT 78.3850,
    verified INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    job_type TEXT DEFAULT 'Full-time', -- Full-time, Internship, Contract, Part-time
    pay_amount REAL NOT NULL,
    pay_frequency TEXT DEFAULT 'year', -- year, month, day, hour
    date_needed TEXT, -- e.g. 'Immediate' / 'Within 30 Days'
    start_time TEXT,
    end_time TEXT,
    workers_needed INTEGER DEFAULT 1,
    experience_required TEXT DEFAULT 'Fresher / 0 Years', -- Fresher / 0 Years, 0-1 Years, 1-2 Years, 2+ Years
    location_address TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    application_deadline TEXT,
    status TEXT DEFAULT 'active', -- active, filled, completed, cancelled
    min_qualification TEXT DEFAULT 'Any Graduate', -- B.Tech, B.Sc, B.Com, BBA, BCA, MCA, MBA, Diploma, Any Graduate
    work_arrangement TEXT DEFAULT 'On-site', -- On-site, Hybrid, Remote
    is_fresher_friendly INTEGER DEFAULT 1, -- 1 for true, 0 for false
    min_experience_years REAL DEFAULT 0.0,
    salary_min REAL,
    salary_max REAL,
    responsibilities TEXT,
    eligibility TEXT,
    benefits TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employer_id) REFERENCES employer_profiles(id) ON DELETE CASCADE
);

-- Job Skills Required
CREATE TABLE IF NOT EXISTS job_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    cover_note TEXT,
    resume_url TEXT,
    status TEXT DEFAULT 'applied' CHECK(status IN ('pending', 'applied', 'under_review', 'shortlisted', 'accepted', 'rejected', 'withdrawn', 'completed')),
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
);

-- Email Verification OTP & Tokens
CREATE TABLE IF NOT EXISTS email_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Email Action Tokens for Application Approval (Accept/Reject)
CREATE TABLE IF NOT EXISTS action_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    action TEXT NOT NULL CHECK(action IN ('accept', 'reject')),
    recipient_email TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used INTEGER DEFAULT 0,
    used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- Application Decision Audits
CREATE TABLE IF NOT EXISTS application_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    actor_email TEXT,
    actor_ip TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- Email Delivery Logs
CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL, -- 'sent', 'failed', 'queued'
    error_message TEXT,
    application_id INTEGER,
    html_content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Saved Jobs (Bookmarks)
CREATE TABLE IF NOT EXISTS saved_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE(student_id, job_id)
);

-- Interactions for Collaborative Filtering
CREATE TABLE IF NOT EXISTS job_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL, -- VIEW_JOB, SEARCH_JOB, SAVE_JOB, APPLY_JOB, ACCEPT_JOB, COMPLETE_JOB, REJECT_JOB, RATE_JOB
    interaction_weight INTEGER NOT NULL, -- View=1, Search=2, Save=3, Apply=5, Accept=7, Complete=10
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Chat Messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    application_id INTEGER,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE SET NULL,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'system', -- application_status, new_job, message, reminder, system
    link TEXT,
    is_read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Reviews and Ratings
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    reviewee_id INTEGER NOT NULL,
    rating REAL NOT NULL CHECK(rating >= 1.0 AND rating <= 5.0),
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewee_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Recommendation Weighting Settings (Configurable AI engine)
CREATE TABLE IF NOT EXISTS recommendation_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_weight REAL DEFAULT 0.40,
    location_weight REAL DEFAULT 0.25,
    availability_weight REAL DEFAULT 0.15,
    collaborative_weight REAL DEFAULT 0.10,
    salary_weight REAL DEFAULT 0.10,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Availabilities table
CREATE TABLE IF NOT EXISTS availabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    start_time TEXT DEFAULT '10:00',
    end_time TEXT DEFAULT '19:00',
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE
);

-- Master Locations table
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    area TEXT,
    city TEXT DEFAULT 'Hyderabad',
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Recommendations history table
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    match_score REAL NOT NULL,
    reasons TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

