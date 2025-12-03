"""
Database Models for Stroke Warning System
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'doctor' or 'data_scientist'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

class Patient(db.Model):
    """Patient model for storing patient records and predictions"""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    hypertension = db.Column(db.Integer, nullable=False)  # 0 or 1
    heart_disease = db.Column(db.Integer, nullable=False)  # 0 or 1
    ever_married = db.Column(db.String(5), nullable=False)  # Yes or No
    work_type = db.Column(db.String(50), nullable=False)
    residence_type = db.Column(db.String(10), nullable=False)  # Urban or Rural
    avg_glucose_level = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    smoking_status = db.Column(db.String(50), nullable=False)
    stroke_prediction = db.Column(db.String(50))  # High Risk or Low Risk
    validated = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Patient {self.name} (ID: {self.id})>'

    def tojson(self):
        """Convert patient record to JSON-safe dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'hypertension': self.hypertension,
            'heart_disease': self.heart_disease,
            'ever_married': self.ever_married,
            'work_type': self.work_type,
            'residence_type': self.residence_type,
            'avg_glucose_level': self.avg_glucose_level,
            'bmi': self.bmi,
            'smoking_status': self.smoking_status,
            'stroke_prediction': self.stroke_prediction,
            
            'created_at': self.created_at.isoformat()
        }

    def to_dict(self):
        """Convert patient record to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'hypertension': self.hypertension,
            'heart_disease': self.heart_disease,
            'ever_married': self.ever_married,
            'work_type': self.work_type,
            'residence_type': self.residence_type,
            'avg_glucose_level': self.avg_glucose_level,
            'bmi': self.bmi,
            'smoking_status': self.smoking_status,
            'stroke_prediction': self.stroke_prediction,
            
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }