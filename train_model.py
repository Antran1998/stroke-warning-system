"""
Machine Learning Model Training Script
Now imports from the separate models.py file
"""
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Import from our modular structure
from app import create_app
from models import db, Patient

def load_data_from_database():
    """Load patient data from database"""
    app = create_app()
    
    with app.app_context():
        patients = Patient.query.all()
        
        data = []
        for patient in patients:
            data.append({
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
                'stroke': 1 if patient.stroke_prediction == 'High Risk' else 0
            })
        
        return pd.DataFrame(data)

def preprocess_data(df):
    """Preprocess and encode categorical variables"""
    le = LabelEncoder()
    
    categorical_columns = ['gender', 'ever_married', 'work_type', 
                          'residence_type', 'smoking_status']
    
    for col in categorical_columns:
        df[col] = le.fit_transform(df[col])
    
    X = df.drop('stroke', axis=1)
    y = df['stroke']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, scaler

def train_models(X_train, X_test, y_train, y_test):
    """Train multiple classification models"""
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'SVM': SVC(kernel='rbf', probability=True, random_state=42),
        'Naive Bayes': GaussianNB(),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)
        
        results[name] = {
            'model': model,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        print(f"Accuracy: {accuracy:.4f}")
        print(f"F1-Score: {f1:.4f}")
