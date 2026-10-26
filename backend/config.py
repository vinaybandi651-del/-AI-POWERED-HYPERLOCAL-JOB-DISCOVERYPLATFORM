import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

def load_dotenv_file(filepath):
    """Load key-value pairs from .env file into os.environ if not already set."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v

# Attempt loading from project root or backend
load_dotenv_file(os.path.join(PROJECT_ROOT, '.env'))
load_dotenv_file(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hyperlocal-job-match-production-secret-key-2026')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    
    # SQLite default, seamlessly replaceable by PostgreSQL:
    # e.g. postgresql://user:password@localhost:5432/hyperlocal_jobs
    db_path = os.path.join(BASE_DIR, 'hyperlocal_jobs.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1')
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 72))

    # Allow uploads up to 10MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # Admin & Reviewer Configuration
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'vinaybandi651@gmail.com').strip()

    # Email Delivery Settings (Gmail SMTP with App Password)
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com').strip()
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_EMAIL = (os.environ.get('SMTP_EMAIL') or os.environ.get('SMTP_USERNAME') or ADMIN_EMAIL).strip()
    SMTP_APP_PASSWORD = (os.environ.get('SMTP_APP_PASSWORD') or os.environ.get('SMTP_PASSWORD') or '').strip()

    SMTP_USERNAME = SMTP_EMAIL
    SMTP_PASSWORD = SMTP_APP_PASSWORD
    MAIL_FROM = os.environ.get('MAIL_FROM', '') or (f'"GradMatch AI" <{SMTP_USERNAME}>' if SMTP_USERNAME else f'"GradMatch AI" <{ADMIN_EMAIL}>')
    APPLICATION_BASE_URL = os.environ.get('APPLICATION_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')

    # Send all new job application notification emails to ADMIN_EMAIL (vinaybandi651@gmail.com)
    _raw_reviewers = os.environ.get('APPLICATION_NOTIFICATION_EMAILS', '')
    if _raw_reviewers:
        _parsed = [e.strip() for e in _raw_reviewers.split(',') if e.strip()]
        if ADMIN_EMAIL not in _parsed:
            _parsed.insert(0, ADMIN_EMAIL)
        APPLICATION_NOTIFICATION_EMAILS = _parsed
    else:
        APPLICATION_NOTIFICATION_EMAILS = [ADMIN_EMAIL]
