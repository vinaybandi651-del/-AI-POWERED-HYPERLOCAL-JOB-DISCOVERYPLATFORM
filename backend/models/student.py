import json
from datetime import datetime
from extensions import db

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    education = db.Column(db.String(150), nullable=True)
    college = db.Column(db.String(150), nullable=True) # or institution
    experience = db.Column(db.String(50), default='Beginner') # Beginner, Intermediate, Experienced
    bio = db.Column(db.Text, nullable=True)
    preferred_categories = db.Column(db.Text, default='[]') # JSON list
    preferred_job_type = db.Column(db.String(50), default='Part-time')
    expected_salary = db.Column(db.Float, default=600.0)
    salary_type = db.Column(db.String(20), default='day') # hour, day, month
    max_distance_km = db.Column(db.Float, default=8.0)
    latitude = db.Column(db.Float, default=17.4483)
    longitude = db.Column(db.Float, default=78.3915)
    address = db.Column(db.String(255), default='Madhapur, Hyderabad')
    profile_photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = db.relationship('StudentSkill', backref='student_profile', cascade='all, delete-orphan')
    availabilities = db.relationship('Availability', backref='student_profile', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='student_profile', cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', backref='student_profile', cascade='all, delete-orphan')
    interactions = db.relationship('JobInteraction', backref='student_profile', cascade='all, delete-orphan')

    def get_categories(self):
        try:
            return json.loads(self.preferred_categories) if self.preferred_categories else []
        except Exception:
            return [self.preferred_categories] if self.preferred_categories else []

    def set_categories(self, cats):
        self.preferred_categories = json.dumps(cats if isinstance(cats, list) else [cats])

    def to_dict(self):
        skills_list = [s.skill_name for s in self.skills]
        days_list = [a.day_of_week for a in self.availabilities]
        time_start = self.availabilities[0].start_time if self.availabilities else "10:00"
        time_end = self.availabilities[0].end_time if self.availabilities else "19:00"

        # Calculate completion percentage
        checks = [self.education, self.college, self.bio, skills_list, self.address, days_list, self.expected_salary]
        completion = int((sum(1 for c in checks if c) / len(checks)) * 100)

        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.user.full_name if self.user else '',
            'email': self.user.email if self.user else '',
            'phone': self.user.phone if self.user else '',
            'avatar_url': self.user.avatar_url if self.user else '',
            'education': self.education,
            'college': self.college,
            'institution': self.college,
            'experience': self.experience,
            'experience_level': self.experience,
            'bio': self.bio,
            'preferred_categories': self.get_categories(),
            'preferred_job_type': self.preferred_job_type,
            'expected_salary': self.expected_salary,
            'salary_type': self.salary_type,
            'max_distance_km': self.max_distance_km,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'skills': skills_list,
            'available_days': days_list,
            'available_time_start': time_start,
            'available_time_end': time_end,
            'completion_percentage': completion
        }

class StudentSkill(db.Model):
    __tablename__ = 'student_skills'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(50), default='Intermediate') # Beginner, Intermediate, Advanced

class Availability(db.Model):
    __tablename__ = 'availabilities'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False) # Monday, Saturday, etc.
    start_time = db.Column(db.String(10), default='10:00')
    end_time = db.Column(db.String(10), default='19:00')
