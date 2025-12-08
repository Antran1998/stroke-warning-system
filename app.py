"""
Main Flask Application for Stroke Warning System
"""
import json
import csv
import io
import pickle
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient
from config import config
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
)

# Global variable to hold the trained model
TRAINED_MODEL = None

def load_trained_model():
    """Load the latest trained model from disk"""
    global TRAINED_MODEL
    
    model_dir = 'model'
    metrics_path = os.path.join(model_dir, 'metrics.json')
    
    # Check if we have a deployed model
    if not os.path.exists(metrics_path):
        print("No model deployed. Using rule-based prediction.")
        return None
    
    try:
        # Read metrics to get the model filename
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        model_filename = metrics.get('model_filename')
        if not model_filename:
            # Backward compatibility: try old format
            algorithm = metrics.get('algorithm')
            if algorithm:
                model_filename = f'{algorithm}_model.pkl'
            else:
                print("No model filename specified in metrics.json")
                return None
        
        model_path = os.path.join(model_dir, model_filename)
        
        if not os.path.exists(model_path):
            print(f"Model file not found: {model_path}")
            return None
        
        # Load the model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        TRAINED_MODEL = model_data
        algorithm = metrics.get('algorithm', 'Unknown')
        accuracy = metrics.get('accuracy', 0)
        print(f"? Loaded deployed model: {algorithm}")
        print(f"  File: {model_filename}")
        print(f"  Accuracy: {accuracy * 100:.2f}%")
        return model_data
        
    except Exception as e:
        print(f"Error loading trained model: {e}")
        return None

def preprocess_data_for_training(df):
    """Preprocess and encode categorical variables for training"""
    df = df.copy()
    
    # Handle missing values
    numeric_cols = ['age', 'avg_glucose_level', 'bmi']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    
    # Encode categorical columns
    le = LabelEncoder()
    categorical_columns = ['gender', 'ever_married', 'work_type', 'residence_type', 'smoking_status']
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = le.fit_transform(df[col])
    
    # Features/target split
    X = df.drop('stroke', axis=1)
    y = df['stroke'].astype(int)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, scaler, list(X.columns)

def get_model_by_algorithm(algorithm):
    """Return the appropriate model based on algorithm selection"""
    models = {
        'random_forest': RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        ),
        'svm': SVC(
            kernel='rbf',
            random_state=42,
            probability=True,
            class_weight='balanced'
        ),
        'naive_bayes': GaussianNB(),
        'gradient_boost': GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        ),
        'logistic_regression': LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )
    }
    
    if algorithm not in models:
        raise ValueError(f'Unknown algorithm: {algorithm}')
    
    return models[algorithm]

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Load trained model if available
    trained_model_data = load_trained_model()
    
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
        high_risk_count = Patient.query.filter(Patient.stroke_prediction == 1).count()
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
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            # Validate required fields
            required_fields = [
                'name', 'age', 'gender', 'hypertension', 'heart_disease',
                'ever_married', 'work_type', 'residence_type', 'avg_glucose_level',
                'bmi', 'smoking_status'
            ]
            
            for field in required_fields:
                if field not in data or data[field] == '' or data[field] is None:
                    return jsonify({
                        'success': False,
                        'message': f'Missing or empty field: {field}'
                    }), 400

            # Validate numeric fields
            try:
                age = int(data['age'])
                hypertension = int(data['hypertension'])
                heart_disease = int(data['heart_disease'])
                avg_glucose_level = float(data['avg_glucose_level'])
                bmi = float(data['bmi'])
                
                if age < 1 or age > 120:
                    return jsonify({
                        'success': False,
                        'message': 'Age must be between 1 and 120'
                    }), 400
                
                if hypertension not in [0, 1]:
                    return jsonify({
                        'success': False,
                        'message': 'Hypertension must be 0 or 1'
                    }), 400
                
                if heart_disease not in [0, 1]:
                    return jsonify({
                        'success': False,
                        'message': 'Heart disease must be 0 or 1'
                    }), 400
                
                if avg_glucose_level < 0:
                    return jsonify({
                        'success': False,
                        'message': 'Average glucose level must be positive'
                    }), 400
                
                if bmi < 0:
                    return jsonify({
                        'success': False,
                        'message': 'BMI must be positive'
                    }), 400
                    
            except (ValueError, TypeError) as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid numeric value: {str(e)}'
                }), 400

            # Make prediction using the rule-based predict_stroke function
            prediction_data = {
                'age': age,
                'hypertension': hypertension,
                'heart_disease': heart_disease,
                'avg_glucose_level': avg_glucose_level,
                'bmi': bmi,
                'smoking_status': data['smoking_status']
            }
            prediction = predict_stroke(prediction_data)
            prediction_int = 1 if prediction == 'High Risk' else 0
            
            # Create new patient
            new_patient = Patient(
                name=data['name'],
                age=age,
                gender=data['gender'],
                hypertension=hypertension,
                heart_disease=heart_disease,
                ever_married=data['ever_married'],
                work_type=data['work_type'],
                residence_type=data['residence_type'],
                avg_glucose_level=avg_glucose_level,
                bmi=bmi,
                smoking_status=data['smoking_status'],
                stroke_prediction=prediction_int,
                created_by=session['username']
            )
            
            db.session.add(new_patient)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Patient added successfully',
                'prediction': prediction,
                'patient_id': new_patient.id
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
            Patient.stroke_prediction == 1
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
                'bmi', 'smoking_status', 'stroke_prediction'
            ]

            prediction = None
            for key in updatable:
                if key in data:
                    val = data.get(key)
                    # convert numeric fields
                    if key in ('age', 'hypertension', 'heart_disease', 'stroke_prediction'):
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

            # If stroke_prediction was not manually provided, recalculate
            if 'stroke_prediction' not in data:
                patient_data = {
                    'age': patient.age or 0,
                    'hypertension': int(patient.hypertension) if patient.hypertension is not None else 0,
                    'heart_disease': int(patient.heart_disease) if patient.heart_disease is not None else 0,
                    'avg_glucose_level': float(patient.avg_glucose_level) if patient.avg_glucose_level is not None else 0.0,
                    'bmi': float(patient.bmi) if patient.bmi is not None else 0.0,
                    'smoking_status': patient.smoking_status or 'Unknown'
                }
                prediction = predict_stroke(patient_data)
                patient.stroke_prediction = 1 if prediction == 'High Risk' else 0
            else:
                # Convert the stored prediction to text for response
                prediction = 'High Risk' if patient.stroke_prediction == 1 else 'Low Risk'
            
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
            label = 'High Risk' if patient.stroke_prediction == 1 else 'Low Risk'
            data['prediction_trends'][month][label] += 1
        
        return jsonify(data)

    @app.route('/data_scientist/export_data', methods=['GET'])
    def data_scientist_export():
        """Export all patient data as JSON for data scientist dashboard"""
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            patients = Patient.query.all()
            data = [patient.to_dict() for patient in patients]
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export-data', methods=['POST'])
    def export_data():
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            filters = request.json.get('filters', {}) if request.json else {}
            format_type = request.json.get('format', 'json') if request.json else 'json'
            
            query = Patient.query
            
            # Apply filters
            if filters.get('startDate'):
                query = query.filter(Patient.created_at >= filters['startDate'])
            if filters.get('endDate'):
                query = query.filter(Patient.created_at <= filters['endDate'])
            if filters.get('riskLevel'):
                # accept 0/1 or labels
                risk_levels = filters['riskLevel']
                mapped = []
                for r in risk_levels:
                    if isinstance(r, int):
                        mapped.append(r)
                    elif isinstance(r, str):
                        mapped.append(1 if r == 'High Risk' else 0)
                query = query.filter(Patient.stroke_prediction.in_(mapped))
            
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

    @app.route('/data_scientist/train_model', methods=['POST'])
    def train_model():
        """Train machine learning model with specified configuration"""
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            algorithm = data.get('algorithm')
            test_size = float(data.get('test_size', 20)) / 100
            cv_folds = int(data.get('cross_validation', 5))
            
            if not algorithm:
                return jsonify({'success': False, 'error': 'Algorithm not specified'}), 400
            
            # Load data from database
            patients = Patient.query.filter(Patient.stroke_prediction.isnot(None)).all()
            
            if len(patients) < 50:
                return jsonify({
                    'success': False, 
                    'error': f'Insufficient data for training. Need at least 50 records, but only have {len(patients)}.'
                }), 400
            
            # Prepare data
            patient_data = []
            for patient in patients:
                patient_data.append({
                    'age': patient.age,
                    'gender': patient.gender,
                    'hypertension': patient.hypertension,
                    'heart_disease': patient.heart_disease,
                    'ever_married': patient.ever_married,
                    'work_type': patient.work_type,
                    'residence_type': patient.residence_type,
                    'avg_glucose_level': patient.avg_glucose_level,
                    'bmi': patient.bmi,
                    'smoking_status': patient.smoking_status,
                    'stroke': int(patient.stroke_prediction)
                })
            
            df = pd.DataFrame(patient_data)
            
            # Preprocess data
            X, y, scaler, feature_names = preprocess_data_for_training(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Select and train model
            model = get_model_by_algorithm(algorithm)
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = {
                'algorithm': algorithm,
                'dataset_size': len(patients),
                'training_size': len(X_train),
                'test_size': len(X_test),
                'test_size_percent': test_size * 100,
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                'f1_score': float(f1_score(y_test, y_pred, zero_division=0)),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
            }
            
            # Calculate ROC-AUC if possible
            if hasattr(model, 'predict_proba'):
                try:
                    y_proba = model.predict_proba(X_test)[:, 1]
                    metrics['roc_auc'] = float(roc_auc_score(y_test, y_proba))
                except:
                    metrics['roc_auc'] = None
            else:
                metrics['roc_auc'] = None
            
            # Cross-validation
            try:
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='accuracy')
                metrics['cv_scores'] = cv_scores.tolist()
                metrics['cv_mean'] = float(np.mean(cv_scores))
                metrics['cv_std'] = float(np.std(cv_scores))
            except Exception as e:
                metrics['cv_scores'] = []
                metrics['cv_mean'] = None
                metrics['cv_std'] = None
            
            # Feature importances (if available)
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                feature_importance = [
                    {'feature': name, 'importance': float(imp)} 
                    for name, imp in zip(feature_names, importances)
                ]
                feature_importance.sort(key=lambda x: x['importance'], reverse=True)
                metrics['feature_importance'] = feature_importance[:10]  # Top 10
            else:
                metrics['feature_importance'] = []
            
            # Save model with unique timestamp
            model_dir = 'model'
            os.makedirs(model_dir, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            model_filename = f'{algorithm}_{timestamp}_model.pkl'
            model_path = os.path.join(model_dir, model_filename)
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'model': model,
                    'scaler': scaler,
                    'feature_names': feature_names
                }, f)
            
            # Save metrics for this specific model
            metrics['trained_at'] = datetime.utcnow().isoformat()
            metrics['trained_by'] = session['username']
            metrics['model_filename'] = model_filename
            metrics['deployed'] = False
            
            # Load all models history
            models_history_path = os.path.join(model_dir, 'models_history.json')
            if os.path.exists(models_history_path):
                with open(models_history_path, 'r') as f:
                    models_history = json.load(f)
            else:
                models_history = []
            
            # Add this model to history
            models_history.append(metrics)
            
            # Keep only last 20 models
            models_history = models_history[-20:]
            
            # Save updated history
            with open(models_history_path, 'w') as f:
                json.dump(models_history, f, indent=2)
            
            # DO NOT auto-deploy - user must manually select
            
            return jsonify({
                'success': True,
                'message': 'Model trained successfully. Go to Model Management to deploy it.',
                'metrics': metrics
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/data_scientist/list_models', methods=['GET'])
    def list_models():
        """List all trained models with their metrics"""
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            model_dir = 'model'
            models_history_path = os.path.join(model_dir, 'models_history.json')
            
            if not os.path.exists(models_history_path):
                return jsonify({'models': []})
            
            with open(models_history_path, 'r') as f:
                models_history = json.load(f)
            
            # Check which model is currently deployed
            metrics_path = os.path.join(model_dir, 'metrics.json')
            deployed_filename = None
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    deployed_metrics = json.load(f)
                    deployed_filename = deployed_metrics.get('model_filename')
            
            # Mark deployed model
            for model in models_history:
                model['is_deployed'] = (model.get('model_filename') == deployed_filename)
            
            # Sort by trained_at descending (newest first)
            models_history.sort(key=lambda x: x.get('trained_at', ''), reverse=True)
            
            return jsonify({'models': models_history})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/data_scientist/deploy_model', methods=['POST'])
    def deploy_model():
        """Deploy a specific trained model"""
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            model_filename = data.get('model_filename')
            
            if not model_filename:
                return jsonify({'success': False, 'error': 'Model filename not specified'}), 400
            
            model_dir = 'model'
            model_path = os.path.join(model_dir, model_filename)
            
            if not os.path.exists(model_path):
                return jsonify({'success': False, 'error': 'Model file not found'}), 404
            
            # Load the model to verify it works
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # Load models history to get metrics
            models_history_path = os.path.join(model_dir, 'models_history.json')
            with open(models_history_path, 'r') as f:
                models_history = json.load(f)
            
            # Find metrics for this model
            model_metrics = None
            for m in models_history:
                if m.get('model_filename') == model_filename:
                    model_metrics = m
                    break
            
            if not model_metrics:
                return jsonify({'success': False, 'error': 'Model metrics not found'}), 404
            
            # Mark this model as deployed
            model_metrics['deployed'] = True
            model_metrics['deployed_at'] = datetime.utcnow().isoformat()
            model_metrics['deployed_by'] = session['username']
            
            # Unmark other models
            for m in models_history:
                if m.get('model_filename') != model_filename:
                    m['deployed'] = False
            
            # Save updated history
            with open(models_history_path, 'w') as f:
                json.dump(models_history, f, indent=2)
            
            # Save as active metrics.json (for backward compatibility)
            metrics_path = os.path.join(model_dir, 'metrics.json')
            with open(metrics_path, 'w') as f:
                json.dump(model_metrics, f, indent=2)
            
            # Load model into memory
            global TRAINED_MODEL
            TRAINED_MODEL = model_data
            
            return jsonify({
                'success': True,
                'message': f'Model deployed successfully. Now using {model_metrics.get("algorithm")} for predictions.',
                'metrics': model_metrics
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/data_scientist/delete_model', methods=['POST'])
    def delete_model():
        """Delete a trained model"""
        if 'username' not in session or session['role'] != 'data_scientist':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            model_filename = data.get('model_filename')
            
            if not model_filename:
                return jsonify({'success': False, 'error': 'Model filename not specified'}), 400
            
            model_dir = 'model'
            
            # Check if this model is currently deployed
            metrics_path = os.path.join(model_dir, 'metrics.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    deployed_metrics = json.load(f)
                if deployed_metrics.get('model_filename') == model_filename:
                    return jsonify({
                        'success': False,
                        'error': 'Cannot delete currently deployed model. Deploy another model first.'
                    }), 400
            
            # Delete model file
            model_path = os.path.join(model_dir, model_filename)
            if os.path.exists(model_path):
                os.remove(model_path)
            
            # Remove from history
            models_history_path = os.path.join(model_dir, 'models_history.json')
            if os.path.exists(models_history_path):
                with open(models_history_path, 'r') as f:
                    models_history = json.load(f)
                
                models_history = [m for m in models_history if m.get('model_filename') != model_filename]
                
                with open(models_history_path, 'w') as f:
                    json.dump(models_history, f, indent=2)
            
            return jsonify({
                'success': True,
                'message': 'Model deleted successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    def predict_stroke(patient_data):
        """
        Predict stroke risk based on patient data.
        Uses trained ML model if available, falls back to rule-based system.
        """
        global TRAINED_MODEL
        
        # Try ML model first
        if TRAINED_MODEL is not None:
            try:
                return predict_with_ml_model(patient_data, TRAINED_MODEL)
            except Exception as e:
                print(f"ML prediction failed: {e}. Falling back to rule-based.")
                # Fall through to rule-based
        
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
    
    def predict_with_ml_model(patient_data, model_data):
        """
        Make prediction using the trained ML model
        """
        model = model_data['model']
        scaler = model_data['scaler']
        feature_names = model_data['feature_names']
        
        # Create DataFrame with patient data
        df = pd.DataFrame([patient_data])
        
        # Ensure we have all required features
        for feature in feature_names:
            if feature not in df.columns:
                df[feature] = 0  # Default value for missing features
        
        # Encode categorical variables
        le = LabelEncoder()
        categorical_columns = ['gender', 'ever_married', 'work_type', 'residence_type', 'smoking_status']
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
                # Fit and transform - in production you'd save the encoders too
                df[col] = le.fit_transform(df[col])
        
        # Select and order features
        X = df[feature_names]
        
        # Scale features
        X_scaled = scaler.transform(X)
        
        # Make prediction
        prediction = model.predict(X_scaled)[0]
        
        # Convert to text
        return 'High Risk' if prediction == 1 else 'Low Risk'
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
