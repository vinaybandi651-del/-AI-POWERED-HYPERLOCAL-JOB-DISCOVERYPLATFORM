from datetime import datetime
from extensions import db

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    cover_note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='applied') # applied, under_review, shortlisted, accepted, rejected, completed
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('job_id', 'student_id', name='uq_job_student_app'),)

    def to_dict(self):
        j = self.job
        sp = self.student_profile
        emp_user_id = j.employer_profile.user_id if (j and j.employer_profile) else None
        company_name = (j.employer_profile.company_name or j.employer_profile.business_name) if (j and j.employer_profile) else ''

        return {
            'id': self.id,
            'application_id': self.id,
            'job_id': self.job_id,
            'student_id': self.student_id,
            'cover_note': self.cover_note,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'job_title': j.title if j else '',
            'company_name': company_name,
            'employer_user_id': emp_user_id,
            'category': j.category if j else '',
            'job_type': j.job_type if j else '',
            'pay_amount': j.pay_amount if j else 0,
            'pay_frequency': j.pay_frequency if j else 'day',
            'location_address': j.location_address if j else '',
            'student_name': sp.user.full_name if (sp and sp.user) else '',
            'student_user_id': sp.user_id if sp else None,
            'student_email': sp.user.email if (sp and sp.user) else '',
            'student_phone': sp.user.phone if (sp and sp.user) else '',
            'student_avatar': sp.user.avatar_url if (sp and sp.user) else '',
            'education': sp.education if sp else '',
            'college': sp.college if sp else '',
            'experience': sp.experience if sp else ''
        }

class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'job_id', name='uq_student_saved_job'),)

    def to_dict(self):
        j = self.job
        return {
            'id': self.id,
            'student_id': self.student_id,
            'job_id': self.job_id,
            'saved_at': self.saved_at.isoformat() if self.saved_at else None,
            'job': j.to_dict() if j else None
        }
