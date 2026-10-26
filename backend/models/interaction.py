from datetime import datetime
from extensions import db

INTERACTION_WEIGHTS = {
    'VIEW': 1,
    'SEARCH': 2,
    'SAVE': 3,
    'APPLY': 5,
    'ACCEPT': 7,
    'COMPLETE': 10,
    'RATE': 8,
    'REJECT': -2
}

class JobInteraction(db.Model):
    __tablename__ = 'job_interactions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)
    interaction_weight = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'job_id': self.job_id,
            'interaction_type': self.interaction_type,
            'interaction_weight': self.interaction_weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    area = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), default='Hyderabad')
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
