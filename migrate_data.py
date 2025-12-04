import csv
import os
from app import create_app, db
from models import Patient


def clear_data():
    """
    Clears all patient data from the database.
    """
    app = create_app(os.getenv('FLASK_CONFIG') or 'development')
    with app.app_context():
        try:
            deleted = Patient.query.delete()
            db.session.commit()
            print(f"Cleared {deleted} patient records from the database.")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to clear patient data: {e}")


def migrate_data():
    """
    Migrates data from brain_Stroke.csv to the database.
    """
    app = create_app(os.getenv('FLASK_CONFIG') or 'development')
    with app.app_context():
        # Check if there are already a significant number of patients
        if Patient.query.count() > 10:
            print("It appears the data has already been migrated. Aborting.")
            return

        try:
            with open('brain_stroke.csv', mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                patients_to_add = []
                
                for row in reader:
                    # Normalize stroke value from CSV (handle different header cases and string values)
                    raw_stroke = row.get('stroke') if 'stroke' in row else row.get('Stroke')
                    stroke_val = 0
                    if raw_stroke is not None:
                        s = str(raw_stroke).strip()
                        if s in ('0', '1'):
                            stroke_val = int(s)
                        elif s.lower() in ('yes', 'y', 'true'):
                            stroke_val = 1
                        elif s.lower() in ('no', 'n', 'false'):
                            stroke_val = 0

                    # Prepare data for prediction and patient creation
                    patient_data_for_prediction = {
                        'age': float(row.get('age', 0)),
                        'hypertension': int(row.get('hypertension', 0)),
                        'heart_disease': int(row.get('heart_disease', 0)),
                        'avg_glucose_level': float(row.get('avg_glucose_level', 0.0)),
                        'bmi': float(row.get('bmi')) if row.get('bmi') and row.get('bmi').lower() != 'n/a' else 0.0,
                        'smoking_status': row.get('smoking_status', 'Unknown'),
                        'stroke': stroke_val
                    }

                    # Create a new Patient object
                    new_patient = Patient(
                        name=f"Patient {row.get('id', '')}",
                        age=patient_data_for_prediction['age'],
                        gender=row.get('gender'),
                        hypertension=patient_data_for_prediction['hypertension'],
                        heart_disease=patient_data_for_prediction['heart_disease'],
                        ever_married=row.get('ever_married'),
                        work_type=row.get('work_type'),
                        residence_type=row.get('Residence_type'),
                        avg_glucose_level=patient_data_for_prediction['avg_glucose_level'],
                        bmi=patient_data_for_prediction['bmi'],
                        smoking_status=patient_data_for_prediction['smoking_status'],
                        stroke_prediction=patient_data_for_prediction['stroke'],
                        validated=True,
                        created_by='migration_script'
                    )
                    patients_to_add.append(new_patient)

                db.session.bulk_save_objects(patients_to_add)
                db.session.commit()
                print(f"Successfully migrated {len(patients_to_add)} patients.")

        except FileNotFoundError:
            print("Error: 'brain_stroke.csv' not found. Make sure it's in the root directory.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    # Run clear before migration if desired
    clear_data()
    migrate_data()