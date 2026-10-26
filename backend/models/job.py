from datetime import datetime
from extensions import db

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=True)

class JobSkill(db.Model):
    __tablename__ = 'job_skills'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)

class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profiles.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(50), default='Part-time')
    pay_amount = db.Column(db.Float, nullable=False)
    pay_frequency = db.Column(db.String(20), default='day') # hour, day, week
    date_needed = db.Column(db.String(100), default='Immediate')
    start_time = db.Column(db.String(10), default='10:00')
    end_time = db.Column(db.String(10), default='18:00')
    workers_needed = db.Column(db.Integer, default=1)
    experience_required = db.Column(db.String(50), default='No Experience')
    location_address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    application_deadline = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='active') # active, filled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = db.relationship('JobSkill', backref='job', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan')
    saved_entries = db.relationship('SavedJob', backref='job', cascade='all, delete-orphan')
    interactions = db.relationship('JobInteraction', backref='job', cascade='all, delete-orphan')

    def to_dict(self, ref_lat=None, ref_lon=None):
        skills_list = [s.skill_name for s in self.skills]
        company = self.employer_profile.company_name or self.employer_profile.business_name if self.employer_profile else 'Business'
        avatar = self.employer_profile.user.avatar_url if self.employer_profile and self.employer_profile.user else None

        data = {
            'id': self.id,
            'employer_id': self.employer_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'job_type': self.job_type,
            'pay_amount': self.pay_amount,
            'pay_frequency': self.pay_frequency,
            'date_needed': self.date_needed,
            'date': self.date_needed,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'workers_needed': self.workers_needed,
            'experience_required': self.experience_required,
            'location_address': self.location_address,
            'address': self.location_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'application_deadline': self.application_deadline,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'company_name': company,
            'business_name': company,
            'business_type': self.employer_profile.business_category if self.employer_profile else '',
            'company_address': self.employer_profile.address if self.employer_profile else '',
            'employer_avatar': avatar,
            'skills': skills_list,
            'required_skills': skills_list,
            'applicant_count': len(self.applications)
        }

        if ref_lat is not None and ref_lon is not None and self.latitude is not None and self.longitude is not None:
            import math
            R = 6371.0
            phi1, phi2 = math.radians(ref_lat), math.radians(self.latitude)
            dphi = math.radians(self.latitude - ref_lat)
            dlam = math.radians(self.longitude - ref_lon)
            a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2.0)**2
            c = 2.0 * math.atan2(math.sqrt(min(1.0, max(0.0, a))), math.sqrt(1.0 - min(1.0, max(0.0, a))))
            dist = round(R * c, 2)
            data['distance_km'] = dist
            data['formatted_distance'] = f"{int(dist * 1000)} m away" if dist < 1.0 else f"{dist:.1f} km away"
        else:
            data['distance_km'] = None
            data['formatted_distance'] = "Distance N/A"

        return data
