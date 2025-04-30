# backend.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sqlite3

# ========== Initialize App ==========
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Database Helpers ==========
def query_db(query, args=()):
    conn = sqlite3.connect('healthcare.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    results = cur.fetchall()
    conn.close()
    return [dict(row) for row in results]

def execute_db(query, args=()):
    conn = sqlite3.connect('healthcare.db')
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()

# ========== Root Test ==========
@app.get("/")
def root():
    return {"message": "✅ FastAPI Healthcare API is running!"}

# ========== Patient and Visit APIs ==========

@app.get("/active_patients")
def get_active_patients():
    return query_db("SELECT * FROM Patients WHERE check_in_status = 'Checked-in'")

@app.get("/appointments_today")
def get_appointments_today():
    return query_db("""
        SELECT a.*, p.first_name, p.last_name
        FROM Appointments a
        JOIN Patients p ON a.patient_id = p.patient_id
        WHERE DATE(appointment_date) = DATE('now')
    """)

@app.get("/age_demographics")
def get_age_demographics():
    return query_db("""
        SELECT 
            CASE 
                WHEN age BETWEEN 0 AND 18 THEN '0-18'
                WHEN age BETWEEN 19 AND 35 THEN '19-35'
                WHEN age BETWEEN 36 AND 55 THEN '36-55'
                ELSE '55+'
            END AS age_group,
            COUNT(*) as count
        FROM (
            SELECT 
                CAST((julianday('now') - julianday(date_of_birth)) / 365.25 AS INT) AS age
            FROM Patients
        )
        GROUP BY age_group
    """)

@app.get("/patient_list")
def get_patient_list():
    return query_db("SELECT patient_id, first_name, last_name FROM Patients")

@app.get("/patient_details/{patient_id}")
def get_patient_details(patient_id: int):
    return query_db("""
        SELECT 
            p.patient_id, p.first_name, p.last_name, p.gender, p.date_of_birth,
            MAX(v.record_date) AS last_visit
        FROM Patients p
        LEFT JOIN Vitals v ON p.patient_id = v.patient_id
        WHERE p.patient_id = ?
        GROUP BY p.patient_id
    """, (patient_id,))

# ========== Risk and Health Trends APIs ==========

@app.get("/risk_scores")
def get_risk_scores():
    return query_db("""
        SELECT rs.*, p.first_name, p.last_name, p.gender, p.date_of_birth
        FROM RiskScores rs
        JOIN Patients p ON rs.patient_id = p.patient_id
    """)

@app.get("/monthly_risk_trends")
def get_monthly_risk_trends():
    return query_db("""
        SELECT 
            strftime('%Y-%m', score_date) as month,
            AVG(heart_disease_risk) as avg_heart_risk,
            AVG(diabetes_risk) as avg_diabetes_risk
        FROM RiskScores
        GROUP BY month
        ORDER BY month
    """)

@app.get("/patient_risk_trend/{patient_id}")
def get_patient_risk_trend(patient_id: int):
    return query_db("""
        SELECT 
            strftime('%Y-%m', score_date) as month,
            AVG(heart_disease_risk) as avg_heart_risk,
            AVG(diabetes_risk) as avg_diabetes_risk
        FROM RiskScores
        WHERE patient_id = ?
        GROUP BY month
        ORDER BY month
    """, (patient_id,))

# ========== Lab Reports APIs ==========

@app.get("/recent_lab_reports")
def get_recent_lab_reports():
    return query_db("""
        SELECT lr.*, p.first_name, p.last_name
        FROM LabReports lr
        JOIN Patients p ON lr.patient_id = p.patient_id
        WHERE DATE(report_date) >= DATE('now', '-7 days')
        ORDER BY report_date DESC
        LIMIT 50
    """)

@app.get("/lab_reports_by_patient/{patient_id}")
def get_lab_reports_by_patient(patient_id: int):
    return query_db("""
        SELECT * FROM LabReports
        WHERE patient_id = ?
        ORDER BY report_date DESC
    """, (patient_id,))

# ========== Save (POST) APIs ==========

@app.post("/save_lab_report")
async def save_lab_report(request: Request):
    try:
        data = await request.json()
        required_keys = ['patient_id', 'report_type', 'report_date', 'result']
        if not all(key in data for key in required_keys):
            return {"status": "error", "message": "Missing required fields"}

        # Validate patient exists
        patient_check = query_db("SELECT 1 FROM Patients WHERE patient_id = ?", (data['patient_id'],))
        if not patient_check:
            return {"status": "error", "message": "Patient ID does not exist"}

        # Insert
        execute_db("""
            INSERT INTO LabReports (patient_id, report_type, report_date, result)
            VALUES (?, ?, ?, ?)
        """, (data['patient_id'], data['report_type'], data['report_date'], data['result']))

        return {"status": "success", "message": "Lab report saved successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/save_risk")
async def save_risk(request: Request):
    try:
        data = await request.json()
        required_keys = ['patient_id', 'heart_disease_risk', 'diabetes_risk']
        if not all(key in data for key in required_keys):
            return {"status": "error", "message": "Missing required fields"}

        # Validate patient exists
        patient_check = query_db("SELECT 1 FROM Patients WHERE patient_id = ?", (data['patient_id'],))
        if not patient_check:
            return {"status": "error", "message": "Patient ID does not exist"}

        # Insert
        execute_db("""
            INSERT INTO RiskScores (patient_id, score_date, heart_disease_risk, diabetes_risk)
            VALUES (?, ?, ?, ?)
        """, (data['patient_id'], datetime.now().isoformat(), data['heart_disease_risk'], data['diabetes_risk']))

        return {"status": "success", "message": "Risk score saved successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ========== Database Check API ==========

@app.get("/test_db")
def test_db():
    return query_db("SELECT name FROM sqlite_master WHERE type='table'")

# ========== Run if executed directly ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
