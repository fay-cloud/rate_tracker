from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy without an app object first
# It will be initialized with the app in app.py
db = SQLAlchemy()

class Provider(db.Model):
    __tablename__ = 'providers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    registration_link = db.Column(db.String(255), nullable=False)

    # Relationship to ExchangeRate: one provider can have many rates
    rates = db.relationship('ExchangeRate', backref='provider', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'registration_link': self.registration_link
        }

    def __repr__(self):
        return f'<Provider {self.name}>'

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    currency_pair = db.Column(db.String(10), nullable=False)  # e.g., USD_EUR
    rate = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'provider_name': self.provider.name if self.provider else None,
            'currency_pair': self.currency_pair,
            'rate': self.rate,
            'last_updated': self.last_updated.isoformat()
        }

    def __repr__(self):
        return f'<ExchangeRate {self.currency_pair} for {self.provider.name if self.provider else "N/A"} - {self.rate}>'

class UserActivity(db.Model):
    __tablename__ = 'user_activity'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False) # e.g., 'register_click'
    provider_name = db.Column(db.String(100), nullable=True)
    currency_pair_viewed = db.Column(db.String(10), nullable=True) # Optional: which pair was viewed when click occurred
    ip_address = db.Column(db.String(45), nullable=True) # Optional: for basic analytics
    user_agent = db.Column(db.String(255), nullable=True) # Optional
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'provider_name': self.provider_name,
            'currency_pair_viewed': self.currency_pair_viewed,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f'<UserActivity {self.action} - {self.provider_name} at {self.timestamp}>'

def init_app(flask_app):
    """Initializes the database with the Flask app."""
    db.init_app(flask_app)
