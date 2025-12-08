# Use Cases Report: Doctor and Data Scientist Workflows

## Overview
This document comprehensively lists all use cases for the two primary stakeholder groups in the Stroke Warning System: **Doctors/Physicians** and **Data Scientists/ML Engineers**.

---

## 1. DOCTOR USE CASES

### 1.1 Authentication & Access Control
**Use Case:** Secure Login to Doctor Dashboard
- **Actor:** Doctor/Physician
- **Precondition:** Valid doctor credentials (username/password)
- **Flow:**
  1. Navigate to system login page
  2. Enter doctor credentials
  3. System validates and grants role-based access to doctor dashboard
- **Postcondition:** Access to patient management and risk assessment tools
- **Implementation:** `/login` endpoint, role-based session management
---

### 1.2 Patient Management

#### 1.2.1 Add New Patient
**Use Case:** Register New Patient with Clinical Data
- **Actor:** Doctor
- **Flow:**
  1. Access "Add New Patient" form on dashboard
  2. Enter patient demographics (name, age, gender, marital status)
  3. Input clinical metrics:
     - Hypertension status (Yes/No)
     - Heart disease history (Yes/No)
     - Average glucose level (mg/dL)
     - BMI
     - Smoking status (formerly smoked, never smoked, smokes, unknown)
     - Work type (Private, Self-employed, Govt_job, children, Never_worked)
     - Residence type (Urban/Rural)
  4. Submit patient data
  5. System validates input and performs immediate stroke risk prediction
- **Postcondition:** Patient record created with risk prediction; doctor notified of risk level
- **Validation Rules:**
  - Age: 1-120 years
  - Glucose level: positive value
  - BMI: positive value
  - All required fields must be completed
- **Implementation:** `/doctor/add_patient` POST endpoint, client-side form validation

#### 1.2.2 View Patient Records
**Use Case:** Browse All Patient Records
- **Actor:** Doctor
- **Flow:**
  1. Access patient records table on dashboard
  2. View paginated list of patients with key metrics:
     - ID, Name, Age, Gender
     - Hypertension, Heart Disease indicators
     - Glucose level, BMI
     - Stroke risk prediction badge (High Risk/Low Risk/Pending)
     - Registration date
  3. Navigate through pages using pagination controls
  4. Adjust rows per page (10, 20, 50, 100)
- **Postcondition:** Doctor has overview of patient population and risk distribution
- **Implementation:** `/doctor/dashboard` route with pagination support

#### 1.2.3 View Patient Details
**Use Case:** Access Detailed Patient Information
- **Actor:** Doctor
- **Flow:**
  1. Click on any patient row in the records table
  2. Side panel opens displaying comprehensive patient information organized by:
     - **Personal Information:** Name, age, gender, marital status
     - **Health Indicators:** BMI, glucose level, hypertension, heart disease, smoking status
     - **Additional Information:** Work type, residence type, registration date
     - **Stroke Risk Assessment:** Prominently displayed risk badge
  3. Review patient details for clinical decision-making
- **Postcondition:** Doctor has complete patient context for care planning
- **Implementation:** Client-side panel display with `showPatientDetails()` function

#### 1.2.4 Edit Patient Information
**Use Case:** Update Patient Data and Recalculate Risk
- **Actor:** Doctor
- **Flow:**
  1. View patient details in side panel
  2. Click "Edit" button
  3. Form fields become editable for:
     - Personal information (name, age, gender, marital status)
     - Health indicators (BMI, glucose, hypertension, heart disease, smoking)
     - Work type and residence type
     - Manual stroke prediction override (optional)
  4. Modify patient data as needed
  5. Click "Save" to commit changes
  6. System validates input and recalculates stroke risk prediction (unless manually overridden)
  7. Confirmation message displays new risk assessment
- **Postcondition:** Patient record updated; risk prediction refreshed; doctor notified
- **Validation:** Same rules as add patient
- **Implementation:** `/doctor/update_patient` POST endpoint, inline form editing
---

### 1.3 Risk Assessment & Clinical Decision Support

#### 1.3.1 Automated Stroke Risk Prediction
**Use Case:** Receive AI-Driven Risk Assessment for Patient
- **Actor:** Doctor
- **Trigger:** Patient data submission or update
- **Flow:**
  1. System processes patient clinical features
  2. If ML model deployed:
     - Features encoded and scaled
     - Model predicts stroke probability
     - Risk classification determined (High Risk if > 50%, else Low Risk)
  3. If no ML model deployed:
     - Rule-based prediction engine calculates risk score using weighted factors:
       - Age > 60: +30 points
       - Hypertension: +25 points
       - Heart disease: +25 points
       - Glucose > 125 mg/dL: +15 points
       - BMI > 30: +10 points
       - Smoking (current): +15 points
     - Risk threshold: > 50% = High Risk
  4. Prediction displayed with prominent badge (color-coded)
- **Postcondition:** Doctor receives clear risk classification for clinical decision-making
- **Implementation:** `predict_stroke()` function with ML fallback to rule-based system

#### 1.3.2 View High Risk Patient Summary
**Use Case:** Prioritize High-Risk Cases
- **Actor:** Doctor
- **Flow:**
  1. View dashboard statistics cards displaying:
     - Total patients count
     - High risk cases count
     - Pending analysis count
  2. Identify patients requiring immediate attention
  3. Filter or sort patient list by risk level (implicitly via visual badges)
- **Postcondition:** Doctor can prioritize interventions for high-risk patients
- **Implementation:** Dashboard statistics aggregation in `/doctor/dashboard` route

#### 1.3.3 Track Pending Cases
**Use Case:** Identify Patients Awaiting Risk Assessment
- **Actor:** Doctor
- **Flow:**
  1. View "Pending Analysis" statistic on dashboard
  2. Identify patients with null prediction values
  3. Follow up on incomplete assessments
- **Postcondition:** No patients overlooked; all cases processed
- **Implementation:** Count of patients with `stroke_prediction == None`

### 1.4 Logout
**Use Case:** Securely End Session
- **Actor:** Doctor
- **Flow:**
  1. Click "Logout" button in navigation
  2. Session cleared
  3. Redirect to login page
- **Postcondition:** Session terminated; access revoked
- **Implementation:** `/logout` route with session.clear()

---

## 2. DATA SCIENTIST USE CASES

### 2.1 Authentication & Access Control
**Use Case:** Secure Login to Data Scientist Dashboard
- **Actor:** Data Scientist/ML Engineer
- **Precondition:** Valid data scientist credentials
- **Flow:**
  1. Navigate to system login page
  2. Enter data scientist credentials
  3. System validates and grants role-based access to data scientist dashboard
- **Postcondition:** Access to data analysis, model training, and deployment tools
- **Implementation:** `/login` endpoint with role='data_scientist' validation

---

### 2.2 Data Collection & Export

#### 2.2.1 Export Patient Data as JSON
**Use Case:** Download Complete Dataset in JSON Format
- **Actor:** Data Scientist
- **Flow:**
  1. Navigate to "Data Collection & Export" section
  2. Click "Export as JSON" button
  3. System queries all patient records from database
  4. Converts records to JSON array format
  5. Browser downloads file: `stroke_dataset_YYYY-MM-DD.json`
  6. Success message displays record count
- **Postcondition:** Dataset available for external analysis, training, or archiving
- **Use Cases:** Model training, external analysis, data backup, compliance audits
- **Implementation:** `/data_scientist/export_data` GET endpoint

#### 2.2.2 Export Patient Data as CSV
**Use Case:** Download Dataset in CSV Format for Spreadsheet Analysis
- **Actor:** Data Scientist
- **Flow:**
  1. Click "Export as CSV" button
  2. System retrieves patient records
  3. Converts JSON to CSV format with proper escaping
  4. Browser downloads file: `stroke_dataset_YYYY-MM-DD.csv`
  5. Success message confirms export
- **Postcondition:** Dataset ready for import into Excel, Pandas, or statistical software
- **Use Cases:** Excel analysis, R/SPSS import, stakeholder reporting
- **Implementation:** Client-side JSON-to-CSV conversion

#### 2.2.3 Filtered Data Export
**Use Case:** Export Data with Date Range and Risk Level Filters
- **Actor:** Data Scientist
- **Flow:**
  1. Specify export filters:
     - Start date (optional)
     - End date (optional)
     - Risk level selection (High Risk, Low Risk, or both)
  2. Submit filtered export request
  3. System applies query filters
  4. Download filtered dataset in requested format
- **Postcondition:** Targeted dataset for specific analysis needs
- **Implementation:** `/api/export-data` POST endpoint with filter parameters

---

### 2.3 Data Analysis & Quality Assurance

#### 2.3.1 Analyze Dataset Statistics
**Use Case:** Generate Comprehensive Dataset Overview
- **Actor:** Data Scientist
- **Flow:**
  1. Click "Analyze Dataset" button
  2. System calculates statistics:
     - **Dataset Overview:** Total records, high/low risk distribution, class balance
     - **Age Statistics:** Mean, median, min, max
     - **BMI Statistics:** Mean, median, min, max
     - **Glucose Statistics:** Mean, median, min, max, distribution
     - **Risk Factors:** Hypertension prevalence, heart disease count, smoking rate
     - **Gender Distribution:** Male/female/other counts
  3. Results displayed in organized grid layout
- **Postcondition:** Data scientist understands dataset composition and distribution
- **Use Cases:** Data quality assessment, feature engineering planning, bias detection
- **Implementation:** Client-side `analyzeData()` function with statistical calculations

#### 2.3.2 Check for Missing Values
**Use Case:** Identify Data Completeness Issues
- **Actor:** Data Scientist
- **Flow:**
  1. Click "Check Missing Values" button
  2. System scans all fields for null, empty, or undefined values
  3. Results displayed in table format:
     - Feature name
     - Missing value count
     - Percentage missing
     - Status indicator (? complete or ? missing)
  4. Summary message indicates overall data quality
- **Postcondition:** Data scientist aware of data cleaning requirements before training
- **Use Cases:** Data preprocessing planning, imputation strategy
- **Implementation:** Client-side missing value detection algorithm

#### 2.3.3 Detect Outliers
**Use Case:** Identify Statistical Anomalies Using IQR Method
- **Actor:** Data Scientist
- **Flow:**
  1. Click "Detect Outliers" button
  2. System applies IQR (Interquartile Range) method to numeric features:
     - Calculate Q1 (25th percentile) and Q3 (75th percentile)
     - IQR = Q3 - Q1
     - Lower bound = Q1 - 1.5 × IQR
     - Upper bound = Q3 + 1.5 × IQR
     - Identify values outside bounds
  3. Results displayed per feature (age, BMI, glucose) with:
     - Outlier count
     - Acceptable range (bounds)
     - Recommendations for handling
- **Postcondition:** Data scientist can decide on outlier treatment strategy
- **Use Cases:** Data cleaning, anomaly detection, domain validation
- **Implementation:** Client-side `detectOutliersIQR()` function

#### 2.3.4 Analyze Feature Distribution
**Use Case:** Understand Feature Distributions and Skewness
- **Actor:** Data Scientist
- **Flow:**
  1. Click "Feature Distribution" button
  2. System calculates distribution metrics for numeric features:
     - Mean, median, range
     - Distribution shape (normal, left-skewed, right-skewed)
  3. Target variable distribution analyzed:
     - High Risk vs Low Risk counts and percentages
     - Class balance assessment
  4. Results displayed with interpretation
- **Postcondition:** Data scientist understands data distribution for preprocessing decisions
- **Use Cases:** Normalization planning, transformation decisions, imbalance handling
- **Implementation:** Client-side distribution analysis

---

### 2.4 Machine Learning Model Training

#### 2.4.1 Configure Model Training Parameters
**Use Case:** Specify Training Configuration
- **Actor:** Data Scientist
- **Flow:**
  1. Navigate to "Model Training Configuration" section
  2. Select algorithm from dropdown:
     - Random Forest
     - Support Vector Machine (SVM)
     - Naive Bayes
     - Gradient Boosting
     - Logistic Regression
  3. Set test set size (10-40%, default 20%)
  4. Set cross-validation folds (3-10, default 5)
  5. Submit training request
- **Precondition:** Minimum 50 patient records with predictions in database
- **Postcondition:** Training initiated with specified configuration
- **Implementation:** Training configuration form with validation

#### 2.4.2 Train Machine Learning Model
**Use Case:** Execute End-to-End Model Training Pipeline
- **Actor:** Data Scientist
- **Flow:**
  1. Submit training configuration
  2. System executes training pipeline:
     - **Data Loading:** Retrieve patient records with predictions from database
     - **Data Validation:** Ensure minimum 50 records available
     - **Preprocessing:**
       - Convert data to Pandas DataFrame
       - Handle missing values (median imputation for numeric features)
       - Encode categorical variables (gender, ever_married, work_type, residence_type, smoking_status)
       - Feature scaling using StandardScaler
     - **Train/Test Split:** Stratified split maintaining class distribution
     - **Model Selection:** Instantiate algorithm with preconfigured hyperparameters:
       - Random Forest: 200 trees, balanced class weights
       - SVM: RBF kernel, probability estimates enabled, balanced weights
       - Naive Bayes: Gaussian distribution
       - Gradient Boosting: 100 estimators, learning rate 0.1
       - Logistic Regression: L2 regularization, balanced weights
     - **Training:** Fit model on training set
     - **Prediction:** Generate predictions on test set
     - **Evaluation:** Calculate metrics (accuracy, precision, recall, F1, ROC-AUC, confusion matrix)
     - **Cross-Validation:** K-fold CV on training set for robustness assessment
     - **Feature Importance:** Extract if available (tree-based models)
     - **Model Persistence:** Save as pickle file with timestamp: `{algorithm}_{timestamp}_model.pkl`
     - **Metadata Storage:** Save metrics and configuration to `models_history.json`
  3. Training results displayed with comprehensive metrics
- **Postcondition:** Trained model saved to disk with full metadata; available for deployment
- **Error Handling:** Insufficient data, training failures, validation errors
- **Implementation:** `/data_scientist/train_model` POST endpoint

#### 2.4.3 View Training Results
**Use Case:** Review Model Performance Metrics
- **Actor:** Data Scientist
- **Flow:**
  1. Training completes successfully
  2. Results displayed including:
     - **Training Configuration:** Algorithm, dataset sizes, split ratio
     - **Performance Metrics:** Accuracy, precision, recall, F1-score, ROC-AUC (color-coded)
     - **Cross-Validation Results:** Mean accuracy, standard deviation across folds
     - **Confusion Matrix:** Visual table showing TP, TN, FP, FN counts
     - **Feature Importance:** Top 10 features ranked by importance (if available)
     - **Algorithm Insights:** Strengths, limitations, recommendations for selected algorithm
     - **Next Steps:** Deployment instructions
- **Postcondition:** Data scientist understands model performance and can decide on deployment
- **Implementation:** Client-side rendering of training results

---

### 2.5 Model Management & Deployment

#### 2.5.1 View All Trained Models
**Use Case:** List All Available Models with Metrics
- **Actor:** Data Scientist
- **Flow:**
  1. Navigate to "Model Management" section
  2. Click "Refresh Models List"
  3. System loads all models from `models_history.json`
  4. Models displayed in chronological order (newest first) with:
     - Deployment status badge (?? DEPLOYED or inactive)
     - Algorithm name
     - Performance metrics (accuracy, precision, recall, F1)
     - Training metadata (date, trainer, dataset size, CV results)
     - Action buttons (Deploy, Delete)
  5. Currently deployed model clearly indicated
- **Postcondition:** Data scientist has complete overview of model inventory
- **Implementation:** `/data_scientist/list_models` GET endpoint

#### 2.5.2 Deploy Trained Model
**Use Case:** Activate Model for Production Predictions
- **Actor:** Data Scientist
- **Flow:**
  1. Review model performance in models list
  2. Click "?? Deploy" button for chosen model
  3. Confirm deployment (replaces currently deployed model)
  4. System executes deployment:
     - Verify model file exists
     - Load and validate model
     - Update `models_history.json` (mark as deployed)
     - Copy metrics to `metrics.json` (active model metadata)
     - Load model into memory (global TRAINED_MODEL variable)
     - Record deployment timestamp and deployer username
  5. Success message confirms deployment
  6. Model status refreshed throughout dashboard
- **Postcondition:** Selected model now active for all stroke risk predictions; doctors use deployed model
- **Implementation:** `/data_scientist/deploy_model` POST endpoint

#### 2.5.3 Check Model Status
**Use Case:** View Currently Deployed Model Information
- **Actor:** Data Scientist
- **Flow:**
  1. Dashboard automatically checks model status on page load
  2. Status panel displays:
     - **If model deployed:** Algorithm name, accuracy, active status, "Reload Model" button
     - **If no model deployed:** Warning message, recommendation to train and deploy
  3. Visual indicators (color-coded banners)
- **Postcondition:** Data scientist aware of production model status
- **Implementation:** Client-side `checkModelStatus()` function called on page load

#### 2.5.4 Reload Deployed Model
**Use Case:** Refresh Model in Memory After External Changes
- **Actor:** Data Scientist
- **Flow:**
  1. Click "Reload Model" button in model status panel
  2. System reloads model from disk into memory
  3. Confirmation message displayed
- **Postcondition:** Model refreshed without redeployment or server restart
- **Use Cases:** Hot-reload after file system changes, troubleshooting
- **Implementation:** `/data_scientist/reload_model` POST endpoint

#### 2.5.5 Delete Trained Model
**Use Case:** Remove Unwanted Model from Inventory
- **Actor:** Data Scientist
- **Flow:**
  1. Identify model to delete in models list
  2. Click "??? Delete" button
  3. Confirm deletion (irreversible action)
  4. System executes deletion:
     - Validate model is not currently deployed (prevent accidental deletion)
     - Delete model file from disk
     - Remove entry from `models_history.json`
  5. Success confirmation; models list refreshes
- **Precondition:** Model is not currently deployed
- **Postcondition:** Model removed from system; disk space freed
- **Implementation:** `/data_scientist/delete_model` POST endpoint

#### 2.5.6 Compare Models
**Use Case:** Evaluate Multiple Models Side-by-Side
- **Actor:** Data Scientist
- **Flow:**
  1. View models list with all trained models
  2. Visually compare metrics across models:
     - Accuracy (prominently displayed)
     - Precision, recall, F1-score
     - Cross-validation results
     - Dataset sizes
  3. Select best performing model for deployment
- **Postcondition:** Informed deployment decision based on comprehensive comparison
- **Implementation:** Models list display with sortable metrics

---

### 2.6 Analytics & Monitoring

#### 2.6.1 View Dashboard Statistics
**Use Case:** Monitor System-Wide Metrics
- **Actor:** Data Scientist
- **Flow:**
  1. View dashboard statistics cards:
     - **Total Patients:** Count of all records
     - **High Risk Cases:** Count of patients predicted as high risk
     - **Stroke Rate:** Percentage of high risk patients
  2. Track data growth and risk prevalence over time
- **Postcondition:** Data scientist understands dataset scope and risk distribution
- **Implementation:** Dashboard statistics aggregation in `/data_scientist/dashboard`

#### 2.6.2 Access Analytics API
**Use Case:** Retrieve Structured Analytics Data
- **Actor:** Data Scientist (via API or custom tools)
- **Flow:**
  1. Send GET request to `/api/analytics/dashboard-data`
  2. System calculates and returns:
     - Age distribution by decade
     - Gender distribution
     - Risk factors prevalence
     - Prediction trends by month
     - Feature correlations
  3. Data returned as JSON for further processing
- **Postcondition:** Analytics data available for custom visualizations or reporting
- **Implementation:** `/api/analytics/dashboard-data` GET endpoint

---

### 2.7 Model Versioning & Governance

#### 2.7.1 Track Model History
**Use Case:** Maintain Audit Trail of All Model Versions
- **Actor:** Data Scientist / Compliance Officer
- **Flow:**
  1. All trained models automatically logged to `models_history.json`
  2. Each entry includes:
     - Model filename (unique timestamp identifier)
     - Algorithm type
     - Performance metrics
     - Training configuration
     - Dataset metadata
     - Trainer username
     - Training timestamp
     - Deployment status and timestamp
  3. History maintained (last 20 models retained)
- **Postcondition:** Complete audit trail for compliance and analysis
- **Use Cases:** Model governance, A/B testing, rollback capability, compliance audits
- **Implementation:** Persistent JSON-based model registry

#### 2.7.2 Model Rollback
**Use Case:** Revert to Previous Model Version
- **Actor:** Data Scientist
- **Flow:**
  1. Identify previous model version in models list
  2. Deploy selected historical model
  3. Previous model becomes active
- **Postcondition:** System reverted to known-good model state
- **Use Cases:** Production issues, performance regression, emergency rollback
- **Implementation:** Re-deployment of historical model via deploy endpoint

---

### 2.8 Algorithm Selection & Optimization

#### 2.8.1 Compare Algorithm Performance
**Use Case:** Determine Optimal Algorithm for Dataset
- **Actor:** Data Scientist
- **Flow:**
  1. Train models using different algorithms (Random Forest, SVM, etc.)
  2. Compare performance metrics in models list
  3. Review algorithm-specific insights and recommendations
  4. Consider trade-offs:
     - **Random Forest:** High accuracy, interpretability, robustness
     - **SVM:** High-dimensional performance, requires tuning
     - **Naive Bayes:** Fast, simple, baseline
     - **Gradient Boosting:** Highest potential accuracy, complex
     - **Logistic Regression:** Interpretable, fast, linear assumptions
  5. Select best algorithm based on requirements (accuracy vs interpretability vs speed)
- **Postcondition:** Optimal algorithm identified for production use
- **Implementation:** Algorithm recommendations displayed with training results

#### 2.8.2 Hyperparameter Tuning (Implicit)
**Use Case:** Use Pre-configured Hyperparameters for Algorithms
- **Actor:** Data Scientist
- **Flow:**
  1. System applies production-ready hyperparameters for each algorithm:
     - Balanced class weights (address imbalance)
     - Regularization parameters
     - Ensemble sizes
     - Kernel configurations
  2. Parameters optimized for healthcare/stroke prediction use case
- **Postcondition:** Models trained with reasonable defaults
- **Future Enhancement:** Expose hyperparameter tuning interface
- **Implementation:** `get_model_by_algorithm()` function with hardcoded configurations

---

### 2.9 Data Preprocessing Insights

#### 2.9.1 Understand Preprocessing Pipeline
**Use Case:** Document Data Transformations for Reproducibility
- **Actor:** Data Scientist
- **Flow:**
  1. Review preprocessing steps applied during training:
     - Missing value imputation (median for numeric)
     - Categorical encoding (LabelEncoder)
     - Feature scaling (StandardScaler)
     - Class balancing (class_weight='balanced')
  2. Ensure preprocessing consistency between training and inference
- **Postcondition:** Preprocessing pipeline documented and reproducible
- **Use Cases:** Model debugging, deployment validation, documentation
- **Implementation:** `preprocess_data_for_training()` function

#### 2.9.2 Feature Engineering Insights
**Use Case:** Analyze Feature Importance for Model Interpretation
- **Actor:** Data Scientist
- **Flow:**
  1. After training tree-based models, view top 10 features by importance
  2. Understand which clinical factors drive predictions:
     - Age, hypertension, glucose level typically most important
  3. Use insights for:
     - Clinical communication
     - Feature engineering
     - Data collection prioritization
- **Postcondition:** Model behavior interpretable and actionable
- **Implementation:** Feature importance extraction and display in training results