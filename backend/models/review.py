from datetime import datetime
from extensions import db

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], backref='reviews_received')
    job = db.relationship('Job', backref='reviews')

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer.full_name if self.reviewer else '',
            'reviewee_id': self.reviewee_id,
            'reviewee_name': self.reviewee.full_name if self.reviewee else '',
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    reasons = db.Column(db.Text, nullable=True) # JSON list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecommendationWeight(db.Model):
    __tablename__ = 'recommendation_weights'

    id = db.Column(db.Integer, primary_key=True)
    content_weight = db.Column(db.Float, default=0.40)
    location_weight = db.Column(db.Float, default=0.25)
    availability_weight = db.Column(db.Float, default=0.15)
    collaborative_weight = db.Column(db.Float, default=0.10)
    salary_weight = db.Column(db.Float, default=0.10)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
