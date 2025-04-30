# database_setup.py

import sqlite3

def create_tables():
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()

    # --- Patients Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            date_of_birth TEXT,
            check_in_status TEXT
        )
    ''')

    # --- Appointments Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            appointment_date TEXT,
            doctor_name TEXT,
            status TEXT,
            FOREIGN KEY(patient_id) REFERENCES Patients(patient_id)
        )
    ''')

    # --- Lab Reports Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS LabReports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            report_type TEXT,
            report_date TEXT,
            result TEXT,
            FOREIGN KEY(patient_id) REFERENCES Patients(patient_id)
        )
    ''')

    # --- Vitals Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Vitals (
            vital_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            record_date TEXT,
            blood_pressure TEXT,
            heart_rate INTEGER,
            glucose_level INTEGER,
            bmi REAL,
            hemoglobin REAL,
            cholesterol INTEGER,
            FOREIGN KEY(patient_id) REFERENCES Patients(patient_id)
        )
    ''')

    # --- Users Table (for login and RBAC) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # --- Risk Scores Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RiskScores (
            risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            score_date TEXT,
            heart_disease_risk REAL,
            diabetes_risk REAL,
            FOREIGN KEY(patient_id) REFERENCES Patients(patient_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ All tables created successfully.")

if __name__ == "__main__":
    create_tables()
