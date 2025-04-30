import sqlite3
import pandas as pd

conn = sqlite3.connect("healthcare.db")

# View all table names
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("Tables:\n", tables)

# Example: View top 5 patients
patients = pd.read_sql("SELECT * FROM Patients LIMIT 5", conn)
print("\nPatients:\n", patients)

# Example: View top 5 risk scores
risks = pd.read_sql("SELECT * FROM RiskScores ORDER BY score_date DESC LIMIT 5", conn)
print("\nRiskScores:\n", risks)

conn.close()
