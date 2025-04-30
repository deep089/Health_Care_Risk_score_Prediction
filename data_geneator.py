import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

def calculate_heart_risk(age, sys, dia, hr, bmi, chol):
    score = (
        0.02 * age +
        0.015 * sys +
        0.01 * dia +
        0.02 * hr +
        0.03 * bmi +
        0.025 * chol / 10
    )
    return round(min(score / 10, 1), 2)

def calculate_diabetes_risk(age, glucose, bmi, hemo):
    score = (
        0.03 * age +
        0.05 * glucose +
        0.04 * bmi +
        -0.02 * hemo
    )
    return round(min(score / 15, 1), 2)

def generate_data(n_patients=10000, visits_per_patient=5):
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()

    for _ in range(n_patients):
        # Patient info
        first = fake.first_name()
        last = fake.last_name()
        gender = random.choice(['Male', 'Female'])
        dob_obj = fake.date_of_birth(minimum_age=20, maximum_age=85)
        dob = dob_obj.isoformat()
        age = int((datetime.now().date() - dob_obj).days / 365.25)
        check_in_status = random.choice(['Checked-in', 'Not Checked-in'])

        cursor.execute('''
            INSERT INTO Patients (first_name, last_name, gender, date_of_birth, check_in_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (first, last, gender, dob, check_in_status))
        patient_id = cursor.lastrowid

        for i in range(visits_per_patient):
            days_ago = random.randint(0, 180)
            visit_date = (datetime.now() - timedelta(days=days_ago)).isoformat()

            # Appointment
            doctor = fake.name()
            status = random.choice(['Scheduled', 'Completed', 'Missed'])
            cursor.execute('''
                INSERT INTO Appointments (patient_id, appointment_date, doctor_name, status)
                VALUES (?, ?, ?, ?)
            ''', (patient_id, visit_date, doctor, status))

            # Lab Report
            report_type = random.choice(['Blood Test', 'X-ray', 'ECG'])
            result = random.choice(['Normal', 'Abnormal'])
            cursor.execute('''
                INSERT INTO LabReports (patient_id, report_type, report_date, result)
                VALUES (?, ?, ?, ?)
            ''', (patient_id, report_type, visit_date, result))

            # Vitals
            systolic = random.randint(100, 160)
            diastolic = random.randint(60, 100)
            bp = f"{systolic}/{diastolic}"
            hr = random.randint(60, 100)
            glucose = random.randint(70, 200)
            bmi = round(random.uniform(18.0, 35.0), 1)
            hemo = round(random.uniform(10.0, 17.0), 1)
            chol = random.randint(150, 280)

            cursor.execute('''
                INSERT INTO Vitals (patient_id, record_date, blood_pressure, heart_rate,
                                    glucose_level, bmi, hemoglobin, cholesterol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, visit_date, bp, hr, glucose, bmi, hemo, chol))

            # Risk scores - now calculated using logic
            heart_risk = calculate_heart_risk(age, systolic, diastolic, hr, bmi, chol)
            diabetes_risk = calculate_diabetes_risk(age, glucose, bmi, hemo)

            cursor.execute('''
                INSERT INTO RiskScores (patient_id, score_date, heart_disease_risk, diabetes_risk)
                VALUES (?, ?, ?, ?)
            ''', (patient_id, visit_date, heart_risk, diabetes_risk))

        if _ % 100 == 0:
            print(f"Inserted {_} patients...")

    conn.commit()
    conn.close()
    print("✅ Data generation complete with realistic risk scores.")

if __name__ == '__main__':
    generate_data()
