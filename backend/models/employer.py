from datetime import datetime
from extensions import db

class EmployerProfile(db.Model):
    __tablename__ = 'employer_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    company_name = db.Column(db.String(150), nullable=True) # Alias
    business_description = db.Column(db.Text, nullable=True)
    business_category = db.Column(db.String(100), default='Hospitality & Food')
    phone = db.Column(db.String(25), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, default=17.4504)
    longitude = db.Column(db.Float, default=78.3808)
    website = db.Column(db.String(255), nullable=True)
    verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    jobs = db.relationship('Job', backref='employer_profile', cascade='all, delete-orphan')

    def to_dict(self):
        name = self.business_name or self.company_name or (self.user.full_name if self.user else '')
        return {
            'id': self.id,
            'user_id': self.user_id,
            'business_name': name,
            'company_name': name,
            'description': self.business_description or '',
            'business_description': self.business_description or '',
            'business_type': self.business_category,
            'business_category': self.business_category,
            'phone': self.phone or (self.user.phone if self.user else ''),
            'email': self.email or (self.user.email if self.user else ''),
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'website': self.website,
            'verified': self.verified,
            'avatar_url': self.user.avatar_url if self.user else ''
        }
