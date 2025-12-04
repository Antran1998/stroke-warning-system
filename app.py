"""
Main Flask Application for Stroke Warning System
"""
import json
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient
from config import config

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Add custom template filters
    @app.template_filter('tojson')
    def to_json_filter(obj):
        """Convert an object to its JSON representation"""
        if hasattr(obj, 'tojson'):
            return obj.tojson()
        return obj
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Create default users if they don't exist
        if not User.query.filter_by(username='doctor1').first():
            doctor = User(
                username='doctor1', 
                password=generate_password_hash('doctor123'), 
                role='doctor'
            )
            db.session.add(doctor)
        
        if not User.query.filter_by(username='datascientist1').first():
            ds = User(
                username='datascientist1', 
                password=generate_password_hash('ds123'), 
                role='data_scientist'
            )
            db.session.add(ds)
        
        db.session.commit()
    
    # Routes
    @app.route('/')
    def index():
        return render_template('login.html')

    @app.route('/login', methods=['POST'])
    def login():
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['role'] = user.role
            
            if user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('data_scientist_dashboard'))
        
        return render_template('login.html', error='Invalid credentials')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.route('/doctor/dashboard')
    def doctor_dashboard():
        if 'username' not in session or session['role'] != 'doctor':
            return redirect(url_for('index'))
        
        # Pagination params
        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            page = 1
        try:
            per_page = int(request.args.get('per_page', 10))
        except ValueError:
            per_page = 10
        if per_page <= 0:
            per_page = 10
        if page <= 0:
            page = 1
        
        base_query = Patient.query.order_by(Patient.created_at.desc())
        pagination = base_query.paginate(page=page, per_page=per_page, error_out=False)
        patients = pagination.items
        
        # Stats
        total_patients = Patient.query.count()
        high_risk_count = Patient.query.filter(Patient.stroke_prediction == 'High Risk').count()
        pending_count = Patient.query.filter(Patient.stroke_prediction == None).count()
        
        return render_template(
            'doctor_dashboard.html', 
            patients=patients,
            total_patients=total_patients,
            high_risk_count=high_risk_count,
            pending_count=pending_count,
            pagination=pagination,
            per_page=per_page
        )

    @app.route('/doctor/add_patient', methods=['POST'])
    def add_patient():
        if 'username' not in session or session['role'] != 'doctor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = [
                'name', 'age', 'gender', 'hypertension', 'heart_disease',
                'ever_married', 'work_type', 'residence_type', 'avg_glucose_level',
                'bmi', 'smoking_status'
            ]
            
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'Missing required field: {field}'
                    }), 400

            # Make prediction using the rule-based predict_stroke function
            prediction = predict_stroke(data)
            
            # Create new patient
            new_patient = Patient(
                name=data['name'],
                age=data['age'],
                gender=data['gender'],
                hypertension=data['hypertension'],
                heart_disease=data['heart_disease'],
                ever_married=data['ever_married'],
                work_type=data['work_type'],
                residence_type=data['residence_type'],
                avg_glucose_level=data['avg_glucose_level'],
                bmi=data['bmi'],
                smoking_status=data['smoking_status'],
                stroke_prediction=prediction,
                created_by=session['username']
            )
            
            db.session.add(new_patient)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Patient added successfully',
                'prediction': prediction
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error adding patient: {str(e)}'
            }), 500
        
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/data_scientist/dashboard')
    def data_scientist_dashboard():
        if 'username' not in session or session['role'] != 'data_scientist':
            return redirect(url_for('index'))
        
        total_patients = Patient.query.count()
        stroke_cases = Patient.query.filter(
            Patient.stroke_prediction == 'High Risk'
        ).count()
        
        # Get model metrics if available
        try:
            with open('model/metrics.json', 'r') as f:
                model_metrics = json.load(f)
        except FileNotFoundError:
            model_metrics = None
        
        return render_template('data_scientist_dashboard.html', 
                             total_patients=total_patients,
                             stroke_cases=stroke_cases,
                             model_metrics=model_metrics)

    @app.route('/doctor/update_patient', methods=['POST'])
    def update_patient():
        """Update patient details from doctor dashboard editable panel.
        Expects JSON body with at least 'id' and any updatable fields.
        Recalculates stroke prediction and probability after update.
        """
        if 'username' not in session or session.get('role') != 'doctor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        try:
            data = request.get_json() or {}
            if 'id' not in data:
                return jsonify({'success': False, 'message': 'Missing patient id'}), 400

            patient_id = int(data.get('id'))
            patient = Patient.query.get(patient_id)
            if not patient:
                return jsonify({'success': False, 'message': 'Patient not found'}), 404

            # Update allowed fields only
            updatable = [
                'name', 'age', 'gender', 'hypertension', 'heart_disease',
                'ever_married', 'work_type', 'residence_type', 'avg_glucose_level',
                'bmi', 'smoking_status'
            ]

            for key in updatable:
                if key in data:
                    val = data.get(key)
                    # convert numeric fields
                    if key in ('age', 'hypertension', 'heart_disease'):
                        try:
                            setattr(patient, key, int(val) if val is not None and val != '' else None)
                        except (ValueError, TypeError):
                            return jsonify({'success': False, 'message': f'Invalid value for {key}'}), 400
                    elif key in ('avg_glucose_level', 'bmi'):
                        try:
                            setattr(patient, key, float(val) if val is not None and val != '' else None)
                        except (ValueError, TypeError):
                            return jsonify({'success': False, 'message': f'Invalid value for {key}'}), 400
                    else:
                        setattr(patient, key, val)

            # If stroke_prediction was provided, use that instead of recalculating
            if 'stroke_prediction' not in data:
                # No manual prediction provided, recalculate using the helper
                patient_data = {
                    'age': patient.age or 0,
                    'hypertension': int(patient.hypertension) if patient.hypertension is not None else 0,
                    'heart_disease': int(patient.heart_disease) if patient.heart_disease is not None else 0,
                    'avg_glucose_level': float(patient.avg_glucose_level) if patient.avg_glucose_level is not None else 0.0,
                    'bmi': float(patient.bmi) if patient.bmi is not None else 0.0,
                    'smoking_status': patient.smoking_status or 'Unknown'
                }
                prediction = predict_stroke(patient_data)
                patient.stroke_prediction = prediction
            # else stroke_prediction was already set by the form data above
            patient.updated_at = datetime.utcnow() if hasattr(patient, 'updated_at') else patient.created_at

            db.session.commit()

            return jsonify({'success': True, 'message': 'Patient updated', 'prediction': prediction})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/analytics/dashboard-data')
    def get_dashboard_data():
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'error': 'Unauthorized'}), 401
            
        patients = Patient.query.all()
        data = {
            'age_distribution': {},
            'gender_distribution': {},
            'risk_factors': {},
            'prediction_trends': {},
            'correlations': {}
        }
        
        # Calculate analytics data
        for patient in patients:
            # Age distribution
            age_group = f"{(patient.age // 10) * 10}-{(patient.age // 10) * 10 + 9}"
            data['age_distribution'][age_group] = data['age_distribution'].get(age_group, 0) + 1
            
            # Gender distribution
            data['gender_distribution'][patient.gender] = data['gender_distribution'].get(patient.gender, 0) + 1
            
            # Risk factors
            if patient.hypertension:
                data['risk_factors']['hypertension'] = data['risk_factors'].get('hypertension', 0) + 1
            if patient.heart_disease:
                data['risk_factors']['heart_disease'] = data['risk_factors'].get('heart_disease', 0) + 1
            if patient.smoking_status == 'smokes':
                data['risk_factors']['smoking'] = data['risk_factors'].get('smoking', 0) + 1
            
            # Prediction trends by month
            month = patient.created_at.strftime('%Y-%m')
            if month not in data['prediction_trends']:
                data['prediction_trends'][month] = {'High Risk': 0, 'Low Risk': 0}
            if patient.stroke_prediction in data['prediction_trends'][month]:
                data['prediction_trends'][month][patient.stroke_prediction] += 1
        
        return jsonify(data)



    @app.route('/api/export-data', methods=['POST'])
    def export_data():
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            filters = request.json.get('filters', {})
            format_type = request.json.get('format', 'json')
            
            query = Patient.query
            
            # Apply filters
            if filters.get('startDate'):
                query = query.filter(Patient.created_at >= filters['startDate'])
            if filters.get('endDate'):
                query = query.filter(Patient.created_at <= filters['endDate'])
            if filters.get('riskLevel'):
                query = query.filter(Patient.stroke_prediction.in_(filters['riskLevel']))
            
            patients = query.all()
            data = [patient.to_dict() for patient in patients]
            
            if format_type == 'csv':
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    return Response(
                        output.getvalue(),
                        mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=patient_data.csv'}
                    )
            else:
                return jsonify(data)
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'error': 'Unauthorized'}), 401
        
        patients = Patient.query.all()
        data = [patient.to_dict() for patient in patients]
        
        return jsonify(data)

    def predict_stroke(patient_data):
        """
        Predict stroke risk based on patient data using a rule-based system.
        """

        # Rule-based system as fallback
        risk_score = 0
        
        # Age factor
        if patient_data['age'] > 60:
            risk_score += 30
        elif patient_data['age'] > 45:
            risk_score += 15
        
        # Hypertension (major risk factor)
        if patient_data['hypertension'] == 1:
            risk_score += 25
        
        # Heart disease (major risk factor)
        if patient_data['heart_disease'] == 1:
            risk_score += 25
        
        # Glucose level
        if patient_data['avg_glucose_level'] > 125:
            risk_score += 15
        elif patient_data['avg_glucose_level'] > 100:
            risk_score += 10
        
        # BMI
        if patient_data['bmi'] > 30:
            risk_score += 10
        elif patient_data['bmi'] > 25:
            risk_score += 5
        
        # Smoking status
        if patient_data['smoking_status'] == 'smokes':
            risk_score += 15
        elif patient_data['smoking_status'] == 'formerly smoked':
            risk_score += 8
        
        # Convert to probability internally (not stored)
        probability = min(risk_score / 100, 0.95)

        # Determine risk level: only High Risk or Low Risk (no Medium)
        return 'High Risk' if probability > 0.5 else 'Low Risk'
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
