"""
Script to add sample patients to the database
"""
from app import create_app
from models import db, Patient
from datetime import datetime, timedelta

def add_sample_patients():
    """Add sample patients to the database"""
    # Sample patient data with varied risk factors
    patients = [
        {
            'name': 'John Smith',
            'age': 65,
            'gender': 'Male',
            'hypertension': 1,
            'heart_disease': 1,
            'ever_married': 'Yes',
            'work_type': 'Private',
            'residence_type': 'Urban',
            'avg_glucose_level': 228.69,
            'bmi': 28.5,
            'smoking_status': 'formerly smoked',
            'stroke_prediction': 'High Risk',
            'stroke_probability': 0.82,
            'created_by': 'doctor1',
            'created_at': datetime.utcnow() - timedelta(days=5)
        },
        {
            'name': 'Sarah Johnson',
            'age': 42,
            'gender': 'Female',
            'hypertension': 0,
            'heart_disease': 0,
            'ever_married': 'Yes',
            'work_type': 'Self-employed',
            'residence_type': 'Rural',
            'avg_glucose_level': 105.92,
            'bmi': 23.1,
            'smoking_status': 'never smoked',
            'stroke_prediction': 'Low Risk',
            'stroke_probability': 0.15,
            'created_by': 'doctor1',
            'created_at': datetime.utcnow() - timedelta(days=3)
        },
        {
            'name': 'Michael Chen',
            'age': 55,
            'gender': 'Male',
            'hypertension': 1,
            'heart_disease': 0,
            'ever_married': 'Yes',
            'work_type': 'Govt_job',
            'residence_type': 'Urban',
            'avg_glucose_level': 171.23,
            'bmi': 32.1,
            'smoking_status': 'smokes',
            'stroke_prediction': 'Medium Risk',
            'stroke_probability': 0.45,
            'created_by': 'doctor1',
            'created_at': datetime.utcnow() - timedelta(days=2)
        },
        {
            'name': 'Emily Davis',
            'age': 28,
            'gender': 'Female',
            'hypertension': 0,
            'heart_disease': 0,
            'ever_married': 'No',
            'work_type': 'Private',
            'residence_type': 'Urban',
            'avg_glucose_level': 95.12,
            'bmi': 21.8,
            'smoking_status': 'never smoked',
            'stroke_prediction': 'Low Risk',
            'stroke_probability': 0.08,
            'created_by': 'doctor1',
            'created_at': datetime.utcnow() - timedelta(days=1)
        },
        {
            'name': 'Robert Wilson',
            'age': 71,
            'gender': 'Male',
            'hypertension': 1,
            'heart_disease': 1,
            'ever_married': 'Yes',
            'work_type': 'Private',
            'residence_type': 'Rural',
            'avg_glucose_level': 245.88,
            'bmi': 29.9,
            'smoking_status': 'formerly smoked',
            'stroke_prediction': 'High Risk',
            'stroke_probability': 0.91,
            'created_by': 'doctor1',
            'created_at': datetime.utcnow()
        }
    ]

    # Create app context
    app = create_app()
    
    with app.app_context():
        # Add each patient to the database
        for patient_data in patients:
            patient = Patient(**patient_data)
            db.session.add(patient)
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully added {len(patients)} sample patients to the database.")

if __name__ == '__main__':
    add_sample_patients()