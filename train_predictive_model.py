import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor

# Step 1: Load data
conn = sqlite3.connect("healthcare.db")
query = """
SELECT 
    CAST((julianday('now') - julianday(p.date_of_birth)) / 365.25 AS INT) AS age,
    v.blood_pressure,
    v.heart_rate,
    v.glucose_level,
    v.bmi,
    v.hemoglobin,
    v.cholesterol,
    rs.heart_disease_risk,
    rs.diabetes_risk
FROM Vitals v
JOIN Patients p ON v.patient_id = p.patient_id
JOIN RiskScores rs ON rs.patient_id = p.patient_id
"""
df = pd.read_sql(query, conn)
conn.close()

# Preprocessing
df = df[df['blood_pressure'].str.contains('/')]
df[['systolic', 'diastolic']] = df['blood_pressure'].str.split('/', expand=True).astype(float)
df.drop(columns=['blood_pressure'], inplace=True)
df.dropna(inplace=True)

print(f"✅ Loaded {df.shape[0]} records for training.")

X = df[['age', 'systolic', 'diastolic', 'heart_rate', 'glucose_level', 'bmi', 'hemoglobin', 'cholesterol']]
y_heart = df['heart_disease_risk']
y_diabetes = df['diabetes_risk']

X_train, X_test, y_train_heart, y_test_heart, y_train_diabetes, y_test_diabetes = train_test_split(
    X, y_heart, y_diabetes, test_size=0.2, random_state=42
)

# Model dictionary
models = {
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
    "LinearRegression": LinearRegression()
}

# Collect results here
results = []

def evaluate_model(model, X_train, X_test, y_train, y_test, task_name):
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    return {
        "Task": task_name,
        "Model": type(model).__name__,
        "R² Score": round(r2, 4),
        "RMSE": round(rmse, 4)
    }

# Step 5: Train & collect results
for task_name, (y_train, y_test) in {"Heart Disease": (y_train_heart, y_test_heart), "Diabetes": (y_train_diabetes, y_test_diabetes)}.items():
    for name, model in models.items():
        metrics = evaluate_model(model, X_train, X_test, y_train, y_test, task_name)
        results.append(metrics)

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Save best models separately
def train_best_model(X_train, X_test, y_train, y_test, label):
    best_r2 = -np.inf
    best_model = None
    best_model_name = None
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        r2 = r2_score(y_test, preds)
        if r2 > best_r2:
            best_r2 = r2
            best_model = model
            best_model_name = name
    return best_model_name, best_model

heart_model_name, heart_model = train_best_model(X_train, X_test, y_train_heart, y_test_heart, "Heart Disease")
diabetes_model_name, diabetes_model = train_best_model(X_train, X_test, y_train_diabetes, y_test_diabetes, "Diabetes")

joblib.dump(heart_model, "heart_risk_model.pkl")
joblib.dump(diabetes_model, "diabetes_risk_model.pkl")

print("\n📊 Detailed Model Evaluation Results:")
print(results_df.sort_values(by=["Task", "R² Score"], ascending=[True, False]))

print(f"\n✅ Best Heart Model: {heart_model_name} → Saved as 'heart_risk_model.pkl'")
print(f"✅ Best Diabetes Model: {diabetes_model_name} → Saved as 'diabetes_risk_model.pkl'")
print("✅ Models trained and saved successfully.")