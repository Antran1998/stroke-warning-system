# Stroke Warning System

A Flask-based web application for managing patient records and predicting stroke risk. It provides two roles: doctor and data scientist. Doctors can add/update patients and see risk summaries. Data scientists can view analytics and export data.

## Prerequisites
- Python 3.10+ installed
- Git
- Optional: virtual environment tool (`venv`)

## Quick Start
1. Clone the repository
   - `git clone https://github.com/Antran1998/stroke-warning-system`
   - `cd stroke-warning-system`

2. Create and activate a virtual environment
   - Windows: `python -m venv .venv && .venv\Scripts\activate`
   - macOS/Linux: `python -m venv .venv && source .venv/bin/activate`

3. Install dependencies
   - `pip install -r requirements.txt`

4. Optional: set environment variables
   - `FLASK_CONFIG` (default `development`)
   - `DEV_DATABASE_URL` or `DATABASE_URL` for a custom database URI (default is SQLite `hospital.db`)
   - `SECRET_KEY` for session security

5. Initialize the database and start the app
   - `python app.py`
   - The app creates tables and two default users on first run:
     - Doctor: username `doctor1`, password `doctor123`
     - Data Scientist: username `datascientist1`, password `ds123`
   - Open `http://localhost:5000` in your browser.

## Project Structure
- `app.py`: Flask app factory, routes, and rule-based predictor
- `models.py`: SQLAlchemy models (`User`, `Patient`)
- `config.py`: Environment-based configuration
- `templates/`: HTML templates for dashboards and login
- `static/`: Static assets (CSS)
- `migrate_data.py`: Import patients from `brain_stroke.csv` into the database
- `train_model.py`: ML training script using data from the database
- `requirements.txt`: Python dependencies

## Running in Different Environments
- Development (default): uses `sqlite:///hospital.db`
  - `set FLASK_CONFIG=development` (Windows) or `export FLASK_CONFIG=development` (macOS/Linux)
- Production: set `FLASK_CONFIG=production` and `DATABASE_URL`
- Testing: set `FLASK_CONFIG=testing`

## Database
- Default: SQLite file `hospital.db` in the repo directory
- Change DB via `DEV_DATABASE_URL` (development) or `DATABASE_URL` (production), e.g. `postgresql+psycopg2://user:pass@host/dbname`

## Data Migration (optional)
- Place `brain_stroke.csv` in the repository root.
- Run `python migrate_data.py`
- The script aborts if >10 patients already exist to avoid duplicates.

Expected CSV columns:
- `id`, `age`, `gender`, `hypertension`, `heart_disease`, `ever_married`, `work_type`, `Residence_type`, `avg_glucose_level`, `bmi`, `smoking_status`, `stroke`

## Usage
- Login with default credentials
- Doctor dashboard:
  - View patients, pagination
  - Add new patient (rule-based stroke prediction)
  - Inline edit existing patient; prediction updates automatically
- Data Scientist dashboard:
  - View totals, high-risk counts, model metrics (if available)
  - Export data via `/api/export-data` (JSON or CSV)

## Model Training (optional)
- `train_model.py` loads patients from the DB and trains several classifiers.
- Example usage:
  - Create data: add patients or migrate CSV
  - Extend `train_model.py` to persist trained model/metrics (e.g., save to `model/metrics.json`)

## API Endpoints (selected)
- `/doctor/dashboard` (GET)
- `/doctor/add_patient` (POST JSON)
- `/doctor/update_patient` (POST JSON)
- `/data_scientist/dashboard` (GET)
- `/api/analytics/dashboard-data` (GET)
- `/api/export-data` (POST JSON)

## Common Issues
- If you see "Error: 'brain_stroke.csv' not found" when migrating, ensure the file is in the repo root.
- If the app cannot find the DB, check `FLASK_CONFIG` and the `*_DATABASE_URL` environment variables.
- Port conflicts: change port in `app.py` (`app.run(..., port=5000)`).

## Security Notes
- Default credentials are for local testing only. Change `SECRET_KEY` and user passwords for production.
- Consider HTTPS and a production-grade server (e.g., gunicorn) for deployment.

## License
- This project is for educational purposes. Add a license if you intend to distribute.
