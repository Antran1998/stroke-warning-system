"""
Machine Learning Model Training Script
Focused on Random Forest with clear metrics
"""
import os
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
)
import numpy as np

# Import from our modular structure
from app import create_app
from models import db, Patient


def load_data_from_database():
    """Load patient data from database"""
    app = create_app()

    with app.app_context():
        patients = Patient.query.all()
        ones = sum(1 for p in patients if (p.stroke_prediction is not None and int(p.stroke_prediction) == 1))
        zeros = sum(1 for p in patients if (p.stroke_prediction is not None and int(p.stroke_prediction) == 0))
        print(f"Found 1: {ones} - 0: {zeros}")
        data = []
        for patient in patients:
            if patient.stroke_prediction is None:
                continue
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
                'stroke': int(patient.stroke_prediction),
            })
        
        return pd.DataFrame(data)


def load_data_from_csv():
    """Fallback: load data from brain_stroke.csv in project root."""
    csv_path = os.path.join(os.getcwd(), 'brain_stroke.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Fallback CSV 'brain_stroke.csv' not found.")

    df = pd.read_csv(csv_path)

    # Normalize column names to match expected schema
    rename_map = {
        'Residence_type': 'residence_type',
        'Avg_glucose_level': 'avg_glucose_level',
    }
    df = df.rename(columns=rename_map)

    # Ensure required columns exist
    required = {
        'age', 'gender', 'hypertension', 'heart_disease', 'ever_married',
        'work_type', 'residence_type', 'avg_glucose_level', 'bmi',
        'smoking_status', 'stroke'
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    return df


def preprocess_data(df: pd.DataFrame):
    """Preprocess and encode categorical variables"""
    df = df.copy()

    if df.empty:
        raise ValueError("No data available to train the model.")

    # Basic NA handling for numeric columns (median fill)
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


def train_random_forest(X_train, y_train):
    """Train Random Forest classifier."""
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # handle potential class imbalance
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test):
    """Compute clear evaluation metrics for the classifier."""
    y_pred = model.predict(X_test)

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'classification_report': classification_report(y_test, y_pred, zero_division=0)
    }

    if hasattr(model, 'predict_proba'):
        classes = getattr(model, 'classes_', None)
        if classes is not None and len(classes) > 1:
            # pick probability of class 1 if present, else map accordingly
            idx = int(np.where(classes == 1)[0][0]) if 1 in classes else 1
            y_proba = model.predict_proba(X_test)[:, idx]
            try:
                metrics['roc_auc'] = roc_auc_score(y_test, y_proba)
            except ValueError:
                metrics['roc_auc'] = None
        else:
            metrics['roc_auc'] = None
    else:
        metrics['roc_auc'] = None

    return metrics


def print_results(metrics, feature_names, model):
    """Pretty-print metrics and feature importances."""
    print("\n==== Random Forest Evaluation Metrics ====")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1-Score: {metrics['f1_score']:.4f}")
    if metrics['roc_auc'] is not None:
        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print("Confusion Matrix:")
    cm = metrics['confusion_matrix']
    print(f"[[TN: {cm[0][0]}, FP: {cm[0][1]}], [FN: {cm[1][0]}, TP: {cm[1][1]}]]")
    print("\nClassification Report:")
    print(metrics['classification_report'])

    # Cross-validation on the training set for stability estimate
    print("\n5-Fold Cross-Validation on training set:")
    cv_scores = cross_val_score(model, X_train_global, y_train_global, cv=5)
    print(f"CV Mean: {cv_scores.mean():.4f} | CV Std: {cv_scores.std():.4f}")

    # Feature importances
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
        print("\nTop Feature Importances:")
        for name, val in pairs:
            print(f"- {name}: {val:.4f}")


if __name__ == '__main__':
    # Try DB, fallback to CSV
    df = None
    try:
        df = load_data_from_database()
        if df is not None and df.empty:
            df = None
    except Exception:
        df = None

    if df is None:
        try:
            df = load_data_from_csv()
            print("Loaded data from brain_stroke.csv (fallback)")
        except Exception as e:
            print(f"Failed to load data from DB and CSV: {e}")
            df = pd.DataFrame()

    if df.empty:
        print("No data available to train the model.")
    else:
        # Preprocess
        X, y, scaler, feature_names = preprocess_data(df)

        # Stratified train/test split to maintain balance
        sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        for train_idx, test_idx in sss.split(X, y):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Validate both sets contain both classes; if not, adjust test_size or repeat with a different random_state.
        assert y_train.nunique() > 1 and y_test.nunique() > 1, "Train/test must contain both classes."

        # Keep globals for CV printing function
        global X_train_global, y_train_global
        X_train_global, y_train_global = X_train, y_train

        # Train
        rf_model = train_random_forest(X_train, y_train)

        # Evaluate
        metrics = evaluate_model(rf_model, X_test, y_test)

        # Output results
        print_results(metrics, feature_names, rf_model)
